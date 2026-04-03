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

cur.execute("""
INSERT INTO admin_audit_logs (
    event_type,
    actor_user_id,
    actor_username,
    target_user_id,
    target_username,
    entity_type,
    entity_id,
    success,
    reason,
    error_text,
    old_state,
    new_state,
    metadata
)
VALUES (
    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s::jsonb, %s::jsonb
)
""", (
    "manual.audit.test",
    224223270,
    "osifeu_prog",
    224223270,
    "osifeu_prog",
    "system",
    "manual-test",
    True,
    "manual insert validation",
    None,
    "{}",
    '{"status":"ok"}',
    '{"source":"powershell"}'
))

conn.commit()
print("MANUAL AUDIT INSERTED OK")

cur.close()
conn.close()