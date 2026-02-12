from config import MAX_SHORT_TERM


class SessionMemory:
    """Sliding-window short-term memory for a single user session."""

    def __init__(self, max_history: int = MAX_SHORT_TERM):
        self.history: list[dict] = []
        self.max_history = max_history

    def add(self, role: str, content: str):
        self.history.append({"role": role, "content": content})
        if len(self.history) > self.max_history:
            self.history = self.history[-self.max_history:]

    def get(self) -> list[dict]:
        return self.history

    def clear(self):
        self.history.clear()
