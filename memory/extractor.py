"""
Memory extractor — uses a second LLM call to pull structured facts from the message.
"""

import json
import logging
from llm.generator import call_llm
from memory.temporal_store import upsert_memory

logger = logging.getLogger(__name__)

_EXTRACTION_PROMPT = """You are a memory extraction system.

Extract ONLY long-term user information (preferences, constraints, commitments, standing instructions).
If the message contains NO extractable information, return an empty JSON array: []

Return ONLY valid JSON. No explanation. No markdown. No extra text.

Format:
[
  {{"type": "preference", "key": "language", "value": "Hindi"}}
]

Message:
{message}"""


def extract_and_store(user_id: str, message: str) -> None:
    """Extract memories from *message* and persist them."""
    prompt = _EXTRACTION_PROMPT.format(message=message)
    response = call_llm(prompt)

    # Strip possible markdown fences the LLM might add
    cleaned = response.strip().strip("`").strip()
    if cleaned.startswith("json"):
        cleaned = cleaned[4:].strip()

    try:
        memories = json.loads(cleaned)
    except (json.JSONDecodeError, TypeError) as e:
        logger.warning("Memory extraction returned invalid JSON: %s — raw: %.200s", e, response)
        return

    if not isinstance(memories, list):
        logger.warning("Expected a JSON list from extractor, got %s", type(memories).__name__)
        return

    for mem in memories:
        if not all(k in mem for k in ("type", "key", "value")):
            logger.warning("Skipping malformed memory entry: %s", mem)
            continue
        upsert_memory(user_id, mem["type"], mem["key"], mem["value"])
