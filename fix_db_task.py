import os
import psycopg2

db_url = os.environ['DATABASE_URL']
print(f"Connecting to DB from inside Railway...")
conn = psycopg2.connect(db_url)
cur = conn.cursor()

cur.execute('ALTER TABLE users ADD COLUMN IF NOT EXISTS points INTEGER DEFAULT 0;')
cur.execute('ALTER TABLE users ADD COLUMN IF NOT EXISTS streak INTEGER DEFAULT 0;')
cur.execute('ALTER TABLE users ADD COLUMN IF NOT EXISTS last_checkin DATE;')
cur.execute('ALTER TABLE users ADD COLUMN IF NOT EXISTS balance REAL DEFAULT 0;')
cur.execute('ALTER TABLE users ADD COLUMN IF NOT EXISTS tier TEXT DEFAULT \'free\';')
cur.execute('ALTER TABLE users ADD COLUMN IF NOT EXISTS energy INTEGER DEFAULT 100;')
cur.execute('ALTER TABLE users ADD COLUMN IF NOT EXISTS last_energy_update TIMESTAMP DEFAULT NOW();')

conn.commit()
cur.close()
conn.close()

print("✅ DB schema fixed successfully!")