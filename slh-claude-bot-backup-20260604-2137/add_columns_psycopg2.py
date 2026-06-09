import os, psycopg2

conn = psycopg2.connect(os.environ["DATABASE_URL"])
cur = conn.cursor()
cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS referral_code TEXT")
cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS referred_by BIGINT")
cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT NOW()")
cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS last_seen TIMESTAMP DEFAULT NOW()")
conn.commit()
cur.close()
conn.close()
print("✅ Columns added")
