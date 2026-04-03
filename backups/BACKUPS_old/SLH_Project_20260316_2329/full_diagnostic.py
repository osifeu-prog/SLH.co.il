import os
import psycopg2
from dotenv import load_dotenv

load_dotenv(".env")
print("--- DB CONFIG ---")
print(f"DB_NAME: {os.getenv('DB_NAME')}")
print(f"DB_HOST: {os.getenv('DB_HOST')}")

try:
    conn = psycopg2.connect(
        dbname=os.getenv("DB_NAME"), 
        user=os.getenv("DB_USER"), 
        password=os.getenv("DB_PASS"), 
        host=os.getenv("DB_HOST"), 
        port=int(os.getenv("DB_PORT", 5432))
    )
    cur = conn.cursor()
    print("\n--- ATTEMPTING WRITE ---")
    cur.execute("INSERT INTO admin_audit_logs (event_type, success, reason) VALUES ('DIAG_TEST', True, 'Diagnostic test')")
    conn.commit()
    print("SUCCESS: Write worked")
    cur.close()
    conn.close()
except Exception as e:
    print(f"FAILURE: {e}")
