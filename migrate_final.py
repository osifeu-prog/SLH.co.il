import os
import asyncio
import asyncpg

async def migrate():
    conn = await asyncpg.connect(os.environ['DATABASE_URL'])
    try:
        await conn.execute('''
            ALTER TABLE users 
            ADD COLUMN IF NOT EXISTS referral_code TEXT,
            ADD COLUMN IF NOT EXISTS referred_by BIGINT,
            ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT NOW(),
            ADD COLUMN IF NOT EXISTS last_seen TIMESTAMP DEFAULT NOW(),
            ADD COLUMN IF NOT EXISTS last_energy_update TIMESTAMP DEFAULT NOW(),
            ADD COLUMN IF NOT EXISTS energy INTEGER DEFAULT 100;
        ''')
        columns = await conn.fetch("SELECT column_name FROM information_schema.columns WHERE table_name='users'")
        print("✅ Columns now:")
        for c in columns:
            print("   •", c['column_name'])
        print("\n🎉 Migration completed successfully!")
    except Exception as e:
        print("❌ Error:", str(e))
    finally:
        await conn.close()

asyncio.run(migrate())
