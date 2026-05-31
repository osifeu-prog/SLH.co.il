with open('bot.py', 'r', encoding='utf-8') as f:
    c = f.read()

# Remove duplicate last_seen line
c = c.replace('ALTER TABLE users ADD COLUMN IF NOT EXISTS last_seen TIMESTAMP DEFAULT NOW();\n                ALTER TABLE users ADD COLUMN IF NOT EXISTS last_seen TIMESTAMP DEFAULT NOW();',
              'ALTER TABLE users ADD COLUMN IF NOT EXISTS last_seen TIMESTAMP DEFAULT NOW();')

# Add /fix_db command before progress
fix_db_cmd = '''
# ═══════════ FIX DB ═══════════
@dp.message(Command("fix_db"))
async def cmd_fix_db(msg: Message):
    if msg.from_user.id not in ADMIN_IDS: return await msg.answer("Admin only")
    try:
        conn = get_db(); cur = conn.cursor()
        cur.execute("INSERT INTO users (telegram_id, username, tier, referral_code) VALUES (224223270, 'admin', 'business', 'SLH224223270') ON CONFLICT (telegram_id) DO UPDATE SET username = 'admin'")
        cur.execute("ALTER TABLE events DROP CONSTRAINT IF EXISTS events_user_id_fkey")
        conn.commit(); cur.close(); conn.close()
        await msg.answer("✅ User 224223270 created, FK constraint removed")
    except Exception as e:
        await msg.answer(f"Fix DB error: {e}")
'''

insert_marker = "@dp.message(Command(\"progress\"))"
if insert_marker in c:
    c = c.replace(insert_marker, fix_db_cmd + "\n" + insert_marker)
else:
    c += "\n" + fix_db_cmd

with open('bot.py', 'w', encoding='utf-8') as f:
    f.write(c)
print("✅ bot.py updated")
