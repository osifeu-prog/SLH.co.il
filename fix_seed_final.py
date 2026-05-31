import re

with open("bot.py", "r", encoding="utf-8") as f:
    content = f.read()

# Locate the entire seed function (from @dp.message to the next @dp.message or end)
pattern = r"(@dp\.message\(Command\(\"seed\"\)\)\s*async def cmd_seed\(msg: Message\):.*?)(?=\n@dp\.message|\Z)"
replacement = """@dp.message(Command("seed"))
async def cmd_seed(msg: Message):
    if msg.from_user.id not in ADMIN_IDS: return await msg.answer("Admin only")
    try:
        uid = msg.from_user.id
        # Create user directly (bypasses ensure_user issues)
        conn = get_db(); cur = conn.cursor()
        cur.execute(
            "INSERT INTO users (telegram_id, username, tier, referral_code) VALUES (%s, %s, 'business', %s) "
            "ON CONFLICT (telegram_id) DO UPDATE SET username = EXCLUDED.username",
            (uid, "admin", f"SLH{uid}")
        )
        conn.commit()

        cur.execute("INSERT INTO tasks (user_id, description) VALUES (%s,%s), (%s,%s), (%s,%s)",
                    (uid, "Demo task 1: Create NFT store", uid, "Demo task 2: Invite 3 friends", uid, "Demo task 3: Make first deposit"))
        cur.execute("INSERT INTO feedback (user_id, message) VALUES (%s,%s), (%s,%s)",
                    (uid, "Great bot!", uid, "Need more features"))
        cur.execute("INSERT INTO payments (user_id, amount, status) VALUES (%s,%s,%s), (%s,%s,%s)",
                    (uid, 9.9, "confirmed", uid, 29, "pending"))
        cur.execute("INSERT INTO events (user_id, event_type, payload) VALUES (%s,%s,%s), (%s,%s,%s)",
                    (uid, "seed", "demo data inserted", uid, "checkin", "+5"))
        conn.commit(); cur.close(); conn.close()
        await msg.answer("✅ Demo data seeded! Check /tasks, /dashboard, /crm, /events, /feedback.", parse_mode=None)
    except Exception as e:
        await msg.answer(f"Seed error: {e}", parse_mode=None)"""

new_content, count = re.subn(pattern, replacement, content, flags=re.DOTALL)

if count == 0:
    # Fallback: if the pattern was not found, insert at the end of the file (just in case)
    new_content = content + "\n\n" + replacement
    print("⚠️ Pattern not found – appended replacement at end of file.")
else:
    print(f"✅ Seed function replaced ({count} occurrence(s)).")

with open("bot.py", "w", encoding="utf-8") as f:
    f.write(new_content)