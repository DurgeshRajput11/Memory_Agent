"""
FastAPI entry point for the long-term memory chat agent.

Start:  uvicorn app:app --reload
"""

import logging
import time
from contextlib import asynccontextmanager
from concurrent.futures import ThreadPoolExecutor

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from session import SessionMemory
from memory.retrieval_harness import retrieve_all, format_for_injection
from memory.extractor import extract_and_store
from memory.summarizer import should_summarize, compress_session_to_episodic
from llm.generator import call_llm
from retrieval_policy import decide_mode

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ── Background thread pool for async memory extraction ────────
_executor = ThreadPoolExecutor(max_workers=2)


# ── Lifespan (startup / shutdown) ────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Memory Agent started ✅")
    yield
    _executor.shutdown(wait=False)
    logger.info("Memory Agent stopped 🛑")


app = FastAPI(title="Memory Agent", lifespan=lifespan)

# In-memory session store (per user)
sessions: dict[str, SessionMemory] = {}
turn_counters: dict[str, int] = {}  # Track global turn number per user


# ── Request / Response schemas ────────────────────────────────
class ChatRequest(BaseModel):
    user_id: str
    message: str


class ChatResponse(BaseModel):
    response: str
    latency_ms: float


# ── Main chat endpoint ────────────────────────────────────────
@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    user_id = req.user_id
    message = req.message

    # Initialize session and turn counter
    if user_id not in sessions:
        sessions[user_id] = SessionMemory()
        turn_counters[user_id] = 0
    
    session = sessions[user_id]
    turn_counters[user_id] += 1
    current_turn = turn_counters[user_id]
    
    session.add("user", message)

    # Check if we should compress old session turns into episodic memory
    if should_summarize(len(session.history)):
        # Take oldest turns and compress
        to_compress = session.history[:-10]  # Keep last 10 in session
        if to_compress:
            _executor.submit(
                compress_session_to_episodic,
                user_id,
                to_compress,
                current_turn - len(session.history)
            )
            # Clear compressed turns from session
            session.history = session.history[-10:]

    # 2. Retrieval policy decision
    mode = decide_mode(message)

    # 3. Multi-stage retrieval (semantic + episodic)
    memory_injection = ""
    if mode == "active":
        try:
            retrieval_results = retrieve_all(user_id, message, top_k_facts=3, top_k_episodes=2)
            memory_injection = format_for_injection(retrieval_results, max_tokens=200)
            logger.info("Retrieved: %d facts + %d episodes",
                       len(retrieval_results["structured_facts"]),
                       len(retrieval_results["episodic_context"]))
        except Exception as e:
            logger.warning("Memory retrieval failed, continuing without: %s", e)
            memory_injection = "No relevant memory found."

    # 4. Build prompt
    short_context = "\n".join(
        f"{m['role']}: {m['content']}" for m in session.get()
    )

    # Build context from retrieved facts
    if memory_injection and memory_injection != "No relevant memory found.":
        context_section = f"User facts:\n{memory_injection}\n\n"
    else:
        context_section = ""

    prompt = (
        f"{context_section}"
        f"Conversation:\n{short_context}\n\n"
        "Reply naturally in 1-2 sentences. Use facts when relevant."
    )

    # 5. LLM call (the only latency-critical part)
    start = time.perf_counter()
    response = call_llm(prompt)
    latency_ms = (time.perf_counter() - start) * 1000
    logger.info("LLM latency: %.1f ms", latency_ms)

    # 6. Store assistant reply in session
    session.add("assistant", response)

    # 7. Extract memories in background (avoids doubling latency)
    _executor.submit(extract_and_store, user_id, message)

    return ChatResponse(response=response, latency_ms=round(latency_ms, 1))


# ── Health check ──────────────────────────────────────────────
@app.get("/health")
def health():
    return {"status": "ok"}
