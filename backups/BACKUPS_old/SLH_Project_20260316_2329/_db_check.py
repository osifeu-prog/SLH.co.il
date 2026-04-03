import os, asyncio, asyncpg

async def main():
    conn = await asyncpg.connect(
        host=os.getenv("DB_HOST", "127.0.0.1"),
        port=int(os.getenv("DB_PORT", "55432")),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASS"),
        database=os.getenv("DB_NAME"),
    )
    try:
        print("CONNECTED OK")
        rows = await conn.fetch("""
            select table_name
            from information_schema.tables
            where table_schema='public'
            order by table_name
        """)
        print("TABLES:")
        for r in rows:
            print("-", r["table_name"])

        exists = await conn.fetchval("select to_regclass('public.users')")
        print("USERS_TABLE:", exists)

        prod = await conn.fetch("""
            select id, code, title, price_ils, is_active
            from products
            where code='BUY'
        """)
        print("BUY_ROWS:", [dict(x) for x in prod])
    finally:
        await conn.close()

asyncio.run(main())
