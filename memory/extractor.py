"""
Memory extractor — uses a second LLM call to pull structured facts from the message.

Improvements in this version:
- The extraction prompt requests optional confidence and importance fields (0.0 - 1.0).
- The extractor validates entries and applies simple local filters (min confidence / importance).
- Skips obviously malformed or low-quality extractions instead of always persisting them.
- Normalizes keys to canonical forms for consistent retrieval.
"""

import json
import logging
from typing import List

from llm.generator import call_llm
from memory.structured_facts import upsert_fact
from config import CANONICAL_KEY_MAPPING

logger = logging.getLogger(__name__)


_EXTRACTION_PROMPT = """Extract structured facts from the user's message. Return ONLY a JSON array.

Use these canonical keys:
- name, location, timezone, job, language, formatter, project
- testing_framework, api_framework, type_hints, docstrings, line_length
- database, latency_target

Categories:
- identity: name, location, job
- preference: language, formatter, testing_framework, api_framework
- constraint: line_length, latency_target
- instruction: type_hints, docstrings

Format: [{{"category":"identity","key":"name","value":"Alex","confidence":0.9,"importance":0.8}}]

If no facts exist, return: []

User message: {message}

JSON array:"""


# Local thresholds (tuneable)
MIN_CONFIDENCE = 0.4
MIN_IMPORTANCE = 0.2


def _clean_response(response: str) -> str:
    """Strip common wrappers the LLM may add (markdown fences, leading 'json', etc.)."""
    if response is None:
        return ""
    cleaned = response.strip()
    
    # Remove markdown code fences (```json ... ``` or ```...```)
    if cleaned.startswith("```"):
        # Find the first newline after ```
        first_newline = cleaned.find('\n')
        if first_newline > 0:
            cleaned = cleaned[first_newline+1:]
        # Remove trailing ```
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()
    
    # Remove leading "json" label if present
    if cleaned.lower().startswith("json"):
        cleaned = cleaned[4:].strip()
    
    # Find the actual JSON array/object start
    # Look for first [ or { character
    for i, char in enumerate(cleaned):
        if char in '[{':
            cleaned = cleaned[i:]
            break
    
    # Find the last ] or } and cut there
    for i in range(len(cleaned)-1, -1, -1):
        if cleaned[i] in ']}':
            cleaned = cleaned[:i+1]
            break
    
    return cleaned


def _normalize_key(raw_key: str) -> str:
    """Normalize a key to its canonical form using the mapping."""
    raw_key_lower = raw_key.strip().lower()
    
    # Check if it's already canonical
    if raw_key_lower in CANONICAL_KEY_MAPPING:
        return raw_key_lower
    
    # Find canonical key by checking if raw_key is in any alias list
    for canonical, aliases in CANONICAL_KEY_MAPPING.items():
        if raw_key_lower in [a.lower() for a in aliases]:
            logger.debug("Normalized key: %s → %s", raw_key, canonical)
            return canonical
    
    # If no match found, use as-is but log it
    logger.debug("Non-canonical key used: %s", raw_key)
    return raw_key_lower


def _validate_and_normalize(mem: dict) -> dict | None:
    """Validate a single extraction entry and apply defaults.

    Returns normalized dict or None if invalid / should be ignored.
    """
    if not isinstance(mem, dict):
        return None

    category = mem.get("category")
    key = mem.get("key")
    value = mem.get("value")

    if not category or not key or value is None:
        return None

    # normalize simple fields
    category = str(category).strip().lower()
    key = str(key).strip()
    value = str(value).strip()

    if key == "" or value == "":
        return None
    
    # Normalize key to canonical form
    key = _normalize_key(key)
    
    # Only allow valid categories
    if category not in ("identity", "preference", "constraint", "instruction"):
        logger.debug("Skipping invalid category: %s", category)
        return None

    try:
        confidence = float(mem.get("confidence", 1.0))
    except (TypeError, ValueError):
        confidence = 1.0

    try:
        importance = float(mem.get("importance", 0.5))
    except (TypeError, ValueError):
        importance = 0.5

    # basic quality filters
    if confidence < MIN_CONFIDENCE:
        logger.debug("Skipping low-confidence memory: %s (confidence=%.2f)", key, confidence)
        return None

    if importance < MIN_IMPORTANCE:
        logger.debug("Skipping low-importance memory: %s (importance=%.2f)", key, importance)
        return None

    return {
        "category": category,
        "key": key,
        "value": value,
        "confidence": confidence,
        "importance": importance,
    }


def extract_and_store(user_id: str, message: str) -> None:
    """Extract memories from *message*, filter low-quality items, and persist the rest.

    This function is safe to call asynchronously from a background worker. It never raises.
    """
    # Skip extraction for questions - users asking for info, not providing it
    if message.strip().endswith('?'):
        logger.debug("Skipping extraction for question: %s", message[:50])
        return
    
    # Skip very short messages
    if len(message.split()) < 3:
        logger.debug("Skipping extraction for short message: %s", message)
        return
    
    prompt = _EXTRACTION_PROMPT.format(message=message)

    try:
        # Use more tokens for extraction (needs full JSON output)
        import requests
        from config import OLLAMA_URL, LLM_MODEL, LLM_TIMEOUT_SEC
        
        resp = requests.post(
            OLLAMA_URL,
            json={
                "model": LLM_MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.1,
                    "num_predict": 300,  # Allow full JSON extraction
                },
            },
            timeout=LLM_TIMEOUT_SEC,
        )
        resp.raise_for_status()
        response = resp.json().get("response", "")
    except Exception as e:
        logger.warning("Memory extractor LLM call failed: %s", e)
        return

    cleaned = _clean_response(response)

    try:
        candidates: List[dict] = json.loads(cleaned) if cleaned else []
    except (json.JSONDecodeError, TypeError) as e:
        logger.warning("Memory extraction returned invalid JSON: %s — raw: %.200s", e, response)
        return

    if not isinstance(candidates, list):
        logger.warning("Expected a JSON list from extractor, got %s", type(candidates).__name__)
        return

    seen = set()
    for raw in candidates:
        norm = _validate_and_normalize(raw)
        if norm is None:
            logger.debug("Discarding extraction candidate: %s", raw)
            continue

        dedupe_key = (norm["category"], norm["key"], norm["value"])
        if dedupe_key in seen:
            logger.debug("Skipping duplicate extraction: %s", dedupe_key)
            continue
        seen.add(dedupe_key)

        # Persist the normalized fact to structured storage
        try:
            upsert_fact(
                user_id, 
                norm["category"], 
                norm["key"], 
                norm["value"], 
                confidence=norm["confidence"],
                importance=norm["importance"]
            )
        except Exception as e:
            logger.error("Failed to persist fact %s for user %s: %s", norm, user_id, e)
