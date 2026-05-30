from services.db import get_db
from services.wallet import transfer

def create_order(buyer_id: int, product_id: int, price: float, seller_id: int) -> bool:
    if not transfer(buyer_id, seller_id, price):
        return False
    conn = get_db()
    cur = conn.cursor()
    cur.execute("INSERT INTO orders (product_id, buyer_id, status) VALUES (%s,%s,'completed')", (product_id, buyer_id))
    conn.commit()
    conn.close()
    return True
