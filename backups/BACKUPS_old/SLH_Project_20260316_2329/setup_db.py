import asyncpg, asyncio, os
from dotenv import load_dotenv
load_dotenv()

async def setup():
    print('\x1b[36m[*] Connecting to database...\x1b[0m')
    try:
        conn = await asyncpg.connect(host=os.getenv('DB_HOST'), user=os.getenv('DB_USER'), password=os.getenv('DB_PASS'), database=os.getenv('DB_NAME'))
        await conn.execute('CREATE TABLE IF NOT EXISTS users (id SERIAL PRIMARY KEY, user_id BIGINT UNIQUE);')
        print('\x1b[32m[+] Database schema ready.\x1b[0m')
        await conn.close()
    except Exception as e:
        print(f'\x1b[31m[!] Error: {e}\x1b[0m')

if __name__ == '__main__':
    asyncio.run(setup())
