"""
Retrieval Policy — decides whether to query active long-term memory.

Rules:
  • "active"  → run vector retrieval (default for most messages)
  • "session" → rely only on short-term session memory
"""

# Keywords that almost never need long-term memory lookup
_SKIP_KEYWORDS = {"hi", "hello", "hey", "thanks", "thank you", "ok", "okay", "bye", "yes", "no"}


def decide_mode(message: str) -> str:
    """Return 'active' or 'session' based on a lightweight heuristic."""
    cleaned = message.strip().lower()

    # Very short greetings / acknowledgements → skip DB round-trip
    if cleaned in _SKIP_KEYWORDS:
        return "session"

    # Anything with a question mark likely needs memory
    if "?" in message:
        return "active"

    # Default: always retrieve (safe for long conversations)
    return "active"
