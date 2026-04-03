import psycopg2

conn = psycopg2.connect(
    dbname="postgres",
    user="postgres",
    password="admin",
    host="127.0.0.1",
    port=5432,
)

cur = conn.cursor()
cur.execute("update payment_requests set status='rejected' where user_id=%s and status='pending'", (224223270,))
print("rows updated:", cur.rowcount)
conn.commit()
cur.close()
conn.close()
print("done")
