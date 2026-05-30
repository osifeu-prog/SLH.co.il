import os
import psycopg2

SCHEMA_STATEMENTS = [
    """CREATE TABLE IF NOT EXISTS users (
        id BIGSERIAL PRIMARY KEY,
        telegram_id BIGINT UNIQUE NOT NULL,
        username TEXT,
        tier TEXT DEFAULT 'free',
        created_at TIMESTAMP DEFAULT NOW(),
        last_seen TIMESTAMP DEFAULT NOW()
    )""",
    """CREATE TABLE IF NOT EXISTS wallet_balances (
        user_id BIGINT PRIMARY KEY REFERENCES users,
        balance NUMERIC DEFAULT 0,
        updated_at TIMESTAMP DEFAULT NOW()
    )""",
    """CREATE TABLE IF NOT EXISTS ledger_transactions (
        id BIGSERIAL PRIMARY KEY,
        user_id BIGINT REFERENCES users,
        type TEXT NOT NULL,
        category TEXT NOT NULL,
        amount NUMERIC(12,2) NOT NULL,
        currency TEXT DEFAULT 'USD',
        status TEXT DEFAULT 'completed',
        reference_id TEXT,
        metadata JSONB DEFAULT '{}'::jsonb,
        created_at TIMESTAMP DEFAULT NOW()
    )""",
    """CREATE TABLE IF NOT EXISTS events (
        id BIGSERIAL PRIMARY KEY,
        user_id BIGINT REFERENCES users,
        event_type TEXT NOT NULL,
        source TEXT DEFAULT 'telegram',
        entity_type TEXT,
        entity_id TEXT,
        metadata JSONB DEFAULT '{}'::jsonb,
        created_at TIMESTAMP DEFAULT NOW()
    )""",
    """CREATE TABLE IF NOT EXISTS stores (
        id BIGSERIAL PRIMARY KEY,
        owner_id BIGINT REFERENCES users,
        name TEXT,
        description TEXT,
        created_at TIMESTAMP DEFAULT NOW()
    )""",
    """CREATE TABLE IF NOT EXISTS products (
        id BIGSERIAL PRIMARY KEY,
        store_id BIGINT REFERENCES stores,
        name TEXT,
        price NUMERIC(12,2),
        metadata JSONB DEFAULT '{}'::jsonb
    )""",
    """CREATE TABLE IF NOT EXISTS orders (
        id BIGSERIAL PRIMARY KEY,
        product_id BIGINT REFERENCES products,
        buyer_id BIGINT REFERENCES users,
        status TEXT DEFAULT 'pending',
        created_at TIMESTAMP DEFAULT NOW()
    )"""
]

def get_db():
    return psycopg2.connect(os.getenv("DATABASE_URL"))

def init_db():
    conn = get_db()
    cur = conn.cursor()
    for stmt in SCHEMA_STATEMENTS:
        cur.execute(stmt)
    conn.commit()
    conn.close()
