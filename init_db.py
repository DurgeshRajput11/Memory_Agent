"""
Database schema initialization for the memory agent.

Run once:  python init_db.py
"""

import psycopg2
from config import DB_CONFIG

def init():
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    # Enable pgvector extension
    cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")

    # Core memory table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS profile_memory (
            id          SERIAL PRIMARY KEY,
            user_id     TEXT NOT NULL,
            type        TEXT NOT NULL,          -- preference | constraint | commitment | instruction
            key         TEXT NOT NULL,
            value       TEXT NOT NULL,
            confidence  FLOAT DEFAULT 1.0,
            embedding   vector(384),            -- all-MiniLM-L6-v2 produces 384-d vectors
            valid_from  TIMESTAMPTZ DEFAULT NOW(),
            valid_to    TIMESTAMPTZ,            -- NULL = currently active
            created_at  TIMESTAMPTZ DEFAULT NOW()
        );
    """)

    # Index for fast vector similarity search
    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_memory_embedding
        ON profile_memory
        USING ivfflat (embedding vector_cosine_ops)
        WITH (lists = 100);
    """)

    # Index for user + active lookup
    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_memory_user_active
        ON profile_memory (user_id, valid_to);
    """)

    conn.commit()
    cur.close()
    conn.close()
    print("✅ Database schema initialized successfully.")


if __name__ == "__main__":
    init()
