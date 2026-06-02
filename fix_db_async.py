import os
import asyncpg
import asyncio

async def fix_db():
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
        print("✅ Columns added successfully!")
        
        # בדיקה
        cols = await conn.fetch("SELECT column_name FROM information_schema.columns WHERE table_name='users'")
        print("Columns now:", [r['column_name'] for r in cols])
    finally:
        await conn.close()

asyncio.run(fix_db())
