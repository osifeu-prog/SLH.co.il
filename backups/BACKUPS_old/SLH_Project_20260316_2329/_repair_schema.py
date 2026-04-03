import os, asyncio, asyncpg

SQL = """
CREATE TABLE IF NOT EXISTS users (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT UNIQUE NOT NULL,
    username TEXT,
    role TEXT DEFAULT 'user',
    balance NUMERIC DEFAULT 0,
    last_claim TIMESTAMP DEFAULT TIMESTAMP '1970-01-01 00:00:00',
    invited_count INTEGER DEFAULT 0,
    total_sold NUMERIC DEFAULT 0,
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS products (
    id BIGSERIAL PRIMARY KEY,
    code TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    price_ils NUMERIC(12,4) NOT NULL DEFAULT 0,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS purchase_orders (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    product_code TEXT NOT NULL,
    qty INTEGER NOT NULL DEFAULT 1,
    status TEXT NOT NULL DEFAULT 'pending',
    external_payment_ref TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS user_balances (
    user_id BIGINT PRIMARY KEY,
    available NUMERIC(18,8) NOT NULL DEFAULT 0,
    locked NUMERIC(18,8) NOT NULL DEFAULT 0,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS audit_log (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT,
    event_type TEXT,
    payload_json JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO products (code, title, price_ils, is_active)
VALUES ('BUY', 'BUY Entry + Friends Group', 22.2221, TRUE)
ON CONFLICT (code) DO UPDATE
SET title = EXCLUDED.title,
    price_ils = EXCLUDED.price_ils,
    is_active = EXCLUDED.is_active;
"""

async def main():
    conn = await asyncpg.connect(
        host=os.getenv("DB_HOST", "127.0.0.1"),
        port=int(os.getenv("DB_PORT", "55432")),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASS"),
        database=os.getenv("DB_NAME"),
    )
    try:
        await conn.execute(SQL)
        print("SCHEMA_OK")
        rows = await conn.fetch("""
            select table_name
            from information_schema.tables
            where table_schema='public'
            order by table_name
        """)
        print("TABLES:", [r["table_name"] for r in rows])

        prod = await conn.fetch("""
            select id, code, title, price_ils, is_active
            from products
            where code='BUY'
        """)
        print("BUY_ROWS:", [dict(x) for x in prod])
    finally:
        await conn.close()

asyncio.run(main())
