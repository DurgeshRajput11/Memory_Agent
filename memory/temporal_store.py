"""
Temporal memory store — upsert with soft-delete (valid_to) for versioning.
"""

import logging
from database import get_conn, put_conn, embed

logger = logging.getLogger(__name__)


def upsert_memory(user_id: str, mem_type: str, key: str, value: str, confidence: float = 1.0):
    """Soft-close any existing active memory for the same (user, type, key) and insert a new version."""
    conn = get_conn()
    try:
        cur = conn.cursor()

        embedding = embed(f"{mem_type} {key} {value}")

        # Close previous active entry
        cur.execute(
            """
            UPDATE profile_memory
            SET valid_to = NOW()
            WHERE user_id = %s
              AND type    = %s
              AND key     = %s
              AND valid_to IS NULL
            """,
            (user_id, mem_type, key),
        )

        # Insert new version
        cur.execute(
            """
            INSERT INTO profile_memory (user_id, type, key, value, confidence, embedding)
            VALUES (%s, %s, %s, %s, %s, %s::vector)
            """,
            (user_id, mem_type, key, value, confidence, embedding),
        )

        conn.commit()
        cur.close()
        logger.debug("Upserted memory [%s] %s=%s for user %s", mem_type, key, value, user_id)

    except Exception as e:
        conn.rollback()
        logger.error("Failed to upsert memory: %s", e)
    finally:
        put_conn(conn)
