import re

with open("bot.py", "r", encoding="utf-8") as f:
    c = f.read()

# Fix any backslash-escaped quotes like \"admin\"
c = c.replace('\"', '"')

# Add last_seen column if missing
if 'last_seen TIMESTAMP' not in c:
    c = c.replace(
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS referred_by BIGINT;",
        'ALTER TABLE users ADD COLUMN IF NOT EXISTS referred_by BIGINT;\n                ALTER TABLE users ADD COLUMN IF NOT EXISTS last_seen TIMESTAMP DEFAULT NOW();'
    )

# Add ensure_user in seed function if missing
if 'ensure_user(uid, "admin")' not in c:
    old = '        uid = msg.from_user.id\n        cur.execute("INSERT INTO tasks'
    if old in c:
        c = c.replace(old, '        uid = msg.from_user.id\n        ensure_user(uid, "admin")\n        cur.execute("INSERT INTO tasks')
    else:
        pass

with open("bot.py", "w", encoding="utf-8") as f:
    f.write(c)

print("Fixed")

