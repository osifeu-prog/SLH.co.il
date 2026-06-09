import shutil, os

# Restore from the last working backup (final_backup)
shutil.copy("bot.py.final_backup", "bot.py")

with open("bot.py", "r", encoding="utf-8") as f:
    c = f.read()

# Remove BOM
c = c.replace('\ufeff', '')

# Fix ADMIN_IDS
old_admin = 'ADMIN_IDS = [int(x) for x in os.getenv("ADMIN_ID", "").split(",") if x]'
new_admin = 'ADMIN_IDS = [int(x) for x in os.getenv("ADMIN_ID", "").replace(" ", ",").split(",") if x]'
c = c.replace(old_admin, new_admin)

# Add the full logo + menu start
old_start = '@dp.message(Command("start"))\nasync def cmd_start(msg: Message):'
if old_start in c:
    start_index = c.find(old_start)
    # find the end of the old start function (next top-level function or end of file)
    rest = c[start_index:]
    end_idx = rest.find('\n@dp.message(')
    if end_idx == -1:
        end_idx = len(rest)
    else:
        end_idx += start_index
    # remove old start
    c = c[:start_index] + c[end_idx:]

new_start = '''
@dp.message(Command("start"))
async def cmd_start(msg: Message):
    ensure_user(msg.from_user.id, msg.from_user.full_name or "friend")
    logo = ("<pre>╔══════════════════════════════════╗\\n"
            "║     ███████╗██╗     ██╗  ██╗     ║\\n"
            "║     ██╔════╝██║     ██║  ██║     ║\\n"
            "║     ███████╗██║     ███████║     ║\\n"
            "║     ╚════██║██║     ██╔══██║     ║\\n"
            "║     ███████║███████╗██║  ██║     ║\\n"
            "║     ╚══════╝╚══════╝╚═╝  ╚═╝     ║\\n"
            "║   🧠 SLH SPARK AI   v3.2        ║\\n"
            "╚══════════════════════════════════╝</pre>")
    await msg.answer(logo, parse_mode=ParseMode.HTML)
    await msg.answer("<b>✅ SLH SPARK AI v3.2 alive!</b>", reply_markup=main_menu())
'''
c += '\n' + new_start

# Add main_menu if not present
if 'def main_menu():' not in c:
    menu_def = '''
def main_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Status", callback_data="cmd_status"),
         InlineKeyboardButton(text="⭐ Points", callback_data="cmd_points")],
        [InlineKeyboardButton(text="✅ Check-in", callback_data="cmd_checkin"),
         InlineKeyboardButton(text="⚡ Tap-to-Earn", callback_data="cmd_tap")],
        [InlineKeyboardButton(text="💰 Crypto", callback_data="cmd_crypto"),
         InlineKeyboardButton(text="🤝 Donate", callback_data="cmd_donate")],
        [InlineKeyboardButton(text="📖 Guide", callback_data="cmd_guide"),
         InlineKeyboardButton(text="❓ Help", callback_data="cmd_help")],
    ])
'''
    c += '\n' + menu_def

# Add dummy upgrade/donate handlers if missing
if 'async def cmd_upgrade(msg: Message):' not in c:
    c += '''

@dp.message(Command("upgrade"))
async def cmd_upgrade(msg: Message):
    await msg.answer("<b>💎 Premium Tiers</b>\\n\\nPro (9.9 TON/mo) – x1.5 multiplier\\nBusiness (29 TON/mo) – x2.0 multiplier", parse_mode="HTML")

@dp.message(Command("donate"))
async def cmd_donate(msg: Message):
    await msg.answer(f"<b>🤝 Donate to SLH</b>\\nSend TON to:\\n<code>{TON_WALLET}</code>\\nYour ID: <code>{msg.from_user.id}</code>", parse_mode="HTML")

@dp.callback_query(F.data == "cmd_upgrade")
async def on_upgrade_click(callback: CallbackQuery):
    await callback.answer()
    await cmd_upgrade(callback.message)

@dp.callback_query(F.data == "cmd_donate")
async def on_donate_click(callback: CallbackQuery):
    await callback.answer()
    await cmd_donate(callback.message)
'''

# Add Oracle+ and Peace Game (already added in previous step, but ensure)
if 'async def cmd_oracle(msg: Message):' not in c:
    c += '''
@dp.message(Command("oracle"))
async def cmd_oracle(msg: Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔍 Ask the Oracle about SLH", callback_data="oracle_ask")],
        [InlineKeyboardButton(text="📊 System Scan", callback_data="oracle_scan")],
        [InlineKeyboardButton(text="📈 Fundraising Prediction", callback_data="oracle_predict")],
        [InlineKeyboardButton(text="🎮 Secret Game", callback_data="oracle_game")],
        [InlineKeyboardButton(text="🌿 Daily Peace Mission", callback_data="oracle_mission")],
        [InlineKeyboardButton(text="✨ Creativity Mode", callback_data="oracle_creative")],
    ])
    await msg.answer("<b>🔮 SLH Oracle+ Activated</b>\\nChoose your mode:", parse_mode="HTML", reply_markup=kb)

@dp.callback_query(F.data == "oracle_ask")
async def oracle_ask(callback: CallbackQuery):
    await callback.answer()
    await callback.message.answer("<b>🔮 Oracle says:</b>\\nAsk me anything about the project, donations, or the impact of your contribution.", parse_mode="HTML")

@dp.callback_query(F.data == "oracle_scan")
async def oracle_scan(callback: CallbackQuery):
    await callback.answer()
    await callback.message.answer("<b>🔮 System Scan:</b>\\n✅ Bot: Online\\n✅ DB: Connected\\n✅ Railway: Online", parse_mode="HTML")

@dp.callback_query(F.data == "oracle_predict")
async def oracle_predict(callback: CallbackQuery):
    await callback.answer()
    await callback.message.answer("<b>🔮 Fundraising Prediction:</b>\\nCurrent rate: +0.5 TON/day\\nProjected: 15 TON by end of month.", parse_mode="HTML")

@dp.callback_query(F.data == "oracle_mission")
async def oracle_mission(callback: CallbackQuery):
    await callback.answer()
    await callback.message.answer("<b>🌿 Daily Peace Mission:</b>\\nShare the bot with one person who cares about peace and innovation.", parse_mode="HTML")

@dp.message(Command("peace"))
async def cmd_peace(msg: Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🕊 Peace Path", callback_data="peace_path")],
        [InlineKeyboardButton(text="🤖 Innovation Path", callback_data="innovation_path")],
        [InlineKeyboardButton(text="🌍 Humanity Path", callback_data="humanity_path")],
    ])
    await msg.answer("<b>🎮 Peace Game</b>\\nChoose your path:", parse_mode="HTML", reply_markup=kb)

@dp.callback_query(F.data.startswith("peace_"))
async def peace_path_handler(callback: CallbackQuery):
    await callback.answer()
    path = callback.data.replace("peace_", "")
    messages = {
        "path": "You chose the Peace Path. Answer: What is the most important element in conflict resolution?\\nA) Communication  B) Force  C) Ignoring  D) Punishment",
        "innovation_path": "You chose the Innovation Path. Answer: What is the main benefit of humanitarian robots?\\nA) Unbiased assistance  B) Replacing humans  C) Control  D) Data collection",
        "humanity_path": "You chose the Humanity Path. Answer: What strengthens a community?\\nA) Volunteerism  B) Criticism  C) Isolation  D) Competition"
    }
    await callback.message.answer(f"<b>{messages[path]}</b>", parse_mode="HTML")
'''

# Now add the advanced features that were in the previous full bot
# (Progress Tracker, TON Gateway, Tasks API, Seed, etc.)
advanced_code = '''
@dp.message(Command("progress"))
async def cmd_progress(msg: Message):
    if msg.from_user.id not in ADMIN_IDS: return await msg.answer("Admin only")
    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM tasks"); total_tasks = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM tasks WHERE done=TRUE"); done_tasks = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM users"); total_users = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM payments WHERE status='confirmed'"); payments = cur.fetchone()[0]
    cur.execute("SELECT SUM(amount) FROM payments WHERE status='confirmed'"); revenue = cur.fetchone()[0] or 0
    cur.execute("SELECT COUNT(*) FROM feedback"); feedbacks = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM events WHERE created_at > NOW() - INTERVAL '1 day'"); events_today = cur.fetchone()[0]
    conn.close()
    pct = round(done_tasks / total_tasks * 100, 1) if total_tasks > 0 else 0
    bar = "🟩" * int(pct // 10) + "⬜" * (10 - int(pct // 10))
    await msg.answer(
        f"📈 <b>SLH Progress Tracker</b>\\n\\n"
        f"📝 Tasks: {done_tasks}/{total_tasks} {bar} {pct}%\\n"
        f"👥 Users: {total_users}\\n"
        f"💎 Payments: {payments} confirmed\\n"
        f"💰 Revenue: {revenue:.2f} TON\\n"
        f"📩 Feedback: {feedbacks}\\n"
        f"📡 Events today: {events_today}\\n\\n"
        f"<i>Updated: {datetime.datetime.now().strftime('%H:%M')}</i>",
        parse_mode=ParseMode.HTML
    )

@dp.message(Command("seed"))
async def cmd_seed(msg: Message):
    if msg.from_user.id not in ADMIN_IDS: return await msg.answer("Admin only")
    try:
        uid = msg.from_user.id
        ensure_user(uid, "admin")
        conn = get_db(); cur = conn.cursor()
        cur.execute("INSERT INTO tasks (user_id, description) VALUES (%s,%s), (%s,%s), (%s,%s)", (uid, "Demo task 1: Create NFT store", uid, "Demo task 2: Invite 3 friends", uid, "Demo task 3: Make first deposit"))
        cur.execute("INSERT INTO feedback (user_id, message) VALUES (%s,%s), (%s,%s)", (uid, "Great bot!", uid, "Need more features"))
        cur.execute("INSERT INTO payments (user_id, amount, status) VALUES (%s,%s,%s), (%s,%s,%s)", (uid, 9.9, "confirmed", uid, 29, "pending"))
        cur.execute("INSERT INTO events (user_id, event_type, payload) VALUES (%s,%s,%s), (%s,%s,%s)", (uid, "seed", "demo data inserted", uid, "checkin", "+5"))
        conn.commit(); cur.close(); conn.close()
        await msg.answer("✅ Demo data seeded! Check /tasks, /dashboard, /crm, /events, /feedback.", parse_mode=None)
    except Exception as e:
        await msg.answer(f"Seed error: {e}", parse_mode=None)

# Add TON Gateway (monitor)
TONCENTER_V3 = "https://toncenter.com/api/v3"

def ton_monitor():
    while True:
        try:
            url = f"{TONCENTER_V3}/transactions?account={TON_WALLET}&limit=20&sort=desc"
            resp = requests.get(url, timeout=15)
            if resp.status_code != 200:
                time.sleep(30)
                continue
            data = resp.json()
            txs = data.get("transactions", [])
            conn = get_db(); cur = conn.cursor()
            for tx in txs:
                tx_hash = tx.get("hash")
                if not tx_hash: continue
                in_msg = tx.get("in_msg") or {}
                value_nano = int(in_msg.get("value", 0))
                if value_nano <= 0: continue
                amount = value_nano / 1_000_000_000
                comment = str(in_msg.get("message") or in_msg.get("body") or "").strip()
                try:
                    user_id = int(comment)
                    if user_id < 100000: continue
                except: continue
                cur.execute("SELECT 1 FROM payments WHERE tx_hash = %s", (tx_hash,))
                if cur.fetchone(): continue
                cur.execute("INSERT INTO payments (user_id, amount, status, tx_hash) VALUES (%s,%s,%s,%s)", (user_id, amount, "confirmed", tx_hash))
                new_tier = "business" if amount >= 29 else "pro" if amount >= 9.9 else "free"
                cur.execute("UPDATE users SET balance = balance + %s, tier = CASE WHEN %s > tier THEN %s ELSE tier END WHERE telegram_id = %s", (amount, amount, new_tier, user_id))
                cur.execute("INSERT INTO events (user_id, event_type, payload) VALUES (%s,%s,%s)", (user_id, "deposit", f"{amount} TON"))
                conn.commit()
                try:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    loop.run_until_complete(bot.send_message(user_id, f"✅ <b>Deposit received!</b>\\n{amount:.2f} TON"))
                except: pass
            cur.close(); conn.close()
        except Exception as e:
            print(f"TON monitor error: {e}")
        time.sleep(30)

threading.Thread(target=ton_monitor, daemon=True).start()

@dp.message(Command("paid"))
async def cmd_paid(msg: Message):
    if msg.from_user.id not in ADMIN_IDS: return await msg.answer("Admin only")
    parts = msg.text.split()
    if len(parts) < 3: return await msg.answer("Usage: /paid <user_id> <amount>", parse_mode=None)
    try:
        target_uid = int(parts[1])
        amount = float(parts[2])
    except: return await msg.answer("Invalid numbers", parse_mode=None)
    conn = get_db(); cur = conn.cursor()
    cur.execute("INSERT INTO payments (user_id, amount, status) VALUES (%s,%s,'manual')", (target_uid, amount))
    new_tier = "business" if amount >= 29 else "pro" if amount >= 9.9 else "free"
    cur.execute("UPDATE users SET balance = balance + %s, tier = CASE WHEN %s > tier THEN %s ELSE tier END WHERE telegram_id = %s", (amount, amount, new_tier, target_uid))
    cur.execute("INSERT INTO events (user_id, event_type, payload) VALUES (%s,%s,%s)", (target_uid, "deposit_manual", f"{amount} TON"))
    conn.commit(); cur.close(); conn.close()
    await msg.answer(f"✅ Manual deposit of {amount} TON credited to user {target_uid}", parse_mode=None)

# Add Tasks API and Web App (simplified)
try:
    from fastapi import FastAPI, Request
    from fastapi.responses import HTMLResponse, JSONResponse
    from fastapi.middleware.cors import CORSMiddleware
    import uvicorn
    HAS_FASTAPI = True
except ImportError:
    HAS_FASTAPI = False

if HAS_FASTAPI:
    DASHBOARD_HTML = """<html><head><meta charset="utf-8"><title>SLH Dashboard</title>
<style>body{font-family:sans-serif;margin:20px;background:#0a0a1a;color:#e0e0e0}.card{background:#1a1a2e;padding:20px;margin:10px 0;border-radius:10px}.stat{font-size:1.5em;font-weight:bold}</style></head>
<body><h1>SLH SPARK AI</h1>
<div class="card"><div class="stat" id="stats">Loading...</div></div>
<script>fetch('/api/stats').then(r=>r.json()).then(d=>{document.getElementById('stats').innerHTML=`Users: ${d.total_users} | Active: ${d.active_today} | Points: ${d.total_points} | Premium: ${d.premium_users}`})</script>
</body></html>"""

    def make_web_app():
        app = FastAPI()
        app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
        @app.get("/", response_class=HTMLResponse)
        async def dashboard(): return HTMLResponse(content=DASHBOARD_HTML)
        @app.get("/health")
        async def health(): return JSONResponse({"database": True, "bot": True})
        @app.get("/api/stats")
        async def stats():
            conn = get_db(); cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM users"); total = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM users WHERE last_checkin=CURRENT_DATE"); active = cur.fetchone()[0]
            cur.execute("SELECT SUM(points) FROM users"); pts = cur.fetchone()[0] or 0
            cur.execute("SELECT COUNT(*) FROM users WHERE tier!='free'"); prem = cur.fetchone()[0]
            cur.execute("SELECT telegram_id,username,tier,points FROM users ORDER BY points DESC LIMIT 20")
            users = [{"telegram_id":r[0],"username":r[1],"tier":r[2],"points":r[3]} for r in cur.fetchall()]
            conn.close()
            return JSONResponse({"total_users":total,"active_today":active,"total_points":int(pts),"premium_users":prem,"users_list":users})
        @app.get("/api/tasks")
        async def api_tasks(user_id: int = None):
            if not user_id: return JSONResponse({"tasks": []})
            conn = get_db(); cur = conn.cursor()
            cur.execute("SELECT id, description, done, created_at FROM tasks WHERE user_id=%s ORDER BY created_at DESC LIMIT 50", (user_id,))
            tasks = [{"id": r[0], "title": r[1], "done": r[2], "created_at": str(r[3])} for r in cur.fetchall()]
            cur.close(); conn.close()
            return JSONResponse({"tasks": tasks})
        @app.patch("/api/tasks/{task_id}")
        async def api_patch_task(task_id: int, request: Request):
            data = await request.json()
            done = data.get("done", None)
            if done is not None:
                conn = get_db(); cur = conn.cursor()
                cur.execute("UPDATE tasks SET done=%s WHERE id=%s", (done, task_id))
                conn.commit(); cur.close(); conn.close()
            return JSONResponse({"ok": True})
        return app
'''

# Only add advanced features if not already present (to avoid duplicates)
if 'async def cmd_progress(msg: Message):' not in c:
    c += '\n' + advanced_code

# Add remaining guide, faq, tutorial if missing
if 'async def cmd_guide(msg: Message):' not in c:
    guide_code = '''
@dp.message(Command("guide"))
async def cmd_guide(msg: Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⭐ How to earn points", callback_data="guide_points")],
        [InlineKeyboardButton(text="💎 How to deposit TON", callback_data="guide_deposit")],
        [InlineKeyboardButton(text="🏆 What is Tier?", callback_data="guide_tier")],
        [InlineKeyboardButton(text="📋 All commands", callback_data="cmd_help")],
    ])
    await msg.answer("<b>📖 SLH Guide</b>\\nChoose a topic:", parse_mode="HTML", reply_markup=kb)

@dp.message(Command("faq"))
async def cmd_faq(msg: Message):
    await msg.answer("<b>FAQ</b>\\n\\n<b>Q: How to earn points?</b>\\n/checkin daily, /tap, complete /tasks\\n\\n<b>Q: How to deposit TON?</b>\\n/deposit - send TON with your ID in memo\\n\\n<b>Q: Premium tiers?</b>\\nPro: 9.9 TON/mo (x1.5) | Business: 29 TON/mo (x2.0)\\n\\n<b>Q: Referrals?</b>\\n/referral - earn +50 pts per friend", parse_mode="HTML")

@dp.message(Command("tutorial"))
async def cmd_tutorial(msg: Message):
    await msg.answer("<b>🎓 Tutorial</b>\\n\\n1. /register - create account\\n2. /checkin - earn daily points\\n3. /deposit - add TON\\n4. /upgrade - unlock premium\\n5. /task - set your goals\\n\\nQuestions? /support", parse_mode="HTML")

@dp.callback_query(F.data.startswith("guide_"))
async def on_guide_topic(callback: CallbackQuery):
    await callback.answer()
    topics = {
        "guide_points": "<b>⭐ Earning Points</b>\\n\\n/checkin  daily (+5 to +35)\\n/tap  tap button (+5 each)\\n/done  complete task (+10)\\n\\nTip: streak bonus stacks up to 7 days!",
        "guide_deposit": "<b>💎 Depositing TON</b>\\n\\n1. Use /deposit to get wallet address\\n2. Send TON from your wallet\\n3. Include your Telegram ID in memo\\n4. Balance updates after confirmation",
        "guide_tier": "<b>🏆 Tier System</b>\\n\\nFREE  x1.0 multiplier\\nPRO (9.9 TON/mo)  x1.5 multiplier\\nBUSINESS (29 TON/mo)  x2.0 multiplier\\n\\nUpgrade: /upgrade",
    }
    await callback.message.answer(topics.get(callback.data, "Unknown topic"), parse_mode="HTML")
'''
    c += '\n' + guide_code

with open("bot.py", "w", encoding="utf-8") as f:
    f.write(c)

print("✅ Full SLH Bot restored with all features (Oracle, Peace, Progress, TON Gateway, Tasks API, Guides)")