import psycopg2, os
from dotenv import load_dotenv
load_dotenv()

conn = psycopg2.connect(os.getenv("DATABASE_URL"))
cur = conn.cursor()

statements = [
    "ALTER TABLE users ADD COLUMN IF NOT EXISTS points INTEGER DEFAULT 0",
    "ALTER TABLE users ADD COLUMN IF NOT EXISTS streak INTEGER DEFAULT 0",
    "ALTER TABLE users ADD COLUMN IF NOT EXISTS last_checkin DATE",
    "ALTER TABLE users ADD COLUMN IF NOT EXISTS tier TEXT DEFAULT 'free'",
    "ALTER TABLE users ADD COLUMN IF NOT EXISTS balance NUMERIC DEFAULT 0",
]

for stmt in statements:
    cur.execute(stmt)
    print(f"✅ Executed: {stmt}")

conn.commit()
cur.close()
conn.close()
print("All columns added successfully!")
