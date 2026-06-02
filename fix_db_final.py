import psycopg2

# âš ï¸ ×”×—×œ×£ ×‘×›×ª×•×‘×ª ×”×¦×™×‘×•×¨×™×ª ×©×œ×š ×ž-Railway Dashboard
DB_URL = "postgresql://postgres:oPDCKJGOZvNKPaTlNIlWfYnDGsNjgqRg@baboon-production.up.railway.app:5432/railway"

conn = psycopg2.connect(DB_URL)
cur = conn.cursor()

cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS points INTEGER DEFAULT 0;")
cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS streak INTEGER DEFAULT 0;")
cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS last_checkin DATE;")
cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS balance REAL DEFAULT 0;")
cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS tier TEXT DEFAULT 'free';")
cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS energy INTEGER DEFAULT 100;")
cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS last_energy_update TIMESTAMP DEFAULT NOW();")

conn.commit()
cur.close()
conn.close()

print("âœ… DB fixed successfully!")
