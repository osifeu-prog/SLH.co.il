import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
try:
    conn = psycopg2.connect(dbname='postgres', user='postgres', password='??????_??_???????', host='127.0.0.1')
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cursor = conn.cursor()
    cursor.execute('CREATE USER slh_user WITH PASSWORD %s;', ('slh_password',))
    cursor.execute('CREATE DATABASE slh_database OWNER slh_user;')
    cursor.execute('GRANT ALL PRIVILEGES ON DATABASE slh_database TO slh_user;')
    print('\x1b[32m[+] User and Database created successfully!\x1b[0m')
    cursor.close()
    conn.close()
except Exception as e:
    print(f'\x1b[31m[!] Error: {e}\x1b[0m')
