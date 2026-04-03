import os
import psycopg2

SQL_PATH = "tools/enable_airdrop.sql"

def main():
    url = os.environ["DATABASE_URL"]
    with open(SQL_PATH, "r", encoding="utf-8") as f:
        sql = f.read()

    conn = psycopg2.connect(url)
    try:
        cur = conn.cursor()
        cur.execute(sql)
        # אם ה-SQL מחזיר SELECT בסוף, יש תוצאה
        rows = cur.fetchall() if cur.description else []
        conn.commit()
        print(rows)
        cur.close()
    finally:
        conn.close()

if __name__ == "__main__":
    main()
