import os
import psycopg2
import time

time.sleep(2)  # נותן לחיבור להתבסס
db_url = os.environ.get('DATABASE_URL')
if not db_url:
    print("❌ DATABASE_URL not found")
    exit(1)

print(f"Connecting to DB...")
conn = psycopg2.connect(db_url)
cur = conn.cursor()

# טבלת users (אם לא קיימת)
cur.execute("""
CREATE TABLE IF NOT EXISTS users (
    telegram_id BIGINT PRIMARY KEY,
    username TEXT,
    first_name TEXT,
    points INTEGER DEFAULT 0,
    streak INTEGER DEFAULT 0,
    last_checkin DATE,
    tier TEXT DEFAULT 'free',
    balance REAL DEFAULT 0,
    registered BOOLEAN DEFAULT FALSE,
    referral_code TEXT,
    referred_by BIGINT,
    created_at TIMESTAMP DEFAULT NOW()
)
""")

# טבלאות נוספות
cur.execute("""
CREATE TABLE IF NOT EXISTS wallets (
    user_id BIGINT PRIMARY KEY,
    ils REAL DEFAULT 0,
    ton REAL DEFAULT 0,
    usdt REAL DEFAULT 0
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS transactions (
    id SERIAL PRIMARY KEY,
    tx_hash TEXT UNIQUE,
    sender BIGINT,
    receiver BIGINT,
    amount REAL,
    currency TEXT DEFAULT 'ILS',
    status TEXT DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT NOW()
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS merchants (
    id SERIAL PRIMARY KEY,
    user_id BIGINT,
    name TEXT,
    description TEXT,
    logo TEXT,
    verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS products (
    id SERIAL PRIMARY KEY,
    merchant_id INTEGER,
    name TEXT,
    price REAL,
    currency TEXT DEFAULT 'ILS',
    stock INTEGER,
    image TEXT,
    created_at TIMESTAMP DEFAULT NOW()
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS orders (
    id SERIAL PRIMARY KEY,
    buyer_id BIGINT,
    merchant_id INTEGER,
    product_id INTEGER,
    amount REAL,
    status TEXT DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT NOW()
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS events (
    id SERIAL PRIMARY KEY,
    user_id BIGINT,
    event_type TEXT,
    metadata TEXT,
    created_at TIMESTAMP DEFAULT NOW()
)
""")

conn.commit()
cur.close()
conn.close()
print("✅ All tables and columns created/fixed successfully!")