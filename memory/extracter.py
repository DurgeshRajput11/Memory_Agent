import json
from llm.generator import call_llm
from memory.temporal_store import upsert_memory

def extract_and_store(user_id, message):
    prompt = f"""
You are a memory extraction system.

Extract ONLY long-term user information.

Return ONLY valid JSON.
No explanation.
No markdown.
No extra text.

Format:
[
  {{"type": "preference", "key": "language", "value": "Hindi"}}
]

Message:
{message}
"""

    response = call_llm(prompt)

    try:
        memories = json.loads(response)
    except:
        return

    for mem in memories:
        upsert_memory(
            user_id,
            mem["type"],
            mem["key"],
            mem["value"]
        )
