import os, psycopg2, time
from dotenv import load_dotenv

load_dotenv()
db_url = os.getenv('DATABASE_URL')
if not db_url:
    print("No DATABASE_URL")
    exit(1)

conn = psycopg2.connect(db_url)
cur = conn.cursor()
tables = ["points", "streak", "last_checkin", "balance", "tier", "energy", "last_energy_update"]
col_types = ["INTEGER DEFAULT 0", "INTEGER DEFAULT 0", "DATE", "REAL DEFAULT 0", "TEXT DEFAULT 'free'", "INTEGER DEFAULT 100", "TIMESTAMP DEFAULT NOW()"]
for col, typ in zip(tables, col_types):
    try:
        cur.execute(f"ALTER TABLE users ADD COLUMN IF NOT EXISTS {col} {typ}")
        print(f"Added {col}")
    except Exception as e:
        print(f"Skip {col}: {e}")
conn.commit()
cur.close()
conn.close()
print("âœ… DB fixed")

