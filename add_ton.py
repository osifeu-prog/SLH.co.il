# add_ton.py – מוסיף TON Payment Gateway + מתקן seed
import re

with open("bot.py", "r", encoding="utf-8") as f:
    content = f.read()

# --- תיקון seed: ודא ensure_user לפני insert ---
old_seed = """    try:
        conn = get_db(); cur = conn.cursor()
        uid = msg.from_user.id
        cur.execute("INSERT INTO tasks"""
if old_seed in content:
    new_seed = """    try:
        conn = get_db(); cur = conn.cursor()
        uid = msg.from_user.id
        ensure_user(uid, "admin")
        cur.execute("INSERT INTO tasks"""
    content = content.replace(old_seed, new_seed)
    print("✓ Seed fixed (ensure_user added)")

# --- הוספת TON Gateway ---
if "# ═══ TON GATEWAY ═══" not in content:
    ton_code = '''
# ═══ TON GATEWAY ═══
import json as json_module
TONCENTER_V3 = "https://toncenter.com/api/v3"

def ton_monitor():
    """Background thread: checks for incoming TON transactions every 30 seconds."""
    while True:
        try:
            # 1. Get recent transactions
            url = f"{TONCENTER_V3}/transactions?account={TON_WALLET}&limit=20&sort=desc"
            resp = requests.get(url, timeout=15)
            if resp.status_code != 200:
                time.sleep(30)
                continue
            data = resp.json()
            txs = data.get("transactions", [])
            conn = get_db()
            cur = conn.cursor()
            for tx in txs:
                tx_hash = tx.get("hash")
                if not tx_hash:
                    continue
                # Only incoming messages with value > 0
                in_msg = tx.get("in_msg") or {}
                value_nano = int(in_msg.get("value", 0))
                if value_nano <= 0:
                    continue
                amount = value_nano / 1_000_000_000  # nanoTON -> TON
                # Extract comment (user ID)
                comment = str(in_msg.get("message") or in_msg.get("body") or "").strip()
                try:
                    user_id = int(comment)
                    if user_id < 100000:
                        continue
                except:
                    continue
                # Avoid duplicate
                cur.execute("SELECT 1 FROM payments WHERE tx_hash = %s", (tx_hash,))
                if cur.fetchone():
                    continue
                # Record payment
                cur.execute(
                    "INSERT INTO payments (user_id, amount, status, tx_hash) VALUES (%s,%s,%s,%s)",
                    (user_id, amount, "confirmed", tx_hash)
                )
                # Update user balance and tier
                new_tier = "business" if amount >= 29 else "pro" if amount >= 9.9 else "free"
                cur.execute(
                    """UPDATE users SET balance = balance + %s,
                       tier = CASE WHEN %s > tier THEN %s ELSE tier END
                       WHERE telegram_id = %s""",
                    (amount, amount, new_tier, user_id)
                )
                # Insert event
                cur.execute(
                    "INSERT INTO events (user_id, event_type, payload) VALUES (%s,%s,%s)",
                    (user_id, "deposit", f"{amount} TON")
                )
                conn.commit()
                # Notify user
                try:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    loop.run_until_complete(
                        bot.send_message(
                            user_id,
                            f"✅ <b>Deposit received!</b>\n{amount:.2f} TON credited to your balance."
                        )
                    )
                except:
                    pass
            cur.close()
            conn.close()
        except Exception as e:
            print(f"TON monitor error: {e}")
        time.sleep(30)

# Start monitor thread (must be called after dp/bot are ready)
threading.Thread(target=ton_monitor, daemon=True).start()

# Manual payment confirmation (admin backup)
@dp.message(Command("paid"))
async def cmd_paid(msg: Message):
    if msg.from_user.id not in ADMIN_IDS:
        return await msg.answer("Admin only")
    parts = msg.text.split()
    if len(parts) < 3:
        return await msg.answer("Usage: /paid <user_id> <amount>", parse_mode=None)
    try:
        target_uid = int(parts[1])
        amount = float(parts[2])
    except:
        return await msg.answer("Invalid numbers", parse_mode=None)
    conn = get_db(); cur = conn.cursor()
    cur.execute(
        "INSERT INTO payments (user_id, amount, status) VALUES (%s,%s,'manual')",
        (target_uid, amount)
    )
    new_tier = "business" if amount >= 29 else "pro" if amount >= 9.9 else "free"
    cur.execute(
        "UPDATE users SET balance = balance + %s, tier = CASE WHEN %s > tier THEN %s ELSE tier END WHERE telegram_id = %s",
        (amount, amount, new_tier, target_uid)
    )
    cur.execute(
        "INSERT INTO events (user_id, event_type, payload) VALUES (%s,%s,%s)",
        (target_uid, "deposit_manual", f"{amount} TON")
    )
    conn.commit(); cur.close(); conn.close()
    await msg.answer(f"✅ Manual deposit of {amount} TON credited to user {target_uid}", parse_mode=None)
    try:
        await bot.send_message(target_uid, f"✅ <b>Manual deposit received:</b> {amount:.2f} TON")
    except:
        pass
'''
    content = content.replace("# ── AI CHAT ──", ton_code + "\n# ── AI CHAT ──")
    print("✓ TON Gateway added")

with open("bot.py", "w", encoding="utf-8", newline="\n") as f:
    f.write(content)

print("✅ All done. Ready to deploy.")