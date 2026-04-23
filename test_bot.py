import os
import asyncpg
from telegram import Bot

async def test_bot():
    print("=== SLH BOT TEST ===")
    
    # Check environment variables
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    db_url = os.getenv("DATABASE_URL")
    
    print(f"1. TELEGRAM_BOT_TOKEN: {'✅ Set' if token else '❌ Missing'}")
    print(f"2. DATABASE_URL: {'✅ Set' if db_url else '❌ Missing'}")
    
    if not token or not db_url:
        print("\n❌ Missing environment variables!")
        return
    
    # Test database
    try:
        conn = await asyncpg.connect(db_url)
        version = await conn.fetchval("SELECT version()")
        await conn.close()
        print(f"3. Database: ✅ Connected (PostgreSQL {version[:20]})")
    except Exception as e:
        print(f"3. Database: ❌ Error - {e}")
    
    # Test bot
    try:
        bot = Bot(token=token)
        me = await bot.get_me()
        print(f"4. Bot: ✅ Connected - @{me.username}")
    except Exception as e:
        print(f"4. Bot: ❌ Error - {e}")
    
    print("\n✅ Test complete!")

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_bot())
