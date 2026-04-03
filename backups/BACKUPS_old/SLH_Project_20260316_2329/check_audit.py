import os
import psycopg2
from dotenv import load_dotenv

load_dotenv(".env", override=True)

conn = psycopg2.connect(
    dbname=os.getenv("DB_NAME", "postgres"),
    user=os.getenv("DB_USER", "postgres"),
    password=os.getenv("DB_PASS", "admin"),
    host=os.getenv("DB_HOST", "127.0.0.1"),
    port=int(os.getenv("DB_PORT", "5432")),
)
cur = conn.cursor()

cur.execute("SELECT COUNT(*) FROM admin_audit_logs")
print("ROW_COUNT_BEFORE_START =", cur.fetchone()[0])

cur.execute("""
SELECT id, created_at, event_type, actor_user_id, target_user_id, entity_type, entity_id, success, reason
FROM admin_audit_logs
ORDER BY id DESC
LIMIT 10
""")
for row in cur.fetchall():
    print(row)

cur.close()
conn.close()