import re, sys
with open("bot.py", "r", encoding="utf-8") as f:
    c = f.read()
patches = []

# 1. תיקון init_db: הוספת last_seen
if "last_seen TIMESTAMP" not in c:
    old = "ALTER TABLE users ADD COLUMN IF NOT EXISTS referred_by BIGINT;"
    if old in c:
        c = c.replace(old, old + "\n                ALTER TABLE users ADD COLUMN IF NOT EXISTS last_seen TIMESTAMP DEFAULT NOW();")
        patches.append("last_seen column added to init_db")
else:
    patches.append("last_seen already exists - skipping")

# 2. תיקון seed: ensure_user לפני INSERT
if 'ensure_user(uid, "admin")' not in c:
    # נסה למצוא את התבנית המדויקת של seed
    old_seed = '        uid = msg.from_user.id\n        cur.execute("INSERT INTO tasks'
    if old_seed in c:
        c = c.replace(old_seed, '        uid = msg.from_user.id\n        ensure_user(uid, "admin")\n        cur.execute("INSERT INTO tasks')
        patches.append("ensure_user added to seed")
    else:
        # התבנית שונתה? נחפש את uid = msg.from_user.id בתוך seed
        # נשתמש ב-regex להחלפה
        pattern = r'(async def cmd_seed.*?try:.*?\n        )uid = msg\.from_user\.id\n        '
        if re.search(pattern, c, re.DOTALL):
            c = re.sub(pattern, r'\1uid = msg.from_user.id\n        ensure_user(uid, "admin")\n        ', c, count=1, flags=re.DOTALL)
            patches.append("ensure_user added to seed (regex)")
        else:
            patches.append("WARNING: Could not find seed pattern - manual fix needed")
else:
    patches.append("ensure_user already in seed - skipping")

# שמירה רק אם בוצעו שינויים
if "added" in " ".join(patches):
    with open("bot.py", "w", encoding="utf-8") as f:
        f.write(c)
    print("✅ שינויים נשמרו:", ", ".join(patches))
else:
    print("✅ אין צורך בשינויים:", ", ".join(patches))
