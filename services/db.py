import os
import sqlite3
import psycopg2

def get_db():
    db_url = os.getenv("DATABASE_URL", "")
    if db_url:
        # Railway provides a full PostgreSQL URL  use it
        return psycopg2.connect(db_url)
    else:
        # Local development  use SQLite
        conn = sqlite3.connect("slh_local.db")
        conn.execute("PRAGMA journal_mode=WAL")
        return conn

def init_db():
    conn = get_db()
    cur = conn.cursor()
    is_sqlite = isinstance(conn, sqlite3.Connection)
    if is_sqlite:
        cur.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, telegram_id INTEGER UNIQUE NOT NULL, username TEXT, tier TEXT DEFAULT 'free', created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
        cur.execute("CREATE TABLE IF NOT EXISTS wallet_balances (user_id INTEGER PRIMARY KEY REFERENCES users(id), balance REAL DEFAULT 0, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
        cur.execute("CREATE TABLE IF NOT EXISTS ledger_transactions (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER REFERENCES users(id), type TEXT NOT NULL, category TEXT NOT NULL, amount REAL NOT NULL, currency TEXT DEFAULT 'USD', status TEXT DEFAULT 'completed', reference_id TEXT, metadata TEXT DEFAULT '{}', created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
        cur.execute("CREATE TABLE IF NOT EXISTS events (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER REFERENCES users(id), event_type TEXT NOT NULL, source TEXT DEFAULT 'telegram', entity_type TEXT, entity_id TEXT, metadata TEXT DEFAULT '{}', created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
        cur.execute("CREATE TABLE IF NOT EXISTS stores (id INTEGER PRIMARY KEY AUTOINCREMENT, owner_id INTEGER REFERENCES users(id), name TEXT, description TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
        cur.execute("CREATE TABLE IF NOT EXISTS products (id INTEGER PRIMARY KEY AUTOINCREMENT, store_id INTEGER REFERENCES stores(id), name TEXT, price REAL, metadata TEXT DEFAULT '{}')")
        cur.execute("CREATE TABLE IF NOT EXISTS orders (id INTEGER PRIMARY KEY AUTOINCREMENT, product_id INTEGER REFERENCES products(id), buyer_id INTEGER REFERENCES users(id), status TEXT DEFAULT 'pending', created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
    else:
        cur.execute("CREATE TABLE IF NOT EXISTS users (id BIGSERIAL PRIMARY KEY, telegram_id BIGINT UNIQUE NOT NULL, username TEXT, tier TEXT DEFAULT 'free', created_at TIMESTAMP DEFAULT NOW(), last_seen TIMESTAMP DEFAULT NOW())")
        cur.execute("CREATE TABLE IF NOT EXISTS wallet_balances (user_id BIGINT PRIMARY KEY REFERENCES users(id), balance NUMERIC DEFAULT 0, updated_at TIMESTAMP DEFAULT NOW())")
        cur.execute("CREATE TABLE IF NOT EXISTS ledger_transactions (id BIGSERIAL PRIMARY KEY, user_id BIGINT REFERENCES users(id), type TEXT NOT NULL, category TEXT NOT NULL, amount NUMERIC(12,2) NOT NULL, currency TEXT DEFAULT 'USD', status TEXT DEFAULT 'completed', reference_id TEXT, metadata JSONB DEFAULT '{}'::jsonb, created_at TIMESTAMP DEFAULT NOW())")
        cur.execute("CREATE TABLE IF NOT EXISTS events (id BIGSERIAL PRIMARY KEY, user_id BIGINT REFERENCES users(id), event_type TEXT NOT NULL, source TEXT DEFAULT 'telegram', entity_type TEXT, entity_id TEXT, metadata JSONB DEFAULT '{}'::jsonb, created_at TIMESTAMP DEFAULT NOW())")
        cur.execute("CREATE TABLE IF NOT EXISTS stores (id BIGSERIAL PRIMARY KEY, owner_id BIGINT REFERENCES users(id), name TEXT, description TEXT, created_at TIMESTAMP DEFAULT NOW())")
        cur.execute("CREATE TABLE IF NOT EXISTS products (id BIGSERIAL PRIMARY KEY, store_id BIGINT REFERENCES stores(id), name TEXT, price NUMERIC(12,2), metadata JSONB DEFAULT '{}'::jsonb)")
        cur.execute("CREATE TABLE IF NOT EXISTS orders (id BIGSERIAL PRIMARY KEY, product_id BIGINT REFERENCES products(id), buyer_id BIGINT REFERENCES users(id), status TEXT DEFAULT 'pending', created_at TIMESTAMP DEFAULT NOW())")
    conn.commit()
    conn.close()

