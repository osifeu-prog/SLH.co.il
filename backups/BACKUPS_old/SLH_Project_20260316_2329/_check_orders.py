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
        rows = await conn.fetch("""
            select id, user_id, product_code, status, created_at
            from purchase_orders
            order by id desc
            limit 10
        """)
        print([dict(x) for x in rows])
    finally:
        await conn.close()

asyncio.run(main())
