import asyncio, os, time, json, datetime, aiohttp, requests
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from ux.responses import *
from ux.keyboards import *
from services.db import init_db, get_db
from services.wallet import get_balance, transfer
from services.ledger import log_transaction
from services.event import emit_event
from services.store import create_store, get_store
from services.product import add_product, list_products
from services.order import create_order

load_dotenv()
init_db()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN") or os.getenv("BOT_TOKEN")
bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

# ---- Helper ----
def load_db(file):
    if not os.path.exists(file):
        with open(file, "w", encoding="utf-8") as f: json.dump({}, f)
    with open(file, "r", encoding="utf-8") as f: return json.load(f)
def save_db(data, file):
    with open(file, "w", encoding="utf-8") as f: json.dump(data, f, indent=2, ensure_ascii=False)

CONTACTS_FILE, POINTS_FILE = "contacts.json", "points.json"
admin_str = os.getenv("ADMIN_ID", "0")
ADMIN_IDS = [int(x.strip()) for x in admin_str.replace(",", " ").split() if x.strip().isdigit()]

# ========================== BASIC COMMANDS ==========================
@dp.message(Command("start"))
async def cmd_start(msg: Message):
    name = msg.from_user.first_name or msg.from_user.username or "friend"
    kb = kb_main_menu()
    buttons = [[InlineKeyboardButton(**btn) for btn in row] for row in kb]
    markup = InlineKeyboardMarkup(inline_keyboard=buttons)
    await msg.answer(msg_welcome(name), parse_mode=ParseMode.MARKDOWN_V2, reply_markup=markup)

@dp.message(Command("register"))
async def cmd_register(msg: Message):
    uid = msg.from_user.id
    uname = msg.from_user.full_name or msg.from_user.username or "unknown"
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("INSERT INTO users (telegram_id, username, tier) VALUES (%s,%s,'free') ON CONFLICT (telegram_id) DO UPDATE SET username=%s, last_seen=NOW()", (uid, uname, uname))
        conn.commit()
        await msg.answer(msg_register_success(uname), parse_mode=ParseMode.MARKDOWN_V2)
    except Exception as e:
        await msg.answer(f"Registration error: {e}")
    finally:
        conn.close()

@dp.message(Command("donate"))
async def cmd_donate(msg: Message):
    await msg.answer(msg_donate(), parse_mode=ParseMode.MARKDOWN_V2, reply_markup=kb_donate())

@dp.message(Command("checkin"))
async def cmd_checkin(msg: Message):
    uid = msg.from_user.id
    name = msg.from_user.full_name or msg.from_user.username or "user"
    conn = get_db()
    cur = conn.cursor()
    cur.execute("INSERT INTO users (telegram_id, username) VALUES (%s,%s) ON CONFLICT (telegram_id) DO NOTHING", (uid, name))
    cur.execute("SELECT points, streak, last_checkin FROM users WHERE telegram_id=%s", (uid,))
    row = cur.fetchone()
    today = datetime.date.today()
    if row and row[2] == today:
        await msg.answer(msg_checkin_already(), parse_mode=ParseMode.MARKDOWN_V2)
        conn.close()
        return
    points = row[0] if row else 0
    streak = (row[1] + 1) if row else 1
    bonus = min(streak, 7) * 5
    new_points = points + bonus
    cur.execute("UPDATE users SET points=%s, streak=%s, last_checkin=%s WHERE telegram_id=%s", (new_points, streak, today, uid))
    conn.commit()
    conn.close()
    await msg.answer(msg_checkin_success(name, bonus, new_points, streak), parse_mode=ParseMode.MARKDOWN_V2, reply_markup=kb_after_checkin())

@dp.message(Command("points"))
async def cmd_points(msg: Message):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT points, streak FROM users WHERE telegram_id=%s", (msg.from_user.id,))
    row = cur.fetchone()
    conn.close()
    if row:
        await msg.answer(msg_points(msg.from_user.full_name, row[0], "free"), parse_mode=ParseMode.MARKDOWN_V2, reply_markup=kb_after_points())
    else:
        await msg.answer("לא רשום. השתמש ב-/register")

@dp.message(Command("leaderboard"))
async def cmd_leaderboard(msg: Message):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT username, points FROM users ORDER BY points DESC LIMIT 5")
    rows = cur.fetchall()
    conn.close()
    if not rows:
        await msg.answer("אין נתונים")
        return
    entries = [{"username": r[0], "points": r[1]} for r in rows]
    await msg.answer(msg_leaderboard(entries), parse_mode=ParseMode.MARKDOWN_V2, reply_markup=kb_leaderboard())

@dp.message(Command("status"))
async def cmd_status(msg: Message):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM users")
    total = cur.fetchone()[0]
    cur.execute("SELECT COALESCE(SUM(amount),0) FROM ledger_transactions WHERE category='donation' AND type='credit'")
    raised = cur.fetchone()[0]
    conn.close()
    await msg.answer(msg_status(raised, 50000, total, 30), parse_mode=ParseMode.MARKDOWN_V2, reply_markup=kb_status())

@dp.message(Command("users"))
async def cmd_users(msg: Message):
    if msg.from_user.id not in ADMIN_IDS: return await msg.answer(msg_error_admin_only())
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT telegram_id, username, created_at FROM users ORDER BY created_at DESC LIMIT 30")
    rows = cur.fetchall()
    conn.close()
    if not rows: return await msg.answer("אין משתמשים")
    text = "👥 משתמשים:\n" + "\n".join(f"- {r[1]} (@{r[0]}) - {r[2][:10]}" for r in rows)
    await msg.answer(text)

@dp.message(Command("broadcast"))
async def cmd_broadcast(msg: Message):
    if msg.from_user.id not in ADMIN_IDS: return await msg.answer(msg_error_admin_only())
    parts = msg.text.split(" ", 1)
    if len(parts) < 2: return await msg.answer("שימוש: /broadcast <הודעה>")
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT telegram_id FROM users")
    users = cur.fetchall()
    conn.close()
    sent = 0
    for (uid,) in users:
        try:
            await bot.send_message(uid, parts[1])
            sent += 1
        except: pass
    await msg.answer(f"📢 נשלח ל-{sent}/{len(users)} משתמשים.")

@dp.message(Command("morning"))
async def cmd_morning(msg: Message):
    if msg.from_user.id not in ADMIN_IDS: return await msg.answer(msg_error_admin_only())
    conn = get_db()
    cur = conn.cursor()
    today = datetime.date.today()
    cur.execute("SELECT COUNT(*) FROM users")
    total = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM users WHERE DATE(created_at)=%s", (today,))
    new_today = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM users WHERE last_checkin=%s", (today,))
    checked = cur.fetchone()[0]
    cur.execute("SELECT username, points FROM users ORDER BY points DESC LIMIT 3")
    top3 = cur.fetchall()
    conn.close()
    lb = "\n".join(f"{i+1}. {r[0]} - {r[1]} נקודות" for i, r in enumerate(top3))
    await msg.answer(f"🌅 דוח בוקר\nתאריך: {today}\nסה\"כ משתמשים: {total} (+{new_today})\nצ'ק-אין היום: {checked}\nטופ 3:\n{lb}")

@dp.message(Command("stats"))
async def cmd_stats(msg: Message):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM users")
    total = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM users WHERE last_checkin=%s", (datetime.date.today(),))
    checked = cur.fetchone()[0]
    cur.execute("SELECT SUM(points) FROM users")
    total_points = cur.fetchone()[0] or 0
    conn.close()
    await msg.answer(f"📊 סטטיסטיקות קמפיין\nתומכים: {total}\nצ'ק-אין היום: {checked}\nסה\"כ נקודות: {total_points}\nhttps://slh-nft.com/campaign/")

@dp.message(Command("help"))
async def cmd_help(msg: Message):
    await msg.answer(msg_help(), parse_mode=ParseMode.MARKDOWN_V2, reply_markup=kb_help())

@dp.message(Command("referral"))
async def cmd_referral(msg: Message):
    link = f"https://t.me/SLH_Claude_bot?start=ref{msg.from_user.id}"
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT referral_count FROM users WHERE telegram_id=%s", (msg.from_user.id,))
    row = cur.fetchone()
    count = row[0] if row else 0
    conn.close()
    await msg.answer(msg_referral(msg.from_user.full_name, link, count), parse_mode=ParseMode.MARKDOWN_V2, reply_markup=kb_referral())

@dp.message(Command("roadmap"))
async def cmd_roadmap(msg: Message):
    await msg.answer(msg_roadmap(), parse_mode=ParseMode.MARKDOWN_V2, reply_markup=kb_roadmap())

@dp.message(Command("feedback"))
async def cmd_feedback(msg: Message):
    if not msg.text.split(" ", 1)[1:]:
        return await msg.answer(msg_error_no_args("feedback"), parse_mode=ParseMode.MARKDOWN_V2, reply_markup=kb_back_to_menu())
    fb = msg.text.split(" ", 1)[1]
    with open("feedback.txt", "a", encoding="utf-8") as f:
        f.write(f"{datetime.datetime.now()} | {msg.from_user.id} | {fb}\n")
    conn = get_db()
    cur = conn.cursor()
    cur.execute("UPDATE users SET points = points + 5 WHERE telegram_id=%s", (msg.from_user.id,))
    conn.commit()
    conn.close()
    await msg.answer(msg_feedback_success(), parse_mode=ParseMode.MARKDOWN_V2, reply_markup=kb_back_to_menu())

@dp.message(Command("daily"))
async def cmd_daily(msg: Message):
    missions = [{"title": "Check-in", "points": 5, "done": False}, {"title": "Referral", "points": 10, "done": False}]
    await msg.answer(msg_daily(missions), parse_mode=ParseMode.MARKDOWN_V2, reply_markup=kb_daily())

@dp.message(Command("myid"))
async def cmd_myid(msg: Message):
    await msg.answer(f"🪪 ה-ID שלך: {msg.from_user.id}")

@dp.message(Command("backup"))
async def cmd_backup(msg: Message):
    await msg.answer("גיבוי שמור (stub)")

@dp.message(Command("tasks"))
async def cmd_tasks(msg: Message):
    await msg.answer("משימות: /checkin, /referral, /feedback")

@dp.message(Command("support"))
async def cmd_support(msg: Message):
    await msg.answer("הצטרפו לקהילה: https://t.me/SLH_Claude_bot")

@dp.message(Command("upgrade"))
async def cmd_upgrade(msg: Message):
    await msg.answer(
        "⭐ Pro — $9.99/month\n• AI priority access\n• Create unlimited stores\n• Advanced analytics\n\n"
        "💼 Business — $29.99/month\n• All Pro features\n• Custom branding\n• Priority support\n\n"
        "To upgrade, send TON to:\n`UQCr743gEr_nqV_0SBkSp3CtYS_15R3LDLBvLmKeEv7XdGvp`\n\nContact admin after payment.",
        parse_mode=ParseMode.MARKDOWN_V2
    )

@dp.message(Command("commission"))
async def cmd_commission(msg: Message):
    if msg.from_user.id not in ADMIN_IDS: return await msg.answer(msg_error_admin_only())
    await msg.answer("עמלה: 5% לעסקה. שינוי: /set_commission <rate>")

# ========================== WALLET & STORE ==========================
@dp.message(Command("wallet"))
async def cmd_wallet(msg: Message):
    try:
        bal = get_balance(msg.from_user.id)
        await msg.answer(f"💰 יתרת הארנק: ${bal:.2f}")
    except Exception as e:
        await msg.answer(f"שגיאה: {e}")

@dp.message(Command("transfer"))
async def cmd_transfer(msg: Message):
    parts = msg.text.split()
    if len(parts) != 3: return await msg.answer("שימוש: /transfer <מזהה> <סכום>")
    try:
        to = int(parts[1])
        amt = float(parts[2])
        if transfer(msg.from_user.id, to, amt):
            log_transaction(msg.from_user.id, "debit", "transfer", amt, reference=f"to_{to}")
            log_transaction(to, "credit", "transfer", amt, reference=f"from_{msg.from_user.id}")
            emit_event(msg.from_user.id, "transfer_sent", {"to": to, "amount": amt})
            await msg.answer(f"✅ הועבר ${amt:.2f} ל-{to}")
        else:
            await msg.answer("❌ העברה נכשלה  יתרה לא מספקת")
    except Exception as e:
        await msg.answer(f"שגיאה: {e}")

@dp.message(Command("deposit"))
async def cmd_deposit(msg: Message):
    ton = os.getenv("TON_WALLET", "UQCr743gEr_nqV_0SBkSp3CtYS_15R3LDLBvLmKeEv7XdGvp")
    await msg.answer(f"💎 שלח TON ל:\n{ton}\nואז פנה לאדמין")

@dp.message(Command("store"))
async def cmd_store(msg: Message):
    parts = msg.text.split(" ", 2)
    if len(parts) < 2: return await msg.answer("שימוש: /store create <שם> <תיאור> או /store view <id>")
    if parts[1] == "create":
        if len(parts) < 3: return await msg.answer("שימוש: /store create <שם> <תיאור>")
        sid = create_store(msg.from_user.id, parts[2], parts[3] if len(parts) > 3 else "")
        await msg.answer(f"🏪 חנות נוצרה! ID: {sid}")
    elif parts[1] == "view":
        try:
            store = get_store(int(parts[2]))
            await msg.answer(f"חנות: {store['name']}\n{store['description']}")
        except: await msg.answer("שימוש: /store view <id>")
    else: await msg.answer("פקודה לא מוכרת")

@dp.message(Command("add_product"))
async def cmd_add_product(msg: Message):
    text = msg.text.split('\n')[0]
    try:
        if '"' in text:
            parts = text.split('"')
            store_id = int(parts[0].split()[1])
            name = parts[1].strip()
            price = float(parts[2].strip())
        else:
            parts = text.split()
            store_id = int(parts[1]); name = parts[2]; price = float(parts[3])
        pid = add_product(store_id, name, price)
        await msg.answer(f"📦 מוצר נוסף! ID: {pid}")
    except Exception as e: await msg.answer(f"שגיאה: {e}")

@dp.message(Command("products"))
async def cmd_products(msg: Message):
    parts = msg.text.split()
    if len(parts) < 2: return await msg.answer("שימוש: /products <store_id>")
    prods = list_products(int(parts[1]))
    if not prods: return await msg.answer("אין מוצרים")
    text = "מוצרים:\n" + "\n".join(f"{p['id']}. {p['name']} - ${p['price']:.2f}" for p in prods)
    await msg.answer(text)

@dp.message(Command("buy"))
async def cmd_buy(msg: Message):
    parts = msg.text.split()
    if len(parts) < 2: return await msg.answer("שימוש: /buy <product_id>")
    pid = int(parts[1])
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT p.price, s.owner_id FROM products p JOIN stores s ON p.store_id=s.id WHERE p.id=%s", (pid,))
    row = cur.fetchone()
    conn.close()
    if not row: return await msg.answer("מוצר לא נמצא")
    price, seller = row
    if create_order(msg.from_user.id, pid, price, seller):
        log_transaction(msg.from_user.id, "debit", "purchase", price, reference=f"product_{pid}")
        log_transaction(seller, "credit", "sale", price, reference=f"product_{pid}")
        emit_event(msg.from_user.id, "purchase", {"product_id": pid, "amount": price})
        await msg.answer(f"✅ רכישה בוצעה! {price}$ שולמו")
    else:
        await msg.answer("❌ רכישה נכשלה  יתרה לא מספקת")

@dp.message(Command("profile"))
async def cmd_profile(msg: Message):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT username, tier, created_at FROM users WHERE telegram_id=%s", (msg.from_user.id,))
    user = cur.fetchone()
    bal = get_balance(msg.from_user.id)
    conn.close()
    if user:
        await msg.answer(f"👤 משתמש: {user[0]}\n🎖 Tier: {user[1]}\n💰 יתרה: ${bal:.2f}\n📅 הצטרף: {user[2]}")
    else:
        await msg.answer("לא רשום. השתמש ב-/register")

@dp.message(Command("leaders"))
async def cmd_leaders(msg: Message):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT username, points FROM users ORDER BY points DESC LIMIT 10")
    rows = cur.fetchall()
    conn.close()
    if rows:
        await msg.answer("🏆 טופ 10:\n" + "\n".join(f"{i+1}. {r[0]} - {r[1]} נקודות" for i, r in enumerate(rows)))
    else:
        await msg.answer("אין נתונים")

@dp.message(Command("segments"))
async def cmd_segments(msg: Message):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT tier, COUNT(*) FROM users GROUP BY tier")
    rows = cur.fetchall()
    conn.close()
    if rows:
        await msg.answer("📊 פילוח משתמשים:\n" + "\n".join(f"{r[0]}: {r[1]}" for r in rows))
    else:
        await msg.answer("אין נתונים")

@dp.message(Command("dashboard"))
async def cmd_dashboard(msg: Message):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM users")
    users = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM stores")
    stores = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM products")
    products = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM events")
    events = cur.fetchone()[0]
    conn.close()
    await msg.answer(f"📊 דשבורד\nUsers: {users}\nStores: {stores}\nProducts: {products}\nEvents: {events}")

@dp.message(Command("events"))
async def cmd_events(msg: Message):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT event_type, created_at FROM events ORDER BY created_at DESC LIMIT 10")
    rows = cur.fetchall()
    conn.close()
    if rows:
        await msg.answer("📡 אירועים אחרונים:\n" + "\n".join(f"{r[0]} at {r[1]}" for r in rows))
    else:
        await msg.answer("אין אירועים")

# ========================== CRM ==========================
@dp.message(Command("crm"))
async def cmd_crm(msg: Message):
    if msg.from_user.id not in ADMIN_IDS: return await msg.answer(msg_error_admin_only())
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM users")
    total = cur.fetchone()[0]
    cur.execute("SELECT tier, COUNT(*) FROM users GROUP BY tier")
    tiers = cur.fetchall()
    tier_lines = "\n".join(f"{t[0]}: {t[1]}" for t in tiers)
    cur.execute("SELECT SUM(points) FROM users")
    total_points = cur.fetchone()[0] or 0
    conn.close()
    await msg.answer(f"📊 CRM Report\nTotal users: {total}\n\nTiers:\n{tier_lines}\n\nTotal points: {total_points}")

# ========================== ADMIN & HEALTH ==========================
@dp.message(Command("admin"))
async def cmd_admin(msg: Message):
    if msg.from_user.id not in ADMIN_IDS: return await msg.answer(msg_error_admin_only())
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM users")
    total = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM users WHERE last_checkin = CURRENT_DATE")
    checked = cur.fetchone()[0] if total > 0 else 0
    cur.execute("SELECT COUNT(*) FROM events WHERE created_at > NOW() - INTERVAL '1 day'")
    events_today = cur.fetchone()[0]
    cur.execute("SELECT COALESCE(SUM(amount),0) FROM ledger_transactions WHERE category='purchase' AND type='debit' AND created_at > NOW() - INTERVAL '1 day'")
    revenue = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM wallet_balances WHERE balance > 0")
    active_wallets = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM stores")
    stores = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM products")
    products = cur.fetchone()[0]
    conn.close()
    text = (f"👑 *SLH Admin Panel*\n━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"👥 Users: {total} total, {checked} checked in today\n"
            f"📊 Activity: {events_today} events today\n"
            f"💰 Revenue (24h): ${revenue:.2f}\n"
            f"💳 Active wallets: {active_wallets}\n"
            f"🏪 Marketplace: {stores} stores, {products} products\n\n"
            f"📌 Quick actions:\n/users\n/broadcast\n/doctor\n/dashboard")
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👥 Users", callback_data="admin_users"),
         InlineKeyboardButton(text="📢 Broadcast", callback_data="admin_broadcast")],
        [InlineKeyboardButton(text="📊 Dashboard", callback_data="cmd_dashboard"),
         InlineKeyboardButton(text="🩺 Doctor", callback_data="cmd_doctor")]
    ])
    await msg.answer(text, parse_mode=ParseMode.MARKDOWN_V2, reply_markup=keyboard)

@dp.message(Command("statusapi"))
async def cmd_statusapi(msg: Message):
    if msg.from_user.id not in ADMIN_IDS: return await msg.answer(msg_error_admin_only())
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("SELECT 1")
        db_ok = "✅"
    except:
        db_ok = "❌"
    conn.close()
    redis_ok = "✅" if os.getenv("REDIS_URL") else "⚪"
    ai_ok = "✅" if os.getenv("GROQ_API_KEY") else "❌"
    await msg.answer(f"🩺 *API & System Health*\n━━━━━━━━━━━━━━━━━━━━━\n\nDatabase: {db_ok}\nRedis: {redis_ok}\nAI (Groq): {ai_ok}\nBot online: ✅", parse_mode=ParseMode.MARKDOWN_V2)

@dp.message(Command("setreminder"))
async def cmd_setreminder(msg: Message):
    if msg.from_user.id not in ADMIN_IDS: return await msg.answer(msg_error_admin_only())
    parts = msg.text.split()
    if len(parts) < 2: return await msg.answer("שימוש: /setreminder <HH:MM> UTC\nדוגמה: /setreminder 14:00")
    time_str = parts[1]
    try:
        hour, minute = map(int, time_str.split(":"))
        if not (0 <= hour <= 23 and 0 <= minute <= 59): raise ValueError
        conn = get_db()
        cur = conn.cursor()
        cur.execute("CREATE TABLE IF NOT EXISTS bot_config (key TEXT PRIMARY KEY, value TEXT)")
        cur.execute("INSERT INTO bot_config (key, value) VALUES ('reminder_time', %s) ON CONFLICT (key) DO UPDATE SET value = %s", (time_str, time_str))
        conn.commit()
        conn.close()
        await msg.answer(f"✅ תזכורת יומית נקבעה לשעה {time_str} UTC. אשלח דוח כל יום.")
    except:
        await msg.answer("❌ פורמט לא תקין. השתמש HH:MM (24h).")

async def send_daily_reminder():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT value FROM bot_config WHERE key='reminder_time'")
    row = cur.fetchone()
    rem = row[0] if row else "14:00"
    cur.execute("SELECT COUNT(*) FROM users WHERE last_checkin = CURRENT_DATE")
    checked = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM users")
    total = cur.fetchone()[0]
    cur.execute("SELECT COALESCE(SUM(amount),0) FROM ledger_transactions WHERE category='purchase' AND type='debit' AND created_at > NOW() - INTERVAL '1 day'")
    revenue = cur.fetchone()[0] or 0
    conn.close()
    text = f"🌅 *Daily SLH Report*  {datetime.date.today()}\n\n✅ Check-ins today: {checked}/{total}\n💰 Revenue (24h): ${revenue:.2f}\n\n👉 /start to engage!"
    await bot.send_message(ADMIN_IDS[0], text, parse_mode=ParseMode.MARKDOWN_V2)

# ========================== AI ==========================
@dp.message(F.text & ~F.text.startswith("/"))
async def ai_chat(msg: Message):
    groq_key = os.getenv("GROQ_API_KEY")
    if not groq_key: return await msg.answer("AI לא מוגדר")
    try:
        resp = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {groq_key}", "Content-Type": "application/json"},
            json={
                "model": "llama-3.3-70b-versatile",
                "messages": [
                    {"role": "system", "content": "You are SLH AI. Rules: 1) Never summarize 2) Give ONE decision 3) Max 4 lines 4) End with next action 5) Hebrew first."},
                    {"role": "user", "content": msg.text}
                ],
                "max_tokens": 500
            },
            timeout=15
        )
        reply = resp.json()["choices"][0]["message"]["content"]
        await msg.answer(reply[:4000])
    except Exception as e:
        await msg.answer(f"AI error: {e}")

# ========================== DOCTOR ==========================
async def check_railway():
    try:
        token = os.getenv("RAILWAY_API_TOKEN", "")
        project_id = os.getenv("RAILWAY_PROJECT_ID", "")
        if not token or not project_id: return {"ok": False, "status": "NOT_CONFIGURED"}
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        query = """query { deployments(input: { projectId: "%s" }, first: 1) { edges { node { status } } } }""" % project_id
        async with aiohttp.ClientSession() as session:
            async with session.post("https://backboard.railway.app/graphql/v2", json={"query": query}, headers=headers, timeout=8) as resp:
                if resp.status != 200: return {"ok": False, "status": "HTTP_ERROR"}
                data = await resp.json()
                edges = data.get("data", {}).get("deployments", {}).get("edges", [])
                if not edges: return {"ok": False, "status": "NO_DEPLOYMENTS"}
                return {"ok": edges[0]["node"]["status"] == "SUCCESS", "status": edges[0]["node"]["status"]}
    except: return {"ok": False, "status": "ERROR"}

async def check_database():
    db_url = os.getenv("DATABASE_URL")
    if not db_url: return {"ok": None}
    try:
        import psycopg2
        t0 = time.perf_counter()
        conn = psycopg2.connect(db_url, connect_timeout=5)
        conn.cursor().execute("SELECT 1")
        conn.close()
        return {"ok": True, "latency_ms": int((time.perf_counter() - t0)*1000)}
    except: return {"ok": False}

async def check_redis():
    redis_url = os.getenv("REDIS_URL")
    if not redis_url: return {"ok": None}
    try:
        import redis.asyncio as aioredis
        t0 = time.perf_counter()
        r = aioredis.from_url(redis_url, socket_timeout=3)
        await r.ping()
        await r.aclose()
        return {"ok": True, "latency_ms": int((time.perf_counter() - t0)*1000)}
    except: return {"ok": False}

async def check_ai_key():
    for k in ["GROQ_API_KEY", "ANTHROPIC_API_KEY"]:
        if os.getenv(k): return {"ok": True, "provider": k.split("_")[0]}
    return {"ok": False}

def build_doctor_report(railway, db, redis, ai):
    def icon(r): return "✅" if r.get("ok") is True else ("⚪" if r.get("ok") is None else "❌")
    lines = ["🩺 *SLH System Doctor*", "━━━━━━━━━━━━━━━━━━━━━", ""]
    lines.append(f"{icon(railway)} *Railway* — {railway.get('status','?')}")
    lines.append("")
    if db.get("ok"): lines.append(f"{icon(db)} *Database* — {db.get('latency_ms','?')}ms")
    else: lines.append(f"{icon(db)} *Database* — {db.get('detail','error')}")
    if redis.get("ok") is None: lines.append(f"{icon(redis)} *Redis* — not configured")
    elif redis.get("ok"): lines.append(f"{icon(redis)} *Redis* — {redis.get('latency_ms','?')}ms")
    else: lines.append(f"{icon(redis)} *Redis* — error")
    lines.append(f"{icon(ai)} *{ai.get('provider','AI')}* — {ai.get('detail','key present' if ai.get('ok') else 'missing')}")
    lines.append("")
    lines.append("━━━━━━━━━━━━━━━━━━━━━")
    if all(c.get("ok") is True for c in [railway, db, ai]): lines.append("🟢 *All systems operational*")
    elif any(c.get("ok") is False for c in [railway, db, ai]): lines.append("🔴 *Issues detected*")
    else: lines.append("🟡 *Partial checks*")
    return "\n".join(lines)

@dp.message(Command("doctor"))
async def cmd_doctor(msg: Message):
    if msg.from_user.id not in ADMIN_IDS: return await msg.answer(msg_error_admin_only())
    await msg.bot.send_chat_action(chat_id=msg.chat.id, action="typing")
    railway, redis, ai = await asyncio.gather(check_railway(), check_redis(), check_ai_key())
    db = await check_database()
    report = build_doctor_report(railway, db, redis, ai)
    await msg.answer(report, parse_mode=ParseMode.MARKDOWN_V2)

# ========================== CALLBACK ==========================
@dp.callback_query()
async def handle_callback(callback: CallbackQuery):
    await callback.answer()
    data = callback.data
    msg = callback.message
    handlers = {
        "cmd_status": cmd_status, "cmd_points": cmd_points, "cmd_checkin": cmd_checkin,
        "cmd_daily": cmd_daily, "cmd_leaderboard": cmd_leaderboard, "cmd_referral": cmd_referral,
        "cmd_donate": cmd_donate, "cmd_help": cmd_help, "cmd_roadmap": cmd_roadmap,
        "cmd_menu": cmd_start, "cmd_stats": cmd_stats, "cmd_crm": cmd_crm,
        "admin_users": lambda m: asyncio.create_task(cmd_users(m)),
        "admin_broadcast": lambda m: asyncio.create_task(m.answer("Send /broadcast <message>")),
        "cmd_dashboard": cmd_dashboard, "cmd_doctor": cmd_doctor,
    }
    handler = handlers.get(data)
    if handler:
        await handler(msg)
    else:
        await msg.answer(f"Unknown action: {data}")

# ========================== MAIN ==========================
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
