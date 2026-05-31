import psycopg2, os
from dotenv import load_dotenv
load_dotenv()
conn = psycopg2.connect(os.getenv("DATABASE_URL"))
cur = conn.cursor()
cur.execute("""
    INSERT INTO users (telegram_id, username, tier, referral_code)
    VALUES (224223270, 'admin', 'business', 'SLH224223270')
    ON CONFLICT (telegram_id) DO UPDATE SET username = 'admin', tier = 'business'
""")
conn.commit()
cur.close()
conn.close()
print("✅ User 224223270 created/updated in users table")
