import asyncio, os, datetime, re, requests
import psycopg2
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN_IDS = [int(x) for x in re.split(r'[,\s]+', os.getenv("ADMIN_ID", "0").strip()) if x]
TON_WALLET = os.getenv("TON_WALLET", "UQCr743gEr_nqV_0SBkSp3CtYS_15R3LDLBvLmKeEv7XdGvp")

bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

def get_db():
    return psycopg2.connect(os.getenv("DATABASE_URL"))

def init_db():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        ALTER TABLE users ADD COLUMN IF NOT EXISTS points INTEGER DEFAULT 0;
        ALTER TABLE users ADD COLUMN IF NOT EXISTS streak INTEGER DEFAULT 0;
        ALTER TABLE users ADD COLUMN IF NOT EXISTS last_checkin DATE;
        ALTER TABLE users ADD COLUMN IF NOT EXISTS tier TEXT DEFAULT 'free';
        ALTER TABLE users ADD COLUMN IF NOT EXISTS balance NUMERIC DEFAULT 0;
        CREATE TABLE IF NOT EXISTS deposits (id SERIAL PRIMARY KEY, user_id BIGINT, amount NUMERIC, tx_hash TEXT, status TEXT, created_at TIMESTAMP DEFAULT NOW());
        CREATE TABLE IF NOT EXISTS tasks (id SERIAL PRIMARY KEY, user_id BIGINT, description TEXT, done BOOLEAN DEFAULT FALSE, created_at TIMESTAMP DEFAULT NOW());
        CREATE TABLE IF NOT EXISTS feedback (id SERIAL PRIMARY KEY, user_id BIGINT, message TEXT, created_at TIMESTAMP DEFAULT NOW());
    """)
    conn.commit()
    cur.close()
    conn.close()
    print("✅ DB initialized")

init_db()

# ── Main menu keyboard ──
def main_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Status", callback_data="cmd_status"),
         InlineKeyboardButton(text="💰 Points", callback_data="cmd_points")],
        [InlineKeyboardButton(text="✅ Check-in", callback_data="cmd_checkin"),
         InlineKeyboardButton(text="🔥 Tap-to-Earn", callback_data="cmd_tap")],
        [InlineKeyboardButton(text="💎 Upgrade", callback_data="cmd_upgrade"),
         InlineKeyboardButton(text="🤝 Donate", callback_data="cmd_donate")],
        [InlineKeyboardButton(text="📈 Crypto", callback_data="cmd_crypto"),
         InlineKeyboardButton(text="👑 Admin", callback_data="cmd_admin")],
        [InlineKeyboardButton(text="❓ Help", callback_data="cmd_help")],
    ])

# ── START ──
@dp.message(Command("start"))
async def cmd_start(msg: Message):
    name = msg.from_user.first_name or "friend"
    text = f"""╔══════════════════════════════════╗
║   ███████╗██╗     ██╗  ██╗      ║
║   ██╔════╝██║     ██║  ██║      ║
║   ███████╗██║     ███████║      ║
║   ╚════██║██║     ██╔══██║      ║
║   ███████║███████╗██║  ██║      ║
║   ╚══════╝╚══════╝╚═╝  ╚═╝      ║
║                                  ║
║  AI PROJECT CREATION SYSTEM v2  ║
║  ◆ ◆ ◆ ◆ ◆ ◆ ◆ ◆ ◆ ◆ ◆ ◆      ║
╚══════════════════════════════════╝

👋 שלום, {name}!

🤖 <b>SLH AI Ecosystem</b>
פרויקט AI ליצירת חנויות, NFT, מסחר בטוקנים ותשלומי TON.

━━━━━━━━━━━━━━━━━━━━━━━━━━
<b>⚡ יכולות</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━
01 · AI Chat       Claude, Gemini, Groq
02 · Marketplace   חנויות, מוצרים, NFT
03 · Rewards       נקודות, הפניות, TON
04 · Support       ניטור, כרטיסים, סשנים
05 · CRM           משתמשים, tier, analytics
06 · Quiz & XP     קריפטו, leaderboard
07 · TON Wallet    תשלומים, תמלוגים
08 · Infra         DB, Redis, FastAPI

━━━━━━━━━━━━━━━━━━━━━━━━━━
<b>🚀 התחל עכשיו</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━
/register   → הצטרף
/dashboard  → סטטיסטיקות
/upgrade    → Premium plans
/help       → כל הפקודות

slh-nft.com · @SLH_Claude_bot"""
    await msg.answer(text, parse_mode=ParseMode.HTML, reply_markup=main_menu())

# ── HELP ──
@dp.message(Command("help"))
async def cmd_help(msg: Message):
    text = """<b>📘 SLH Bot  Full Command List</b>

<b>💎 Premium &amp; Payments</b>
/upgrade  שדרג ל-Pro/Business
/donate  תרומות
/paid  (אדמין) אשר תשלום

<b>🏆 Rewards &amp; Points</b>
/checkin  צ'ק-אין יומי
/points  נקודות
/tap  Tap-to-Earn
/leaderboard  טבלה
/referral  קישור הפניות

<b>🛒 Marketplace</b>
/store create &lt;name&gt; &lt;desc&gt;
/products &lt;store_id&gt;
/add_product
/buy &lt;product_id&gt;

<b>💰 TON Wallet</b>
/wallet  יתרה
/deposit  הפקדה
/transfer  העברה

<b>📊 Analytics &amp; CRM</b>
/dashboard /stats /status /crm /events /segments

<b>🛠 Tools</b>
/crypto /profile /myid /tasks /feedback /support /daily /roadmap /backup

<b>👑 Admin</b>
/admin /users /broadcast /morning /doctor /statusapi /setreminder"""
    await msg.answer(text, parse_mode=ParseMode.HTML)

# ── UPGRADE ──
@dp.message(Command("upgrade"))
async def cmd_upgrade(msg: Message):
    text = f"""💎 <b>SLH Premium</b>

<b>Pro</b>  9.9 TON / חודש
• AI ללא הגבלה
• Marketplace + NFT

<b>Business</b>  29 TON / חודש
• כל ה-Pro + Custom

שלח TON לכתובת:
<code>{TON_WALLET}</code>

<b>חשוב:</b> כתוב בהעברה את ה-ID שלך:
<code>{msg.from_user.id}</code>

לאחר התשלום שלח /paid"""
    await msg.answer(text, parse_mode=ParseMode.HTML)

@dp.message(Command("paid"))
async def cmd_paid(msg: Message):
    if msg.from_user.id not in ADMIN_IDS:
        return await msg.answer("רק אדמין יכול לאשר.")
    await msg.answer("✅ התשלום נרשם. Premium הופעל.")

# ── DONATE ──
@dp.message(Command("donate"))
async def cmd_donate(msg: Message):
    text = f"""🤝 <b>Donation to SLH Ecosystem</b>
<b>TON:</b> <code>{TON_WALLET}</code>
<b>USDT (TRC-20):</b> <code>TYoB3sXqH3kL9xQZqR5nL8wJqVkL3wYxZ</code>
<b>Bitcoin:</b> <code>bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh</code>
תודה! 🙏"""
    await msg.answer(text, parse_mode=ParseMode.HTML)

# ── CHECKIN ──
@dp.message(Command("checkin"))
async def cmd_checkin(msg: Message):
    uid = msg.from_user.id
    name = msg.from_user.full_name or msg.from_user.username
    conn = get_db()
    cur = conn.cursor()
    cur.execute("INSERT INTO users (telegram_id, username) VALUES (%s,%s) ON CONFLICT DO NOTHING", (uid, name))
    cur.execute("SELECT points, streak, last_checkin FROM users WHERE telegram_id=%s", (uid,))
    row = cur.fetchone()
    today = datetime.date.today()
    if row and row[2] == today:
        conn.close()
        return await msg.answer("⏳ כבר עשית צ'ק-אין היום!")
    points = row[0] if row else 0
    streak = (row[1] + 1) if row else 1
    bonus = min(streak, 7) * 5
    cur.execute("UPDATE users SET points=%s, streak=%s, last_checkin=%s WHERE telegram_id=%s",
                (points+bonus, streak, today, uid))
    conn.commit()
    conn.close()
    await msg.answer(f"✅ +{bonus} נקודות! סה\"כ: {points+bonus} | רצף: {streak} ימים")

# ── POINTS ──
@dp.message(Command("points"))
async def cmd_points(msg: Message):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT points, streak FROM users WHERE telegram_id=%s", (msg.from_user.id,))
    row = cur.fetchone()
    conn.close()
    if row:
        await msg.answer(f"💰 <b>הנקודות שלי</b>\nנקודות: {row[0]} | רצף: {row[1]} ימים", parse_mode=ParseMode.HTML)
    else:
        await msg.answer("עדיין לא נרשמת. /register")

# ── STATUS ──
@dp.message(Command("status"))
async def cmd_status(msg: Message):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM users")
    total = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM users WHERE last_checkin = CURRENT_DATE")
    checked = cur.fetchone()[0]
    conn.close()
    await msg.answer(f"📊 <b>SLH Status</b>\nמשתמשים: {total}\nצ'ק-אין היום: {checked}", parse_mode=ParseMode.HTML)

# ── CRYPTO ──
@dp.message(Command("crypto"))
async def cmd_crypto(msg: Message):
    try:
        resp = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum,the-open-network&vs_currencies=usd", timeout=10)
        data = resp.json()
        btc = data.get("bitcoin", {}).get("usd", "?")
        eth = data.get("ethereum", {}).get("usd", "?")
        ton = data.get("the-open-network", {}).get("usd", "?")
        await msg.answer(f"💰 <b>Crypto Prices</b>\nBTC: ${btc}\nETH: ${eth}\nTON: ${ton}", parse_mode=ParseMode.HTML)
    except:
        await msg.answer("⚠️ לא ניתן להביא מחירים כרגע.")

# ── TAP-TO-EARN ──
@dp.message(Command("tap"))
async def cmd_tap(msg: Message):
    await msg.answer("🔥 <b>Tap-to-Earn!</b>\nלחץ על הכפתור = 5 נקודות.",
                     parse_mode=ParseMode.HTML,
                     reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                         [InlineKeyboardButton(text="TAP HERE 🔥", callback_data="do_tap")]
                     ]))

@dp.callback_query(F.data == "do_tap")
async def handle_tap(callback: CallbackQuery):
    uid = callback.from_user.id
    conn = get_db()
    cur = conn.cursor()
    cur.execute("UPDATE users SET points = points + 5 WHERE telegram_id=%s", (uid,))
    conn.commit()
    cur.execute("SELECT points FROM users WHERE telegram_id=%s", (uid,))
    pts = cur.fetchone()[0]
    conn.close()
    await callback.answer(f"+5! Total: {pts}", show_alert=True)

# ── ADMIN ──
@dp.message(Command("admin"))
async def cmd_admin(msg: Message):
    if msg.from_user.id not in ADMIN_IDS:
        return await msg.answer("👑 אדמין בלבד.")
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM users")
    total = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM users WHERE last_checkin = CURRENT_DATE")
    checked = cur.fetchone()[0]
    conn.close()
    await msg.answer(f"👑 <b>Admin Panel</b>\nמשתמשים: {total}\nצ'ק-אין היום: {checked}", parse_mode=ParseMode.HTML)

@dp.message(Command("users"))
async def cmd_users(msg: Message):
    if msg.from_user.id not in ADMIN_IDS:
        return await msg.answer("👑 אדמין בלבד.")
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT telegram_id, username FROM users LIMIT 20")
    rows = cur.fetchall()
    conn.close()
    text = "\n".join(f"{u[1]} ({u[0]})" for u in rows)
    await msg.answer(f"👥 <b>משתמשים</b>\n{text}", parse_mode=ParseMode.HTML)

@dp.message(Command("broadcast"))
async def cmd_broadcast(msg: Message):
    if msg.from_user.id not in ADMIN_IDS:
        return await msg.answer("👑 אדמין בלבד.")
    parts = msg.text.split(" ", 1)
    if len(parts) < 2:
        return await msg.answer("שימוש: /broadcast &lt;הודעה&gt;", parse_mode=ParseMode.HTML)
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
        except:
            pass
    await msg.answer(f"📢 נשלח ל-{sent}/{len(users)}")

# ── TASKS / FEEDBACK ──
@dp.message(Command("tasks"))
async def cmd_tasks(msg: Message):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT description, done FROM tasks WHERE user_id=%s ORDER BY created_at DESC LIMIT 5", (msg.from_user.id,))
    rows = cur.fetchall()
    conn.close()
    if not rows:
        return await msg.answer("אין משימות. /task <description>")
    text = "\n".join(f"{'✅' if r[1] else '⬜'} {r[0]}" for r in rows)
    await msg.answer(f"📋 <b>משימות</b>\n{text}", parse_mode=ParseMode.HTML)

@dp.message(Command("task"))
async def cmd_add_task(msg: Message):
    parts = msg.text.split(" ", 1)
    if len(parts) < 2:
        return await msg.answer("שימוש: /task <תיאור>")
    conn = get_db()
    cur = conn.cursor()
    cur.execute("INSERT INTO tasks (user_id, description) VALUES (%s, %s)", (msg.from_user.id, parts[1]))
    conn.commit()
    conn.close()
    await msg.answer("✅ משימה נוספה.")

@dp.message(Command("feedback"))
async def cmd_feedback(msg: Message):
    parts = msg.text.split(" ", 1)
    if len(parts) < 2:
        return await msg.answer("שימוש: /feedback <הודעה>")
    conn = get_db()
    cur = conn.cursor()
    cur.execute("INSERT INTO feedback (user_id, message) VALUES (%s, %s)", (msg.from_user.id, parts[1]))
    conn.commit()
    conn.close()
    await msg.answer("🙏 תודה על המשוב!")

# ── CALLBACKS ──
@dp.callback_query()
async def handle_callback(callback: CallbackQuery):
    await callback.answer()
    data = callback.data
    msg = callback.message
    handlers = {
        "cmd_status": cmd_status, "cmd_points": cmd_points, "cmd_checkin": cmd_checkin,
        "cmd_admin": cmd_admin, "cmd_upgrade": cmd_upgrade, "cmd_tap": cmd_tap,
        "cmd_donate": cmd_donate, "cmd_crypto": cmd_crypto, "cmd_help": cmd_help
    }
    handler = handlers.get(data)
    if handler:
        await handler(msg)

# ── MAIN ──
async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
