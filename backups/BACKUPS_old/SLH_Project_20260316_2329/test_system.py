import asyncio
import os
import asyncpg
from dotenv import load_dotenv
from aiogram import Bot

load_dotenv()

async def test_all():
    print("--- Starting System Check ---")
    
    # 1. Check .env
    token = os.getenv("BOT_TOKEN")
    db_url = os.getenv("DB_URL")
    if not token or not db_url:
        print(" Error: Missing environment variables in .env")
        return
    print(" .env variables loaded.")

    # 2. Check Bot Token
    try:
        bot = Bot(token=token)
        me = await bot.get_me()
        print(f" Bot Connection: Success! Bot Name: @{me.username}")
        await bot.session.close()
    except Exception as e:
        print(f" Bot Error: {e}")

    # 3. Check Docker DB Connection
    try:
        conn = await asyncpg.connect(dsn=db_url)
        print(" Database Connection: Success! Docker is responding.")
        
        # Check if table exists
        version = await conn.fetchval("SELECT version()")
        print(f" Postgres Version: {version}")
        
        user_count = await conn.fetchval("SELECT COUNT(*) FROM users")
        print(f" Users in DB: {user_count}")
        
        await conn.close()
    except Exception as e:
        print(f" Database Error: {e}")

    print("--- Check Complete ---")

if __name__ == '__main__':
    asyncio.run(test_all())
