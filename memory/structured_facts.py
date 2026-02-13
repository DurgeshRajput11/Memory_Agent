"""
Structured facts store — deterministic, key-based storage for important user facts.

NO embeddings. NO similarity search. Only exact key lookup.

Use cases:
- User identity (name, pronouns, demographics)
- Preferences (language, timezone, notification settings)
- Constraints (dietary restrictions, accessibility needs)
- Instructions (coding style, communication preferences)
"""

import logging
from typing import List, Optional
from database import get_conn, put_conn

logger = logging.getLogger(__name__)


def upsert_fact(
    user_id: str,
    category: str,
    key: str,
    value: str,
    confidence: float = 1.0,
    importance: float = 0.8
) -> bool:
    """
    Insert or update a structured fact. Uses ON CONFLICT to handle uniqueness.
    
    Returns True if successful, False otherwise.
    """
    conn = get_conn()
    try:
        cur = conn.cursor()
        
        # Upsert: insert or update if conflict on (user_id, category, key, is_active=TRUE)
        cur.execute(
            """
            INSERT INTO structured_facts (user_id, category, key, value, confidence, importance, is_active)
            VALUES (%s, %s, %s, %s, %s, %s, TRUE)
            ON CONFLICT (user_id, category, key, is_active)
            DO UPDATE SET
                value = EXCLUDED.value,
                confidence = EXCLUDED.confidence,
                importance = EXCLUDED.importance,
                updated_at = NOW()
            WHERE structured_facts.confidence <= EXCLUDED.confidence
            """,
            (user_id, category, key, value, confidence, importance)
        )
        
        conn.commit()
        cur.close()
        logger.info("Upserted fact: [%s] %s = %s (confidence=%.2f)", category, key, value, confidence)
        return True
        
    except Exception as e:
        conn.rollback()
        logger.error("Failed to upsert fact: %s", e)
        return False
    finally:
        put_conn(conn)


def get_facts_by_keys(user_id: str, keys: List[str]) -> List[dict]:
    """
    Deterministic lookup: fetch active facts for specific keys.
    
    Returns list of dicts: [{"category", "key", "value", "confidence", "importance"}, ...]
    """
    if not keys:
        return []
    
    conn = get_conn()
    try:
        cur = conn.cursor()
        
        # Use IN clause for multiple keys
        placeholders = ','.join(['%s'] * len(keys))
        cur.execute(
            f"""
            SELECT category, key, value, confidence, importance, updated_at
            FROM structured_facts
            WHERE user_id = %s
              AND key IN ({placeholders})
              AND is_active = TRUE
            ORDER BY importance DESC, updated_at DESC
            """,
            [user_id] + keys
        )
        
        rows = cur.fetchall()
        cur.close()
        
        results = []
        for row in rows:
            results.append({
                "category": row[0],
                "key": row[1],
                "value": row[2],
                "confidence": row[3],
                "importance": row[4],
                "updated_at": row[5]
            })
        
        return results
        
    except Exception as e:
        logger.error("Failed to retrieve facts by keys: %s", e)
        return []
    finally:
        put_conn(conn)


def get_all_facts(user_id: str, min_importance: float = 0.0) -> List[dict]:
    """
    Get all active facts for a user (useful for debugging/display).
    
    Returns list of dicts ordered by importance.
    """
    conn = get_conn()
    try:
        cur = conn.cursor()
        
        cur.execute(
            """
            SELECT category, key, value, confidence, importance
            FROM structured_facts
            WHERE user_id = %s
              AND is_active = TRUE
              AND importance >= %s
            ORDER BY importance DESC, updated_at DESC
            """,
            (user_id, min_importance)
        )
        
        rows = cur.fetchall()
        cur.close()
        
        results = []
        for row in rows:
            results.append({
                "category": row[0],
                "key": row[1],
                "value": row[2],
                "confidence": row[3],
                "importance": row[4]
            })
        
        return results
        
    except Exception as e:
        logger.error("Failed to retrieve all facts: %s", e)
        return []
    finally:
        put_conn(conn)


def delete_fact(user_id: str, category: str, key: str) -> bool:
    """
    Soft-delete a fact by setting is_active = FALSE.
    """
    conn = get_conn()
    try:
        cur = conn.cursor()
        
        cur.execute(
            """
            UPDATE structured_facts
            SET is_active = FALSE, updated_at = NOW()
            WHERE user_id = %s
              AND category = %s
              AND key = %s
              AND is_active = TRUE
            """,
            (user_id, category, key)
        )
        
        conn.commit()
        rows_affected = cur.rowcount
        cur.close()
        
        if rows_affected > 0:
            logger.info("Deleted fact: [%s] %s for user %s", category, key, user_id)
            return True
        else:
            logger.warning("No active fact found to delete: [%s] %s", category, key)
            return False
            
    except Exception as e:
        conn.rollback()
        logger.error("Failed to delete fact: %s", e)
        return False
    finally:
        put_conn(conn)
