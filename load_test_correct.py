import os, sys, random, psycopg2
from dotenv import load_dotenv
load_dotenv()
db_url = os.getenv("DATABASE_URL")
if not db_url:
    print("DATABASE_URL missing")
    sys.exit(1)
conn = psycopg2.connect(db_url)
cur = conn.cursor()
print("?? Creating 100 test users...")
test_users = []
for i in range(1, 101):
    tid = 1000000 + i
    name = f"TestUser{i}"
    cur.execute("""
        INSERT INTO users (telegram_id, username, tier, points, streak, referral_count)
        VALUES (%s, %s, 'free', 0, 0, 0)
        ON CONFLICT (telegram_id) DO UPDATE SET
            username = EXCLUDED.username,
            points = 0,
            streak = 0,
            referral_count = 0,
            last_checkin = NULL
    """, (tid, name))
    test_users.append(tid)
conn.commit()
print(f"? {len(test_users)} test users ready")
print("?? Simulating check-ins...")
for uid in test_users:
    streak = random.randint(0, 7)
    bonus = min(streak+1, 7) * 5
    cur.execute("UPDATE users SET points = points + %s, streak = %s, last_checkin = CURRENT_DATE WHERE telegram_id = %s", (bonus, streak+1, uid))
conn.commit()
print("? Check-ins done")
cur.execute("SELECT SUM(points) FROM users")
total_points = cur.fetchone()[0] or 0
print(f"?? Total points after simulation: {total_points}")
conn.close()
print("Load test completed successfully.")
