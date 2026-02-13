-- Migration 002: Restructure memory into structured facts + episodic memory
-- Run after 001_create_memories.sql (or alongside init_db.py)

-- ============================================================
-- STRUCTURED FACTS (Long-term, deterministic, no embeddings)
-- ============================================================
CREATE TABLE IF NOT EXISTS structured_facts (
    id              SERIAL PRIMARY KEY,
    user_id         TEXT NOT NULL,
    
    -- Fact identification
    category        TEXT NOT NULL,  -- 'identity' | 'preference' | 'constraint' | 'instruction'
    key             TEXT NOT NULL,  -- 'name' | 'language' | 'timezone' | 'coding_style' | etc.
    value           TEXT NOT NULL,
    
    -- Metadata
    confidence      FLOAT DEFAULT 1.0,
    importance      FLOAT DEFAULT 0.8,
    
    -- Versioning (soft-delete for history)
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW(),
    is_active       BOOLEAN DEFAULT TRUE,
    
    -- Ensure one active fact per (user, category, key)
    UNIQUE (user_id, category, key, is_active)
);

-- Index for fast deterministic lookup
CREATE INDEX IF NOT EXISTS idx_facts_user_active 
ON structured_facts (user_id, is_active) 
WHERE is_active = TRUE;

CREATE INDEX IF NOT EXISTS idx_facts_keys
ON structured_facts (user_id, key, is_active);


-- ============================================================
-- EPISODIC MEMORY (Mid-term, conversational, vector-based)
-- ============================================================
CREATE TABLE IF NOT EXISTS episodic_memory (
    id              SERIAL PRIMARY KEY,
    user_id         TEXT NOT NULL,
    
    -- Content
    turn_range      TEXT,           -- e.g., "turns 21-40"
    summary         TEXT NOT NULL,   -- Compressed conversation summary
    embedding       vector(384),     -- For semantic retrieval
    
    -- Metadata
    turn_start      INT,
    turn_end        INT,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Index for vector similarity search on episodic memory
CREATE INDEX IF NOT EXISTS idx_episodic_embedding
ON episodic_memory
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

CREATE INDEX IF NOT EXISTS idx_episodic_user
ON episodic_memory (user_id, created_at DESC);


-- ============================================================
-- MIGRATE OLD DATA (if profile_memory exists)
-- ============================================================
-- If you want to preserve old profile_memory data, uncomment:
-- INSERT INTO structured_facts (user_id, category, key, value, confidence, is_active)
-- SELECT user_id, type, key, value, confidence, (valid_to IS NULL)
-- FROM profile_memory
-- WHERE type IN ('preference', 'identity', 'constraint', 'instruction');
