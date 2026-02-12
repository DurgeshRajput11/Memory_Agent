class SessionMemory:
    def __init__(self):
        self.history = []
        self.max_history = 6

    def add(self, role, content):
        self.history.append({"role": role, "content": content})
        self.history = self.history[-self.max_history:]

    def get(self):
        return self.history
