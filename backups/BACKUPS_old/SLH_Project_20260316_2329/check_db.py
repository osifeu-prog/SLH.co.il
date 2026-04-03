import psycopg2

conn = psycopg2.connect(
    dbname="postgres",
    user="postgres",
    password="admin",
    host="127.0.0.1",
    port=5432,
)

cur = conn.cursor()
cur.execute("select user_id, username, paid, created_at from users order by created_at desc")
print(cur.fetchall())

cur.execute("select id, user_id, status, note, created_at from payment_requests order by id desc")
print(cur.fetchall())

cur.close()
conn.close()
