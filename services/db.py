import os
import psycopg2

def get_db():
    return psycopg2.connect(os.getenv("DATABASE_URL"))

def init_db():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DROP TABLE IF EXISTS wallet_balances CASCADE")
    cur.execute("DROP TABLE IF EXISTS users CASCADE")
    cur.execute("""
        CREATE TABLE users (
            id BIGSERIAL PRIMARY KEY,
            telegram_id BIGINT UNIQUE NOT NULL,
            username TEXT,
            tier TEXT DEFAULT 'free',
            created_at TIMESTAMP DEFAULT NOW(),
            last_seen TIMESTAMP DEFAULT NOW()
        )
    """)
    cur.execute("""
        CREATE TABLE wallet_balances (
            user_id BIGINT PRIMARY KEY REFERENCES users(id),
            balance NUMERIC DEFAULT 0,
            updated_at TIMESTAMP DEFAULT NOW()
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS ledger_transactions (
            id BIGSERIAL PRIMARY KEY,
            user_id BIGINT REFERENCES users(id),
            type TEXT NOT NULL,
            category TEXT NOT NULL,
            amount NUMERIC(12,2) NOT NULL,
            currency TEXT DEFAULT 'USD',
            status TEXT DEFAULT 'completed',
            reference_id TEXT,
            metadata JSONB DEFAULT '{}'::jsonb,
            created_at TIMESTAMP DEFAULT NOW()
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id BIGSERIAL PRIMARY KEY,
            user_id BIGINT REFERENCES users(id),
            event_type TEXT NOT NULL,
            source TEXT DEFAULT 'telegram',
            entity_type TEXT,
            entity_id TEXT,
            metadata JSONB DEFAULT '{}'::jsonb,
            created_at TIMESTAMP DEFAULT NOW()
        )
    """)
    conn.commit()
    conn.close()
