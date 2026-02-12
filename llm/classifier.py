"""
Message classifier — lightweight heuristic to tag message intent.

Used by retrieval_policy to decide whether long-term memory lookup is worthwhile.
"""

# Intent categories returned by classify()
INTENT_QUESTION = "question"
INTENT_STATEMENT = "statement"
INTENT_GREETING = "greeting"
INTENT_COMMAND = "command"

_GREETINGS = {"hi", "hello", "hey", "howdy", "good morning", "good evening", "good afternoon"}
_COMMANDS = {"remember", "forget", "update", "change", "set", "don't", "stop", "always"}


def classify(message: str) -> str:
    """Return a lightweight intent tag for *message*."""
    lower = message.strip().lower().rstrip("!.,")

    if lower in _GREETINGS:
        return INTENT_GREETING

    if any(lower.startswith(cmd) for cmd in _COMMANDS):
        return INTENT_COMMAND

    if "?" in message:
        return INTENT_QUESTION

    return INTENT_STATEMENT
