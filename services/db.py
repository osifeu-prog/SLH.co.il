import os
import psycopg2

def get_db():
    return psycopg2.connect(os.getenv("DATABASE_URL"))

def init_db():
    conn = get_db()
    cur = conn.cursor()
    with open("sql/schema.sql", "r") as f:
        cur.execute(f.read())
    conn.commit()
    conn.close()
