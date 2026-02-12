
from fastapi import FastAPI
from session import SessionMemory
from memory.retriever import retrieve_active
from memory.extractor import extract_and_store
from llm.generator import call_llm
from retrieval_policy import decide_mode
import time

app = FastAPI()

sessions = {}

@app.post("/chat")
def chat(user_id: str, message: str):

    if user_id not in sessions:
        sessions[user_id] = SessionMemory()

    session = sessions[user_id]
    session.add("user", message)

    mode = decide_mode(message)

    active_mem = []
    if mode == "active":
        active_mem = retrieve_active(user_id, message)

    memory_context = "\n".join(
        [f"{m[0]}: {m[1]} = {m[2]}" for m in active_mem]
    )

    short_context = "\n".join(
        [f"{m['role']}: {m['content']}" for m in session.get()]
    )

    prompt = f"""
[ACTIVE MEMORY]
{memory_context}

[RECENT CONVERSATION]
{short_context}

Answer consistently.
"""

    start = time.time()

    response = call_llm(prompt)

    end = time.time()

    latency_ms = (end - start) * 1000
    print(f"LLM Latency: {latency_ms:.2f} ms")

    session.add("assistant", response)

    extract_and_store(user_id, message)

    return {"response": response}
