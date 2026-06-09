import os, asyncio, asyncpg

async def main():
    conn = await asyncpg.connect(os.environ['DATABASE_URL'])
    rows = await conn.fetch("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name")
    print("Tables in database:")
    for r in rows:
        print(f"  - {r['table_name']}")
    await conn.close()

asyncio.run(main())
