import psycopg2, os
conn = psycopg2.connect(os.environ["DATABASE_URL"])
cur = conn.cursor()
cur.execute("INSERT INTO users (telegram_id, username, tier, referral_code) VALUES (224223270, 'admin', 'business', 'SLH224223270') ON CONFLICT (telegram_id) DO UPDATE SET username = 'admin'")
conn.commit()
cur.close()
conn.close()
print("User 224223270 created/updated")
