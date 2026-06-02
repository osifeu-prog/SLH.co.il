from services.db import get_db
import json
from datetime import datetime

def log_transaction(user_id: int, t_type: str, category: str, amount: float, currency: str = "USD", reference: str = None, metadata: dict = None):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO ledger_transactions (user_id, type, category, amount, currency, reference_id, metadata)
        VALUES (%s,%s,%s,%s,%s,%s,%s)
    """, (user_id, t_type, category, amount, currency, reference, json.dumps(metadata or {})))
    conn.commit()
    conn.close()

