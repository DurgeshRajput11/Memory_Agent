"""
Episodic memory store — mid-term conversational memory with vector embeddings.

Stores compressed summaries of conversation chunks (e.g., turns 21-40).
Used for semantic retrieval of past context beyond short-term window.
"""

import logging
from typing import List, Optional
from database import get_conn, put_conn, embed

logger = logging.getLogger(__name__)


def store_episode(
    user_id: str,
    summary: str,
    turn_start: int,
    turn_end: int
) -> bool:
    """
    Store a conversation episode (summary + embedding).
    
    Args:
        user_id: User identifier
        summary: Compressed text summary of conversation turns
        turn_start: Starting turn number (inclusive)
        turn_end: Ending turn number (inclusive)
    
    Returns:
        True if successful, False otherwise
    """
    conn = get_conn()
    try:
        cur = conn.cursor()
        
        # Generate embedding for the summary
        embedding = embed(summary)
        turn_range = f"turns {turn_start}-{turn_end}"
        
        cur.execute(
            """
            INSERT INTO episodic_memory (user_id, turn_range, summary, embedding, turn_start, turn_end)
            VALUES (%s, %s, %s, %s::vector, %s, %s)
            """,
            (user_id, turn_range, summary, embedding, turn_start, turn_end)
        )
        
        conn.commit()
        cur.close()
        logger.info("Stored episode for user %s: %s", user_id, turn_range)
        return True
        
    except Exception as e:
        conn.rollback()
        logger.error("Failed to store episode: %s", e)
        return False
    finally:
        put_conn(conn)


def retrieve_episodes(
    user_id: str,
    query: str,
    top_k: int = 5,
    similarity_threshold: float = 0.4
) -> List[dict]:
    """
    Retrieve relevant conversation episodes using vector similarity.
    
    Args:
        user_id: User identifier
        query: Query text to find relevant episodes
        top_k: Maximum number of episodes to return
        similarity_threshold: Minimum similarity score (cosine distance threshold)
    
    Returns:
        List of dicts: [{"turn_range", "summary", "turn_start", "turn_end", "distance"}, ...]
    """
    conn = get_conn()
    try:
        cur = conn.cursor()
        
        query_embedding = embed(query)
        
        cur.execute(
            """
            SELECT turn_range, summary, turn_start, turn_end,
                   embedding <=> %s::vector AS distance
            FROM episodic_memory
            WHERE user_id = %s
              AND embedding <=> %s::vector < %s
            ORDER BY distance ASC
            LIMIT %s
            """,
            (query_embedding, user_id, query_embedding, similarity_threshold, top_k)
        )
        
        rows = cur.fetchall()
        cur.close()
        
        results = []
        for row in rows:
            results.append({
                "turn_range": row[0],
                "summary": row[1],
                "turn_start": row[2],
                "turn_end": row[3],
                "distance": float(row[4])
            })
        
        logger.debug("Retrieved %d episodes for user %s", len(results), user_id)
        return results
        
    except Exception as e:
        logger.error("Failed to retrieve episodes: %s", e)
        return []
    finally:
        put_conn(conn)


def get_recent_episodes(user_id: str, limit: int = 3) -> List[dict]:
    """
    Get the most recent conversation episodes (by creation time).
    Useful for maintaining continuity without semantic search.
    """
    conn = get_conn()
    try:
        cur = conn.cursor()
        
        cur.execute(
            """
            SELECT turn_range, summary, turn_start, turn_end
            FROM episodic_memory
            WHERE user_id = %s
            ORDER BY created_at DESC
            LIMIT %s
            """,
            (user_id, limit)
        )
        
        rows = cur.fetchall()
        cur.close()
        
        results = []
        for row in rows:
            results.append({
                "turn_range": row[0],
                "summary": row[1],
                "turn_start": row[2],
                "turn_end": row[3]
            })
        
        return results
        
    except Exception as e:
        logger.error("Failed to get recent episodes: %s", e)
        return []
    finally:
        put_conn(conn)


def count_episodes(user_id: str) -> int:
    """Count total episodes stored for a user."""
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM episodic_memory WHERE user_id = %s", (user_id,))
        count = cur.fetchone()[0]
        cur.close()
        return count
    except Exception as e:
        logger.error("Failed to count episodes: %s", e)
        return 0
    finally:
        put_conn(conn)
