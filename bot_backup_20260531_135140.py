import asyncio, os, datetime, re, requests, time, threading, json, traceback
import psycopg2
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from fastapi import FastAPI, Request, Response
from fastapi.responses import HTMLResponse, JSONResponse
import uvicorn

load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN_IDS = [int(x) for x in re.split(r'[,\s]+', os.getenv("ADMIN_ID", "0").strip()) if x]
TON_WALLET = os.getenv("TON_WALLET", "UQCr743gEr_nqV_0SBkSp3CtYS_15R3LDLBvLmKeEv7XdGvp")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
DATABASE_URL = os.getenv("DATABASE_URL", "")
PORT = int(os.getenv("PORT", "8080"))

bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()
web_app = FastAPI()

# ---------- DATABASE (safe init) ----------
def get_db():
    try:
        return psycopg2.connect(DATABASE_URL)
    except Exception as e:
        print(f"DB connection error: {e}")
        return None

def init_db():
    try:
        conn = get_db()
        if not conn: return
        cur = conn.cursor()
        cur.execute("""
            ALTER TABLE users ADD COLUMN IF NOT EXISTS points INTEGER DEFAULT 0;
            ALTER TABLE users ADD COLUMN IF NOT EXISTS streak INTEGER DEFAULT 0;
            ALTER TABLE users ADD COLUMN IF NOT EXISTS last_checkin DATE;
            ALTER TABLE users ADD COLUMN IF NOT EXISTS tier TEXT DEFAULT 'free';
            ALTER TABLE users ADD COLUMN IF NOT EXISTS balance NUMERIC DEFAULT 0;
            ALTER TABLE users ADD COLUMN IF NOT EXISTS energy INTEGER DEFAULT 100;
            ALTER TABLE users ADD COLUMN IF NOT EXISTS last_energy_update TIMESTAMP DEFAULT NOW();
            ALTER TABLE users ADD COLUMN IF NOT EXISTS referral_code TEXT;
            ALTER TABLE users ADD COLUMN IF NOT EXISTS referred_by BIGINT;
            ALTER TABLE users ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT NOW();
            ALTER TABLE users ADD COLUMN IF NOT EXISTS last_seen TIMESTAMP DEFAULT NOW();
            CREATE TABLE IF NOT EXISTS tasks (id SERIAL PRIMARY KEY, user_id BIGINT, description TEXT, done BOOLEAN DEFAULT FALSE, created_at TIMESTAMP DEFAULT NOW());
            CREATE TABLE IF NOT EXISTS feedback (id SERIAL PRIMARY KEY, user_id BIGINT, message TEXT, created_at TIMESTAMP DEFAULT NOW());
            CREATE TABLE IF NOT EXISTS payments (id SERIAL PRIMARY KEY, user_id BIGINT, amount NUMERIC, plan TEXT, status TEXT DEFAULT 'pending', created_at TIMESTAMP DEFAULT NOW());
            CREATE TABLE IF NOT EXISTS events (id SERIAL PRIMARY KEY, user_id BIGINT, event_type TEXT, payload TEXT, created_at TIMESTAMP DEFAULT NOW());
        """)
        conn.commit()
        cur.close()
        conn.close()
        print("✅ DB ready")
    except Exception as e:
        print(f"DB init error (non-fatal): {e}")

init_db()

def ensure_user(uid, name):
    try:
        conn = get_db()
        if not conn: return
        cur = conn.cursor()
        ref = f"SLH{uid}"
        cur.execute("INSERT INTO users (telegram_id, username, tier, referral_code) VALUES (%s,%s,'free',%s) ON CONFLICT (telegram_id) DO UPDATE SET username=%s, last_seen=NOW()", (uid, name, ref, name))
        conn.commit()
        cur.close()
        conn.close()
    except: pass

# ---------- KEYBOARD ----------
def main_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 סטטוס", callback_data="cmd_status"),
         InlineKeyboardButton(text="⭐ נקודות", callback_data="cmd_points")],
        [InlineKeyboardButton(text="✅ Check-in", callback_data="cmd_checkin"),
         InlineKeyboardButton(text="⚡ Tap-to-Earn", callback_data="cmd_tap")],
        [InlineKeyboardButton(text="💎 שדרוג", callback_data="cmd_upgrade"),
         InlineKeyboardButton(text="🤝 תרומה", callback_data="cmd_donate")],
        [InlineKeyboardButton(text="💰 Crypto", callback_data="cmd_crypto"),
         InlineKeyboardButton(text="📋 Dashboard", callback_data="cmd_dashboard")],
        [InlineKeyboardButton(text="❓ עזרה", callback_data="cmd_help")],
    ])

# ---------- SIMPLE HANDLERS ----------
@dp.message(Command("start"))
async def cmd_start(msg: Message):
    uid = msg.from_user.id
    name = msg.from_user.full_name or "חבר"
    ensure_user(uid, name)
    await msg.answer(f"<b>✅ SLH SPARK AI v3.2 alive!</b>\nHello, {name}!", reply_markup=main_menu())

@dp.message(Command("help"))
async def cmd_help(msg: Message):
    await msg.answer("Commands: /start /help /checkin /points /status /dashboard /crypto /tap /wallet /deposit /leaderboard /tasks /admin /doctor /test")

@dp.message(Command("test"))
async def cmd_test(msg: Message):
    if msg.from_user.id not in ADMIN_IDS: return await msg.answer("Admin only")
    report = "🧪 Self-Test\n"
    try:
        conn = get_db(); conn.close(); report += "✅ DB\n"
    except: report += "❌ DB\n"
    try:
        r = requests.get(f"https://api.telegram.org/bot{TOKEN}/getMe", timeout=5)
        report += "✅ Bot Token\n" if r.json().get("ok") else "❌ Token Invalid\n"
    except: report += "❌ Token Error\n"
    await msg.answer(report)

# ---------- AI CHAT ----------
@dp.message(F.text & ~F.text.startswith("/"))
async def ai_chat(msg: Message):
    if not GROQ_API_KEY: return
    try:
        resp = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"},
            json={"model": "llama-3.3-70b-versatile", "messages": [{"role": "user", "content": msg.text}], "max_tokens": 500},
            timeout=15
        )
        reply = resp.json()["choices"][0]["message"]["content"]
        await msg.answer(reply[:4000], parse_mode=ParseMode.HTML)
    except: pass

# ---------- TON MONITOR (thread) ----------
def ton_monitor():
    while True:
        try:
            # simple check, not blocking
            time.sleep(30)
        except: pass

threading.Thread(target=ton_monitor, daemon=True).start()

# ---------- DASHBOARD (minimal) ----------
@web_app.get("/", response_class=HTMLResponse)
async def dashboard():
    return HTMLResponse("<h1>SLH Dashboard</h1><p>Bot is running.</p>")

@web_app.get("/health")
async def health():
    return {"status": "ok"}

# ---------- MAIN ----------
async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    config = uvicorn.Config(web_app, host="0.0.0.0", port=PORT, log_level="warning")
    server = uvicorn.Server(config)
    await asyncio.gather(server.serve(), dp.start_polling(bot))

if __name__ == "__main__":
    asyncio.run(main())
