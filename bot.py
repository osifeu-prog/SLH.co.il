import os, requests, asyncpg, redis, json, subprocess, time
from datetime import datetime
from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, ContextTypes

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "8724910039:AAFkZYO_fV5VFdDpzszWHfhYvJRO25b1fDg")
ADMIN_IDS = [int(os.getenv("TELEGRAM_CHAT_ID_OSIF", "584203384")), int(os.getenv("TELEGRAM_CHAT_ID_TZVIKA", "546671882"))]
DATABASE_URL = os.getenv("DATABASE_URL")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
PROJECT_NAME = "SLH.co.il"
GITHUB_REPO = "https://github.com/osifeu-prog/SLH.co.il"
RAILWAY_URL = "https://slhcoil-production.up.railway.app"
DOMAIN = "https://slh.co.il"

# Redis connection
try:
    redis_client = redis.from_url(REDIS_URL)
    redis_client.ping()
    REDIS_OK = True
except:
    REDIS_OK = False
    redis_client = None

# PostgreSQL functions
async def init_db():
    conn = await asyncpg.connect(DATABASE_URL)
    await conn.execute('''
        CREATE TABLE IF NOT EXISTS roi_history (
            id SERIAL PRIMARY KEY, roi REAL, timestamp TEXT, signal_name TEXT
        )
    ''')
    await conn.execute('''
        CREATE TABLE IF NOT EXISTS alerts (
            id SERIAL PRIMARY KEY, message TEXT, timestamp TEXT, sent_to TEXT
        )
    ''')
    await conn.close()

async def save_roi(roi, signal_name="Signal"):
    conn = await asyncpg.connect(DATABASE_URL)
    await conn.execute('INSERT INTO roi_history (roi, timestamp, signal_name) VALUES ($1, $2, $3)',
                       roi, datetime.now().isoformat(), signal_name)
    await conn.close()
    if REDIS_OK:
        redis_client.lpush("roi_history", json.dumps({"roi": roi, "timestamp": datetime.now().isoformat()}))

async def get_roi_history(limit=10):
    conn = await asyncpg.connect(DATABASE_URL)
    rows = await conn.fetch(f'SELECT roi, timestamp, signal_name FROM roi_history ORDER BY id DESC LIMIT {limit}')
    await conn.close()
    return rows

async def save_alert(message, sent_to="admin"):
    conn = await asyncpg.connect(DATABASE_URL)
    await conn.execute('INSERT INTO alerts (message, timestamp, sent_to) VALUES ($1, $2, $3)',
                       message, datetime.now().isoformat(), sent_to)
    await conn.close()

# Admin check decorator
def admin_only(func):
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.effective_user.id not in ADMIN_IDS:
            await update.message.reply_text("⛔ Access denied. Admins only.")
            return
        return await func(update, context)
    return wrapper

# Bot commands
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"🤖 **SLH Macro Bot**\n\n"
        f"📊 `/roi` - Last ROI\n"
        f"💰 `/price` - BTC price\n"
        f"📈 `/roi_history` - Last 10 ROI\n"
        f"🔐 Admin commands: `/status`, `/deploy`, `/logs`, `/send_alert`, `/broadcast`\n\n"
        f"🌐 **Links:**\n"
        f"• Site: {DOMAIN}\n"
        f"• Railway: {RAILWAY_URL}\n"
        f"• GitHub: {GITHUB_REPO}",
        parse_mode="Markdown"
    )

async def roi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = await asyncpg.connect(DATABASE_URL)
    row = await conn.fetchrow('SELECT roi, timestamp, signal_name FROM roi_history ORDER BY id DESC LIMIT 1')
    await conn.close()
    if row:
        await update.message.reply_text(f"📊 Last ROI: {row[0]}% from {row[2]} at {row[1]}")
    else:
        await update.message.reply_text("⏳ No ROI data yet")

async def roi_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    rows = await get_roi_history(10)
    if not rows:
        await update.message.reply_text("No ROI history")
        return
    msg = "📈 **Last 10 ROI records:**\n"
    for r in rows:
        msg += f"• {r['roi']}% — {r['signal_name']} ({r['timestamp'][:16]})\n"
    await update.message.reply_text(msg, parse_mode="Markdown")

async def price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        r = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd")
        price = r.json()["bitcoin"]["usd"]
        # Cache in Redis
        if REDIS_OK:
            redis_client.set("btc_price", price, ex=60)
        await update.message.reply_text(f"💰 Bitcoin: ${price:,.0f}")
    except Exception as e:
        await update.message.reply_text(f"⚠️ Error: {e}")

@admin_only
async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Check DB
    db_ok = False
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        await conn.execute('SELECT 1')
        await conn.close()
        db_ok = True
    except: pass
    
    msg = f"🔧 **System Status**\n"
    msg += f"• PostgreSQL: {'✅' if db_ok else '❌'}\n"
    msg += f"• Redis: {'✅' if REDIS_OK else '❌'}\n"
    msg += f"• Bot: ✅ Running\n"
    msg += f"• Domain: {DOMAIN}\n"
    msg += f"• Railway: {RAILWAY_URL}\n"
    msg += f"• GitHub: {GITHUB_REPO}\n"
    msg += f"• Last deploy: {os.getenv('RAILWAY_DEPLOYMENT_ID', 'N/A')[:8]}\n"
    await update.message.reply_text(msg, parse_mode="Markdown")

@admin_only
async def deploy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔄 Triggering redeploy via GitHub push...")
    # Trigger redeploy by pushing empty commit (requires GitHub token)
    # For now, just notify
    await update.message.reply_text("To redeploy: push to GitHub or restart in Railway dashboard.")

@admin_only
async def send_alert(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /send_alert <message>")
        return
    msg = " ".join(context.args)
    bot = Bot(token=BOT_TOKEN)
    for admin_id in ADMIN_IDS:
        await bot.send_message(chat_id=admin_id, text=f"📢 ADMIN ALERT:\n{msg}")
    await save_alert(msg, "admin")
    await update.message.reply_text("✅ Alert sent to admins")

@admin_only
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /broadcast <message>")
        return
    msg = " ".join(context.args)
    # Here you would fetch all user chat_ids from DB and send
    await update.message.reply_text("📢 Broadcast feature: implement user table first.")

@admin_only
async def logs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📋 Logs: Check Railway dashboard → Deploy Logs")

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await start(update, context)

async def send_roi_alert(roi_percent, signal_name="Signal"):
    message = f"📈 {signal_name}\nROI: {roi_percent:.2f}%"
    bot = Bot(token=BOT_TOKEN)
    for admin_id in ADMIN_IDS:
        await bot.send_message(chat_id=admin_id, text=message)
    await save_roi(roi_percent, signal_name)

def main():
    import asyncio
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(init_db())
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("roi", roi))
    app.add_handler(CommandHandler("roi_history", roi_history))
    app.add_handler(CommandHandler("price", price))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("deploy", deploy))
    app.add_handler(CommandHandler("send_alert", send_alert))
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(CommandHandler("logs", logs))
    app.add_handler(CommandHandler("help", help_cmd))
    print("🤖 Admin bot running with PostgreSQL + Redis")
    app.run_polling()

if __name__ == "__main__":
    main()
