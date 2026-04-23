import os, requests, asyncpg, redis, json
from datetime import datetime
from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, ContextTypes

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "8724910039:AAFkZYO_fV5VFdDpzszWHfhYvJRO25b1fDg")
ADMIN_IDS = [584203384, 546671882]
DATABASE_URL = os.getenv("DATABASE_URL")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
DOMAIN = "https://slh.co.il"
RAILWAY_URL = "https://slhcoil-production.up.railway.app"
GITHUB_REPO = "https://github.com/osifeu-prog/SLH.co.il"

# Redis
try:
    redis_client = redis.from_url(REDIS_URL)
    redis_client.ping()
    REDIS_OK = True
except:
    REDIS_OK = False
    redis_client = None

async def init_db():
    conn = await asyncpg.connect(DATABASE_URL)
    await conn.execute('''
        CREATE TABLE IF NOT EXISTS roi_history (id SERIAL PRIMARY KEY, roi REAL, timestamp TEXT, signal_name TEXT);
        CREATE TABLE IF NOT EXISTS feedback (id SERIAL PRIMARY KEY, user_id TEXT, username TEXT, message TEXT, timestamp TEXT);
        CREATE TABLE IF NOT EXISTS users (user_id TEXT PRIMARY KEY, username TEXT, first_seen TEXT)
    ''')
    await conn.close()

async def save_feedback(user_id, username, message):
    conn = await asyncpg.connect(DATABASE_URL)
    await conn.execute('INSERT INTO feedback (user_id, username, message, timestamp) VALUES ($1, $2, $3, $4)', str(user_id), username, message, datetime.now().isoformat())
    await conn.close()

async def register_user(user_id, username):
    conn = await asyncpg.connect(DATABASE_URL)
    await conn.execute('INSERT INTO users (user_id, username, first_seen) VALUES ($1, $2, $3) ON CONFLICT (user_id) DO NOTHING', str(user_id), username, datetime.now().isoformat())
    await conn.close()

async def save_roi(roi, signal_name="Signal"):
    conn = await asyncpg.connect(DATABASE_URL)
    await conn.execute('INSERT INTO roi_history (roi, timestamp, signal_name) VALUES ($1, $2, $3)', roi, datetime.now().isoformat(), signal_name)
    await conn.close()

async def get_roi_history(limit=10):
    conn = await asyncpg.connect(DATABASE_URL)
    rows = await conn.fetch(f'SELECT roi, timestamp, signal_name FROM roi_history ORDER BY id DESC LIMIT {limit}')
    await conn.close()
    return rows

def admin_only(func):
    async def wrapper(update, context):
        if update.effective_user.id not in ADMIN_IDS:
            await update.message.reply_text("⛔ Access denied.")
            return
        return await func(update, context)
    return wrapper

async def start(update, context):
    await register_user(update.effective_user.id, update.effective_user.username)
    await update.message.reply_text(f"🤖 SLH Macro Bot\n/roi - Last ROI\n/price - BTC\n/feedback <msg>\n/status - Admin", parse_mode="Markdown")

async def feedback(update, context):
    if not context.args:
        await update.message.reply_text("Usage: /feedback <message>")
        return
    user = update.effective_user
    msg = " ".join(context.args)
    await save_feedback(user.id, user.username or "no_username", msg)
    await update.message.reply_text("✅ Thanks for your feedback!")
    bot = Bot(token=BOT_TOKEN)
    for admin_id in ADMIN_IDS:
        await bot.send_message(chat_id=admin_id, text=f"📢 New feedback from @{user.username or user.id}: {msg}")

async def roi(update, context):
    conn = await asyncpg.connect(DATABASE_URL)
    row = await conn.fetchrow('SELECT roi, timestamp, signal_name FROM roi_history ORDER BY id DESC LIMIT 1')
    await conn.close()
    if row:
        await update.message.reply_text(f"📊 Last ROI: {row[0]}% from {row[2]} at {row[1][:16]}")
    else:
        await update.message.reply_text("⏳ No ROI yet")

async def roi_history(update, context):
    rows = await get_roi_history(10)
    if not rows:
        await update.message.reply_text("No ROI history")
        return
    msg = "📈 **Last 10 ROI:**\n"
    for r in rows:
        msg += f"• {r['roi']}% - {r['signal_name']} ({r['timestamp'][:16]})\n"
    await update.message.reply_text(msg, parse_mode="Markdown")

async def price(update, context):
    try:
        r = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd")
        price = r.json()["bitcoin"]["usd"]
        await update.message.reply_text(f"💰 BTC: ${price:,.0f}")
    except:
        await update.message.reply_text("⚠️ Error")

@admin_only
async def status(update, context):
    db_ok = False
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        await conn.execute('SELECT 1')
        await conn.close()
        db_ok = True
    except: pass
    await update.message.reply_text(f"📡 System Status\nPostgreSQL: {'✅' if db_ok else '❌'}\nRedis: {'✅' if REDIS_OK else '❌'}", parse_mode="Markdown")

@admin_only
async def send_alert(update, context):
    if not context.args:
        await update.message.reply_text("/send_alert <message>")
        return
    msg = " ".join(context.args)
    bot = Bot(token=BOT_TOKEN)
    for admin_id in ADMIN_IDS:
        await bot.send_message(chat_id=admin_id, text=f"📢 ALERT: {msg}")
    await update.message.reply_text("✅ Alert sent")

def main():
    import asyncio
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(init_db())
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("feedback", feedback))
    app.add_handler(CommandHandler("roi", roi))
    app.add_handler(CommandHandler("roi_history", roi_history))
    app.add_handler(CommandHandler("price", price))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("send_alert", send_alert))
    app.add_handler(CommandHandler("help", start))
    print("🤖 Bot running with PostgreSQL + Redis")
    app.run_polling()

if __name__ == "__main__":
    main()
