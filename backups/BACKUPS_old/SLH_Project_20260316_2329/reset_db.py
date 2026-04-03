import psycopg2
import os
from dotenv import load_dotenv
load_dotenv(".env")
def reset():
    conn = psycopg2.connect(dbname='postgres', user='postgres', password='admin', host='127.0.0.1', port=5432)
    cur = conn.cursor()
    cur.execute('DROP TABLE IF EXISTS payment_requests; DROP TABLE IF EXISTS users;')
    cur.execute('CREATE TABLE users (user_id BIGINT PRIMARY KEY, username TEXT, paid BOOLEAN NOT NULL DEFAULT FALSE, created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP);')
    cur.execute('CREATE TABLE payment_requests (id SERIAL PRIMARY KEY, user_id BIGINT NOT NULL, status TEXT NOT NULL DEFAULT \"pending\", note TEXT, created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP);')
    conn.commit(); cur.close(); conn.close()
    print('Database initialized successfully.')
if __name__ == '__main__': reset()
