import os

# ── Database ──────────────────────────────────────────────────
DB_CONFIG = {
    "dbname": os.getenv("PG_DB", "postgres"),
    "user": os.getenv("PG_USER", "postgres"),
    "password": os.getenv("PG_PASSWORD", "pass"),
    "host": os.getenv("PG_HOST", "localhost"),
    "port": os.getenv("PG_PORT", "5432"),
}

# ── Embeddings ────────────────────────────────────────────────
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
EMBEDDING_DIM = 384  # dimension of all-MiniLM-L6-v2

# ── Session / Short-Term Memory ──────────────────────────────
MAX_SHORT_TERM = 6

# ── Retrieval ─────────────────────────────────────────────────
TOP_K = 3
SIMILARITY_THRESHOLD = 0.35  # cosine distance; lower = more similar

# ── Ollama / LLM ─────────────────────────────────────────────
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
LLM_MODEL = os.getenv("LLM_MODEL", "phi3:mini")
LLM_TEMPERATURE = 0.2
LLM_MAX_TOKENS = 120  # keep output short for latency
LLM_TIMEOUT_SEC = 30  # request timeout
