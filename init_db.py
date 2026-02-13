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

    # ============================================================
    # STRUCTURED FACTS (Long-term, deterministic, no embeddings)
    # ============================================================
    cur.execute("""
        CREATE TABLE IF NOT EXISTS structured_facts (
            id              SERIAL PRIMARY KEY,
            user_id         TEXT NOT NULL,
            category        TEXT NOT NULL,
            key             TEXT NOT NULL,
            value           TEXT NOT NULL,
            confidence      FLOAT DEFAULT 1.0,
            importance      FLOAT DEFAULT 0.8,
            created_at      TIMESTAMPTZ DEFAULT NOW(),
            updated_at      TIMESTAMPTZ DEFAULT NOW(),
            is_active       BOOLEAN DEFAULT TRUE
        );
    """)

    cur.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS idx_facts_unique
        ON structured_facts (user_id, category, key, is_active)
        WHERE is_active = TRUE;
    """)

    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_facts_user_active 
        ON structured_facts (user_id, is_active) 
        WHERE is_active = TRUE;
    """)

    # ============================================================
    # EPISODIC MEMORY (Mid-term, conversational, vector-based)
    # ============================================================
    cur.execute("""
        CREATE TABLE IF NOT EXISTS episodic_memory (
            id              SERIAL PRIMARY KEY,
            user_id         TEXT NOT NULL,
            turn_range      TEXT,
            summary         TEXT NOT NULL,
            embedding       vector(384),
            turn_start      INT,
            turn_end        INT,
            created_at      TIMESTAMPTZ DEFAULT NOW()
        );
    """)

    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_episodic_embedding
        ON episodic_memory
        USING ivfflat (embedding vector_cosine_ops)
        WITH (lists = 100);
    """)

    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_episodic_user
        ON episodic_memory (user_id, created_at DESC);
    """)

    # ============================================================
    # OLD profile_memory table (keep for backward compatibility)
    # ============================================================
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
