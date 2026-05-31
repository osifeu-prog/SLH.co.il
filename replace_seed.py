import re
with open("bot.py", "r", encoding="utf-8") as f:
    c = f.read()

# Find the seed function and replace it entirely
old_func = r"@dp\.message\(Command\(\"seed\"\)\).*?(?=\n@dp\.message|\n# ──|\n\n\Z)"
new_func = '''@dp.message(Command("seed"))
async def cmd_seed(msg: Message):
    if msg.from_user.id not in ADMIN_IDS: return await msg.answer("Admin only")
    try:
        uid = msg.from_user.id
        ensure_user(uid, msg.from_user.full_name or "admin")
        conn = get_db(); cur = conn.cursor()
        cur.execute("INSERT INTO tasks (user_id, description) VALUES (%s,%s), (%s,%s), (%s,%s)", (uid, "Demo task 1: Create NFT store", uid, "Demo task 2: Invite 3 friends", uid, "Demo task 3: Make first deposit"))
        cur.execute("INSERT INTO feedback (user_id, message) VALUES (%s,%s), (%s,%s)", (uid, "Great bot!", uid, "Need more features"))
        cur.execute("INSERT INTO payments (user_id, amount, status) VALUES (%s,%s,%s), (%s,%s,%s)", (uid, 9.9, "confirmed", uid, 29, "pending"))
        cur.execute("INSERT INTO events (user_id, event_type, payload) VALUES (%s,%s,%s), (%s,%s,%s)", (uid, "seed", "demo data inserted", uid, "checkin", "+5"))
        conn.commit(); cur.close(); conn.close()
        await msg.answer("✅ Demo data seeded! Check /tasks, /dashboard, /crm, /events, /feedback.", parse_mode=None)
    except Exception as e:
        await msg.answer(f"Seed error: {e}", parse_mode=None)
'''

c, n = re.subn(old_func, new_func, c, flags=re.DOTALL)
if n == 0:
    print("⚠️ Could not find seed function  adding at end of file")
    c += "\n\n" + new_func
else:
    print(f"✅ Seed function replaced ({n} occurrence(s))")

with open("bot.py", "w", encoding="utf-8") as f:
    f.write(c)
print("File updated.")
