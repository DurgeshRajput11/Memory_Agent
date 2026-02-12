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
from memory.retriever import retrieve_active
from memory.extractor import extract_and_store
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

    # 1. Session (short-term) memory
    if user_id not in sessions:
        sessions[user_id] = SessionMemory()
    session = sessions[user_id]
    session.add("user", message)

    # 2. Retrieval policy decision
    mode = decide_mode(message)

    # 3. Retrieve active long-term memories (if needed)
    active_mem: list[tuple] = []
    if mode == "active":
        try:
            active_mem = retrieve_active(user_id, message)
        except Exception as e:
            logger.warning("Memory retrieval failed, continuing without: %s", e)

    # 4. Build prompt
    memory_context = "\n".join(
        f"[{m[0]}] {m[1]} = {m[2]}" for m in active_mem
    ) if active_mem else "No relevant memories."

    short_context = "\n".join(
        f"{m['role']}: {m['content']}" for m in session.get()
    )

    prompt = (
        f"[ACTIVE MEMORY]\n{memory_context}\n\n"
        f"[RECENT CONVERSATION]\n{short_context}\n\n"
        "Answer consistently using the memory and conversation above."
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
