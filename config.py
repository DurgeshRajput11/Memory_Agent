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
LLM_MODEL = os.getenv("LLM_MODEL", "llama3.2:3b")
LLM_TEMPERATURE = 0.3
LLM_MAX_TOKENS = 100  # keep output short for latency
LLM_TIMEOUT_SEC = 30  # request timeout

# ── Canonical Key Schema ─────────────────────────────────────
# Maps LLM-generated keys to canonical keys for consistent retrieval
CANONICAL_KEY_MAPPING = {
    "name": ["name", "full_name", "username", "first_name", "my_name"],
    "language": ["language", "programming_language", "preferred_language", "lang", "code_language"],
    "formatter": ["formatter", "code_formatter", "formatting_tool", "format_tool"],
    "location": ["location", "city", "place", "where", "based_in"],
    "timezone": ["timezone", "tz", "time_zone"],
    "project": ["project", "working_on", "current_project", "hackathon_project"],
    "job": ["job", "occupation", "role", "work", "profession"],
    "testing_framework": ["testing_framework", "test_framework", "testing_tool"],
    "api_framework": ["api_framework", "api_tool", "web_framework"],
    "type_hints": ["type_hints", "use_type_hints", "type_annotations"],
    "docstrings": ["docstrings", "documentation_style", "doc_style"],
    "line_length": ["line_length", "max_line_length", "code_width"],
    "database": ["database", "db", "database_system"],
    "latency_target": ["latency_target", "target_latency", "latency_goal"],
}
