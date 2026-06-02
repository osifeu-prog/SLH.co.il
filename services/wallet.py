from services.db import get_db

def get_balance(user_id: int) -> float:
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT balance FROM wallet_balances WHERE user_id=%s", (user_id,))
    row = cur.fetchone()
    conn.close()
    return row[0] if row else 0.0

def add_balance(user_id: int, amount: float):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO wallet_balances (user_id, balance)
        VALUES (%s, %s)
        ON CONFLICT (user_id) DO UPDATE SET balance = wallet_balances.balance + %s
    """, (user_id, amount, amount))
    conn.commit()
    conn.close()

def transfer(from_user: int, to_user: int, amount: float) -> bool:
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT balance FROM wallet_balances WHERE user_id=%s", (from_user,))
    row = cur.fetchone()
    if not row or row[0] < amount:
        conn.close()
        return False
    cur.execute("UPDATE wallet_balances SET balance = balance - %s WHERE user_id=%s", (amount, from_user))
    cur.execute("""
        INSERT INTO wallet_balances (user_id, balance)
        VALUES (%s, %s)
        ON CONFLICT (user_id) DO UPDATE SET balance = wallet_balances.balance + %s
    """, (to_user, amount, amount))
    conn.commit()
    conn.close()
    return True

