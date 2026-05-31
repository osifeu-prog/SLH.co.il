import re
with open("bot.py", "r", encoding="utf-8") as f:
    c = f.read()

# חיפוש התבנית המדויקת של seed ללא ensure_user
old = '        uid = msg.from_user.id\n        cur.execute("INSERT INTO tasks'
if old in c:
    new = '        uid = msg.from_user.id\n        ensure_user(uid, "admin")\n        cur.execute("INSERT INTO tasks'
    c = c.replace(old, new)
    with open("bot.py", "w", encoding="utf-8") as f:
        f.write(c)
    print("✅ Seed fix applied")
else:
    print("⚠️ Pattern not found  maybe already fixed or changed")
