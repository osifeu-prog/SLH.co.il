from services.db import get_db

def create_store(owner_id: int, name: str, description: str = "") -> int:
    conn = get_db()
    cur = conn.cursor()
    cur.execute("INSERT INTO stores (owner_id, name, description) VALUES (%s,%s,%s) RETURNING id", (owner_id, name, description))
    sid = cur.fetchone()[0]
    conn.commit()
    conn.close()
    return sid

def get_store(store_id: int) -> dict:
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM stores WHERE id=%s", (store_id,))
    row = cur.fetchone()
    conn.close()
    return {"id": row[0], "owner_id": row[1], "name": row[2], "description": row[3]} if row else None
