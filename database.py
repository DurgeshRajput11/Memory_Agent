"""
Database helpers — connection pool + embedding utility.
"""

import logging
import psycopg2
from psycopg2 import pool
from sentence_transformers import SentenceTransformer
from config import DB_CONFIG, EMBEDDING_MODEL

logger = logging.getLogger(__name__)

_pool: pool.SimpleConnectionPool | None = None


def _init_pool():
    """Create the connection pool on first use (lazy)."""
    global _pool
    if _pool is not None:
        return
    try:
        _pool = pool.SimpleConnectionPool(1, 10, **DB_CONFIG)
        logger.info("Database connection pool created.")
    except Exception as e:
        _pool = None
        logger.warning("PostgreSQL is not reachable — memory features disabled. (%s)", e)


def get_conn():
    """Get a connection from the pool (initialises pool on first call)."""
    _init_pool()
    if _pool is None:
        raise RuntimeError("Database pool is not initialised. Is PostgreSQL running?")
    return _pool.getconn()


def put_conn(conn):
    """Return a connection to the pool."""
    if _pool is not None:
        _pool.putconn(conn)


# ── Embedding model (loaded once) ────────────────────────────
model = SentenceTransformer(EMBEDDING_MODEL)


def embed(text: str) -> str:
    """Return a pgvector-compatible string, e.g. '[0.1,0.2,...]'."""
    vec = model.encode(text).tolist()
    return "[" + ",".join(str(round(v, 8)) for v in vec) + "]"
