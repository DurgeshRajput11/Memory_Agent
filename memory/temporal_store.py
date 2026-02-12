from database import conn, embed

def upsert_memory(user_id, mem_type, key, value, confidence=1.0):
    cur = conn.cursor()

    embedding = embed(f"{mem_type} {key} {value}")

    # Close old active memory
    cur.execute("""
        UPDATE profile_memory
        SET valid_to = NOW()
        WHERE user_id=%s
        AND type=%s
        AND key=%s
        AND valid_to IS NULL
    """, (user_id, mem_type, key))

    # Insert new
    cur.execute("""
        INSERT INTO profile_memory
        (user_id, type, key, value, confidence, embedding)
        VALUES (%s,%s,%s,%s,%s,%s)
    """, (user_id, mem_type, key, value, confidence, embedding))

    conn.commit()
    cur.close()
