"""
Active long-term memory retriever — vector similarity search with threshold.
"""

import logging
from database import get_conn, put_conn, embed
from config import TOP_K, SIMILARITY_THRESHOLD

logger = logging.getLogger(__name__)


def retrieve_active(user_id: str, query: str, top_k: int = TOP_K) -> list[tuple]:
    """
    Return top-K active memories whose cosine distance is below the threshold.
    Each row: (type, key, value, distance)
    """
    conn = get_conn()
    try:
        cur = conn.cursor()
        query_embedding = embed(query)

        cur.execute(
            """
            SELECT type, key, value,
                   embedding <=> %s::vector AS distance
            FROM profile_memory
            WHERE user_id = %s
              AND valid_to IS NULL
              AND embedding <=> %s::vector < %s
            ORDER BY distance
            LIMIT %s
            """,
            (query_embedding, user_id, query_embedding, SIMILARITY_THRESHOLD, top_k),
        )

        results = cur.fetchall()
        cur.close()
        return results

    except Exception as e:
        logger.error("Memory retrieval failed: %s", e)
        return []
    finally:
        put_conn(conn)
