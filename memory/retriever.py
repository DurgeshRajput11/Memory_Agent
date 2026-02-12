from database import conn, embed

def retrieve_active(user_id, query, top_k=3):
    cur = conn.cursor()
    query_embedding = embed(query)

    cur.execute("""
        SELECT type, key, value
        FROM profile_memory
        WHERE user_id=%s
        AND valid_to IS NULL
        ORDER BY embedding <-> %s
        LIMIT %s
    """, (user_id, query_embedding, top_k))

    results = cur.fetchall()
    cur.close()
    return results
