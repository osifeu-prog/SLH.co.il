import asyncio, os, datetime, json
import asyncpg
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")
ADMIN_IDS = [int(x) for x in os.getenv("ADMIN_ID", "224223270").split(",")]
TON_WALLET = os.getenv("TON_WALLET", "UQCr743gEr_nqV_0SBkSp3CtYS_15R3LDLBvLmKeEv7XdGvp")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
pool = None

# ====================== AI Engine ======================
async def ask_ai(prompt: str) -> str:
    """Try Groq -> Gemini -> OpenAI -> fallback"""
    # Try Groq first
    try:
        import groq
        client = groq.Client(api_key=GROQ_API_KEY)
        chat = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama3-8b-8192",
            max_tokens=500
        )
        return chat.choices[0].message.content
    except Exception as e:
        pass
    
    # Try Gemini
    if GEMINI_API_KEY:
        try:
            import google.generativeai as genai
            genai.configure(api_key=GEMINI_API_KEY)
            model = genai.GenerativeModel("gemini-1.5-flash")
            resp = model.generate_content(prompt)
            return resp.text
        except:
            pass
    
    # Try OpenAI
    if OPENAI_API_KEY:
        try:
            import openai
            openai.api_key = OPENAI_API_KEY
            resp = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500
            )
            return resp.choices[0].message.content
        except:
            pass
    
    return "מצטער, שירות ה-AI אינו זמין כרגע. אנא נסה שנית מאוחר יותר."

# ====================== DB ======================
async def create_pool():
    global pool
    pool = await asyncpg.create_pool(DATABASE_URL)
    async with pool.acquire() as conn:
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                telegram_id BIGINT UNIQUE NOT NULL,
                username TEXT,
                full_name TEXT,
                points INTEGER DEFAULT 0,
                energy INTEGER DEFAULT 100,
                tier TEXT DEFAULT 'free',
                referral_code TEXT,
                referred_by BIGINT,
                created_at TIMESTAMP DEFAULT NOW(),
                last_seen TIMESTAMP DEFAULT NOW(),
                last_energy_update TIMESTAMP DEFAULT NOW(),
                is_admin BOOLEAN DEFAULT FALSE
            );
        ''')
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id SERIAL PRIMARY KEY, user_id BIGINT, description TEXT,
                done BOOLEAN DEFAULT FALSE, created_at TIMESTAMP DEFAULT NOW()
            );
        ''')
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS identities (
                id SERIAL PRIMARY KEY, user_id BIGINT, full_name TEXT,
                doc_type TEXT, verified BOOLEAN DEFAULT FALSE, created_at TIMESTAMP DEFAULT NOW()
            );
        ''')
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS customers (
                id SERIAL PRIMARY KEY, name TEXT, phone TEXT,
                added_by BIGINT, created_at TIMESTAMP DEFAULT NOW()
            );
        ''')
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS notes (
                id SERIAL PRIMARY KEY, customer_id INTEGER, content TEXT,
                created_by BIGINT, created_at TIMESTAMP DEFAULT NOW()
            );
        ''')
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id SERIAL PRIMARY KEY, name TEXT, description TEXT,
                price INTEGER, stock INTEGER DEFAULT 0, created_at TIMESTAMP DEFAULT NOW()
            );
        ''')
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS purchases (
                id SERIAL PRIMARY KEY, user_id BIGINT, product_id INTEGER,
                points_spent INTEGER, created_at TIMESTAMP DEFAULT NOW()
            );
        ''')
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id SERIAL PRIMARY KEY, from_user BIGINT, to_user BIGINT,
                amount INTEGER, type TEXT, created_at TIMESTAMP DEFAULT NOW()
            );
        ''')
        await conn.execute('''
            ALTER TABLE users 
            ADD COLUMN IF NOT EXISTS referral_code TEXT,
            ADD COLUMN IF NOT EXISTS referred_by BIGINT,
            ADD COLUMN IF NOT EXISTS last_energy_update TIMESTAMP DEFAULT NOW(),
            ADD COLUMN IF NOT EXISTS energy INTEGER DEFAULT 100;
        ''')
        print("All tables & migration OK")
    print("DB Pool ready")

async def ensure_user(uid: int, username: str):
    async with pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO users (telegram_id, username, referral_code)
            VALUES ($1, $2, $3) ON CONFLICT (telegram_id) 
            DO UPDATE SET username = $2, last_seen = NOW()
        """, uid, username, f"SLH{uid}")

def get_multiplier(tier):
    if not tier: return 1.0
    return 2.0 if tier == "business" else 1.5 if tier == "pro" else 1.0

# ====================== Keyboards ======================
def main_menu():
    kb = [
        [types.InlineKeyboardButton(text="📊 סטטוס", callback_data="status"),
         types.InlineKeyboardButton(text="⭐ נקודות", callback_data="points")],
        [types.InlineKeyboardButton(text="✅ צ'ק-אין", callback_data="checkin"),
         types.InlineKeyboardButton(text="⚡ הקש Tap", callback_data="tap")],
        [types.InlineKeyboardButton(text="💎 שדרוג", callback_data="upgrade"),
         types.InlineKeyboardButton(text="🤝 תרומה", callback_data="donate")],
        [types.InlineKeyboardButton(text="💰 קריפטו", callback_data="crypto"),
         types.InlineKeyboardButton(text="🔗 הפניות", callback_data="referral")],
        [types.InlineKeyboardButton(text="📋 משימות", callback_data="tasks"),
         types.InlineKeyboardButton(text="👛 ארנק", callback_data="wallet")],
        [types.InlineKeyboardButton(text="🔮 אורקל", callback_data="oracle"),
         types.InlineKeyboardButton(text="☮️ שלום", callback_data="peace")],
        [types.InlineKeyboardButton(text="📊 דשבורד", callback_data="dashboard"),
         types.InlineKeyboardButton(text="👑 ניהול", callback_data="admin")],
        [types.InlineKeyboardButton(text="❓ עזרה", callback_data="help")]
    ]
    return types.InlineKeyboardMarkup(inline_keyboard=kb)

# ====================== Commands ======================
@dp.message(Command("start"))
async def cmd_start(msg: types.Message):
    uid = msg.from_user.id
    name = msg.from_user.full_name or msg.from_user.username or "friend"
    await ensure_user(uid, name)
    await msg.answer("🧠 <b>SLH Spark AI v4.0</b>\n\nכל המערכות פעילות!", reply_markup=main_menu())

@dp.message(Command("status"))
async def cmd_status(msg: types.Message):
    uid = msg.from_user.id
    async with pool.acquire() as conn:
        user = await conn.fetchrow("SELECT points, energy, tier FROM users WHERE telegram_id=$1", uid)
        if user:
            await msg.answer(f"📊 <b>סטטוס</b>\n⭐ נקודות: {user['points']}\n⚡ אנרגיה: {user['energy']}\n🏅 רמה: {user['tier']}")
        else:
            await msg.answer("משתמש לא נמצא. הקלד /start")

@dp.message(Command("points"))
async def cmd_points(msg: types.Message):
    uid = msg.from_user.id
    async with pool.acquire() as conn:
        pts = await conn.fetchval("SELECT points FROM users WHERE telegram_id=$1", uid)
        await msg.answer(f"⭐ הנקודות שלך: {pts or 0}")

@dp.message(Command("checkin"))
async def cmd_checkin(msg: types.Message):
    uid = msg.from_user.id
    async with pool.acquire() as conn:
        await conn.execute("UPDATE users SET points = points + 10, last_seen = NOW() WHERE telegram_id=$1", uid)
        pts = await conn.fetchval("SELECT points FROM users WHERE telegram_id=$1", uid)
        await msg.answer(f"✅ צ'ק-אין בוצע! +10 נקודות. סה\"כ: {pts}")

@dp.message(Command("tap"))
async def cmd_tap(msg: types.Message):
    uid = msg.from_user.id
    await ensure_user(uid, msg.from_user.username or "unknown")
    async with pool.acquire() as conn:
        await conn.execute("""
            UPDATE users SET 
                energy = LEAST(100, energy + FLOOR(EXTRACT(EPOCH FROM (NOW() - last_energy_update))/3)::int),
                last_energy_update = NOW()
            WHERE telegram_id = $1
        """, uid)
        user = await conn.fetchrow("SELECT energy, points, tier FROM users WHERE telegram_id=$1", uid)
        if not user or user['energy'] < 5:
            return await msg.answer("❌ אין מספיק אנרגיה. חכה מספר שניות.")
        gain = int(5 * get_multiplier(user['tier']))
        new_energy = user['energy'] - 5
        new_points = user['points'] + gain
        await conn.execute("UPDATE users SET energy=$1, points=$2 WHERE telegram_id=$3", new_energy, new_points, uid)
        await msg.answer(f"⚡ +{gain} נקודות! סה\"כ: {new_points} | אנרגיה: {new_energy}")

@dp.message(Command("tasks"))
async def cmd_tasks(msg: types.Message):
    uid = msg.from_user.id
    await ensure_user(uid, msg.from_user.username or "unknown")
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT id, description, done FROM tasks WHERE user_id=$1 AND created_at::date = CURRENT_DATE", uid)
        if not rows:
            for desc in ["Check-in today", "Tap 3 times", "Invite a friend"]:
                await conn.execute("INSERT INTO tasks (user_id, description) VALUES ($1,$2)", uid, desc)
            rows = await conn.fetch("SELECT id, description, done FROM tasks WHERE user_id=$1 AND created_at::date = CURRENT_DATE", uid)
        text = "📋 <b>משימות יומיות</b>:\n\n" + "\n".join(f"{'✅' if r['done'] else '❌'} {r['description']} (ID:{r['id']})" for r in rows)
        await msg.answer(text + "\n\nהשלם משימה: /done [ID]")

@dp.message(Command("done"))
async def cmd_done(msg: types.Message):
    parts = msg.text.split()
    if len(parts) < 2:
        return await msg.answer("שימוש: /done [ID]")
    task_id = int(parts[1])
    uid = msg.from_user.id
    async with pool.acquire() as conn:
        await conn.execute("UPDATE tasks SET done=true WHERE id=$1 AND user_id=$2", task_id, uid)
        await msg.answer(f"✅ משימה {task_id} הושלמה!")

@dp.message(Command("referral"))
async def cmd_referral(msg: types.Message):
    uid = msg.from_user.id
    async with pool.acquire() as conn:
        code = await conn.fetchval("SELECT referral_code FROM users WHERE telegram_id=$1", uid)
        if not code:
            code = f"SLH{uid}"
            await conn.execute("UPDATE users SET referral_code=$1 WHERE telegram_id=$2", code, uid)
        await msg.answer(f"🔗 קישור ההפניה שלך:\nhttps://t.me/SLH_Claude_bot?start={code}\n\nשתף עם חברים וקבל נקודות!")

@dp.message(Command("dashboard"))
async def cmd_dashboard(msg: types.Message):
    uid = msg.from_user.id
    async with pool.acquire() as conn:
        pts = await conn.fetchval("SELECT points FROM users WHERE telegram_id=$1", uid) or 0
        refs = await conn.fetchval("SELECT count(*) FROM users WHERE referred_by=$1", uid) or 0
        await msg.answer(f"📊 <b>לוח מחוונים</b>\n⭐ נקודות: {pts}\n👥 חברים שהופנו: {refs}")

@dp.message(Command("leaderboard"))
async def cmd_leaderboard(msg: types.Message):
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT username, points FROM users ORDER BY points DESC LIMIT 10")
        text = "\n".join(f"{i+1}. {r['username'] or '?'} - {r['points']}" for i,r in enumerate(rows))
        await msg.answer(f"🏆 <b>טבלת מובילים</b>:\n{text}")

@dp.message(Command("profile"))
async def cmd_profile(msg: types.Message):
    uid = msg.from_user.id
    async with pool.acquire() as conn:
        user = await conn.fetchrow("SELECT username, points, tier FROM users WHERE telegram_id=$1", uid)
        if user:
            await msg.answer(f"👤 פרופיל:\nשם: {user['username']}\nנקודות: {user['points']}\nרמה: {user['tier']}")
        else:
            await msg.answer("אין פרופיל. /start")

@dp.message(Command("myid"))
async def cmd_myid(msg: types.Message):
    await msg.answer(f"🆔 ה-Telegram ID שלך: <code>{msg.from_user.id}</code>")

@dp.message(Command("help"))
async def cmd_help(msg: types.Message):
    await msg.answer("❓ עזרה:\n/start, /status, /tap, /tasks, /wallet, /admin ועוד... שלח לי שאלה ואענה!")

# Admin
@dp.message(Command("admin"))
async def cmd_admin(msg: types.Message):
    if msg.from_user.id not in ADMIN_IDS:
        return await msg.answer("⛔ גישת מנהל בלבד.")
    await msg.answer("👑 תפריט מנהל:\n/users /broadcast /crm /stats /backup")

@dp.message(Command("users"))
async def cmd_users(msg: types.Message):
    if msg.from_user.id not in ADMIN_IDS:
        return await msg.answer("⛔ מנהל בלבד.")
    async with pool.acquire() as conn:
        total = await conn.fetchval("SELECT count(*) FROM users")
        await msg.answer(f"👥 סה\"כ משתמשים: {total}")

@dp.message(Command("stats"))
async def cmd_stats(msg: types.Message):
    if msg.from_user.id not in ADMIN_IDS:
        return await msg.answer("⛔ מנהל בלבד.")
    async with pool.acquire() as conn:
        users = await conn.fetchval("SELECT count(*) FROM users")
        points = await conn.fetchval("SELECT sum(points) FROM users") or 0
        await msg.answer(f"📈 סטטיסטיקות:\n👥 משתמשים: {users}\n⭐ סה\"כ נקודות: {points}")

# Stub commands
@dp.message(Command("register"))
async def cmd_register(msg: types.Message): await msg.answer("📝 הרשמה: /identity")
@dp.message(Command("crypto"))
async def cmd_crypto(msg: types.Message): await msg.answer("💰 מידע קריפטו יגיע בקרוב.")
@dp.message(Command("donate"))
async def cmd_donate(msg: types.Message): await msg.answer(f"🤝 תרומה:\n<code>{TON_WALLET}</code>")
@dp.message(Command("upgrade"))
async def cmd_upgrade(msg: types.Message): await msg.answer("💎 שדרוג: Pro (9.9 TON) / Business (29 TON) - /paid")
@dp.message(Command("oracle"))
async def cmd_oracle(msg: types.Message): await msg.answer("🔮 אורקל  חכמה עתיקה. שאל שאלה.")
@dp.message(Command("peace"))
async def cmd_peace(msg: types.Message): await msg.answer("☮️ שלום עולמי מתחיל בך.")
@dp.message(Command("wallet"))
async def cmd_wallet(msg: types.Message): await msg.answer("👛 ארנק: /deposit, /transfer, /simdeposit")
@dp.message(Command("deposit"))
async def cmd_deposit(msg: types.Message): await msg.answer("💰 הפקדה: שלח TON לארנק.")
@dp.message(Command("transfer"))
async def cmd_transfer(msg: types.Message): await msg.answer("🔁 העברת נקודות: /transfer [מזהה] [כמות]")
@dp.message(Command("paid"))
async def cmd_paid(msg: types.Message): await msg.answer("💳 תשלום (בקרוב: TON webhook)")
@dp.message(Command("invite"))
async def cmd_invite(msg: types.Message): await cmd_referral(msg)
@dp.message(Command("simdeposit"))
async def cmd_simdeposit(msg: types.Message):
    uid = msg.from_user.id
    async with pool.acquire() as conn:
        await conn.execute("UPDATE users SET points = points + 100 WHERE telegram_id=$1", uid)
        await msg.answer("💸 +100 נקודות (הדמיה)")
@dp.message(Command("addcustomer"))
async def cmd_addcustomer(msg: types.Message): await msg.answer("➕ הוספת לקוח: /addcustomer [שם] [טלפון]")
@dp.message(Command("customers"))
async def cmd_customers(msg: types.Message):
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT id, name, phone FROM customers LIMIT 10")
        if not rows: return await msg.answer("אין לקוחות.")
        await msg.answer("📋 לקוחות:\n" + "\n".join(f"{r['id']}: {r['name']} - {r['phone']}" for r in rows))
@dp.message(Command("addnote"))
async def cmd_addnote(msg: types.Message): await msg.answer("📝 הערה: /addnote [מזהה לקוח] [טקסט]")
@dp.message(Command("notes"))
async def cmd_notes(msg: types.Message): await msg.answer("📝 צפייה בהערות: /notes [מזהה לקוח]")
@dp.message(Command("vip"))
async def cmd_vip(msg: types.Message): await msg.answer("👑 VIP  בקרוב.")
@dp.message(Command("crm"))
async def cmd_crm(msg: types.Message): await msg.answer("📊 CRM: /customers, /addnote, /notes")
@dp.message(Command("broadcast"))
async def cmd_broadcast(msg: types.Message): await msg.answer("📢 שידור (בקרוב)")
@dp.message(Command("morning"))
async def cmd_morning(msg: types.Message): await msg.answer("🌅 בוקר טוב!")
@dp.message(Command("doctor"))
async def cmd_doctor(msg: types.Message): await msg.answer("🩺 דוקטור (בקרוב)")
@dp.message(Command("statusapi"))
async def cmd_statusapi(msg: types.Message): await msg.answer("📡 API: 200 OK")
@dp.message(Command("setreminder"))
async def cmd_setreminder(msg: types.Message): await msg.answer("⏰ תזכורת הוגדרה (דמו)")
@dp.message(Command("backup"))
async def cmd_backup(msg: types.Message): await msg.answer("💾 גיבוי (בקרוב)")
@dp.message(Command("events"))
async def cmd_events(msg: types.Message): await msg.answer("📅 אירועים: אין אירועים.")
@dp.message(Command("segments"))
async def cmd_segments(msg: types.Message): await msg.answer("📊 סגמנטים (בקרוב)")
@dp.message(Command("guide"))
async def cmd_guide(msg: types.Message): await msg.answer("📘 מדריך: https://example.com/guide")
@dp.message(Command("faq"))
async def cmd_faq(msg: types.Message): await msg.answer("❓ שאלות נפוצות: השתמש ב-/tap לצבור נקודות.")
@dp.message(Command("tutorial"))
async def cmd_tutorial(msg: types.Message): await msg.answer("🎓 הדרכה: התחל עם /start, הקש Tap.")

class IdentityForm(StatesGroup):
    waiting_for_name = State()
    waiting_for_doc = State()

@dp.message(Command("identity"))
async def cmd_identity(msg: types.Message, state: FSMContext):
    await state.set_state(IdentityForm.waiting_for_name)
    await msg.answer("📛 אנא הזן את שמך המלא:")

@dp.message(IdentityForm.waiting_for_name)
async def process_name(msg: types.Message, state: FSMContext):
    await state.update_data(full_name=msg.text)
    await state.set_state(IdentityForm.waiting_for_doc)
    await msg.answer("📄 העלה תמונה של תעודת זהות (או הקלד 'דלג'):")

@dp.message(IdentityForm.waiting_for_doc)
async def process_doc(msg: types.Message, state: FSMContext):
    data = await state.get_data()
    full_name = data['full_name']
    uid = msg.from_user.id
    async with pool.acquire() as conn:
        await conn.execute("INSERT INTO identities (user_id, full_name, doc_type) VALUES ($1,$2,'manual')", uid, full_name)
    await state.clear()
    await msg.answer("✅ זהות נשמרה.")

@dp.message(Command("myidentity"))
async def cmd_myidentity(msg: types.Message):
    uid = msg.from_user.id
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT full_name, verified FROM identities WHERE user_id=$1 ORDER BY id DESC LIMIT 1", uid)
        if row:
            status = "✔️ מאומת" if row['verified'] else "❌ לא מאומת"
            await msg.answer(f"👤 {row['full_name']} - {status}")
        else:
            await msg.answer("אין זהות שמורה. /identity")

# ====================== AI Fallback ======================
@dp.message()
async def ai_fallback(msg: types.Message):
    if msg.text and msg.text.startswith('/'):
        return
    await bot.send_chat_action(msg.chat.id, 'typing')
    reply = await ask_ai(msg.text)
    await msg.answer(reply)

# ====================== Callbacks ======================
@dp.callback_query()
async def main_callback(call: types.CallbackQuery):
    await call.answer()
    data = call.data
    msg = call.message
    mapping = {
        "status": cmd_status, "points": cmd_points, "checkin": cmd_checkin,
        "tap": cmd_tap, "crypto": cmd_crypto, "donate": cmd_donate,
        "upgrade": cmd_upgrade, "tasks": cmd_tasks, "oracle": cmd_oracle,
        "peace": cmd_peace, "wallet": cmd_wallet, "referral": cmd_referral,
        "dashboard": cmd_dashboard, "admin": cmd_admin, "help": cmd_help
    }
    handler = mapping.get(data)
    if handler:
        await handler(msg)
    else:
        await msg.answer("✨ Feature coming soon")

async def main():
    await create_pool()
    await bot.delete_webhook(drop_pending_updates=True)
    print("SLH Spark AI v4.0 - all systems active")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())