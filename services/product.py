import json
from services.db import get_db

def add_product(store_id: int, name: str, price: float, metadata: dict = None) -> int:
    conn = get_db()
    cur = conn.cursor()
    cur.execute("INSERT INTO products (store_id, name, price, metadata) VALUES (%s,%s,%s,%s) RETURNING id",
                (store_id, name, price, json.dumps(metadata or {})))
    pid = cur.fetchone()[0]
    conn.commit()
    conn.close()
    return pid

def list_products(store_id: int) -> list:
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id, name, price FROM products WHERE store_id=%s", (store_id,))
    rows = cur.fetchall()
    conn.close()
    return [{"id": r[0], "name": r[1], "price": r[2]} for r in rows]

