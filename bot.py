import os, requests, asyncpg, json
from datetime import datetime
from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, ContextTypes

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
MASTER_ADMIN_ID = 8789977826
DATABASE_URL = os.getenv("DATABASE_URL")

# ------------------- DB Functions -------------------
async def init_db():
    conn = await asyncpg.connect(DATABASE_URL)
    await conn.execute('''
        CREATE TABLE IF NOT EXISTS admins (
            user_id TEXT PRIMARY KEY,
            added_by TEXT,
            added_at TEXT
        );
        CREATE TABLE IF NOT EXISTS admin_requests (
            user_id TEXT PRIMARY KEY,
            username TEXT,
            requested_at TEXT
        );
    ''')
    await conn.close()

async def is_admin(user_id):
    conn = await asyncpg.connect(DATABASE_URL)
    row = await conn.fetchrow('SELECT user_id FROM admins WHERE user_id = $1', str(user_id))
    await conn.close()
    return row is not None or str(user_id) == str(MASTER_ADMIN_ID)

async def add_admin(admin_id, added_by):
    conn = await asyncpg.connect(DATABASE_URL)
    await conn.execute('INSERT INTO admins (user_id, added_by, added_at) VALUES ($1, $2, $3) ON CONFLICT DO NOTHING', str(admin_id), str(added_by), datetime.now().isoformat())
    await conn.close()

async def remove_admin(admin_id):
    conn = await asyncpg.connect(DATABASE_URL)
    await conn.execute('DELETE FROM admins WHERE user_id = $1', str(admin_id))
    await conn.close()

async def list_admins():
    conn = await asyncpg.connect(DATABASE_URL)
    rows = await conn.fetch('SELECT user_id, added_at FROM admins ORDER BY added_at DESC')
    await conn.close()
    return rows

async def save_request(user_id, username):
    conn = await asyncpg.connect(DATABASE_URL)
    await conn.execute('INSERT INTO admin_requests (user_id, username, requested_at) VALUES ($1, $2, $3) ON CONFLICT (user_id) DO UPDATE SET username = $2, requested_at = $3', str(user_id), username, datetime.now().isoformat())
    await conn.close()

async def get_requests():
    conn = await asyncpg.connect(DATABASE_URL)
    rows = await conn.fetch('SELECT user_id, username, requested_at FROM admin_requests ORDER BY requested_at DESC')
    await conn.close()
    return rows

async def clear_request(user_id):
    conn = await asyncpg.connect(DATABASE_URL)
    await conn.execute('DELETE FROM admin_requests WHERE user_id = $1', str(user_id))
    await conn.close()

# ------------------- Handlers -------------------
async def start(update, context):
    await update.message.reply_text("🤖 SLH Macro Bot\n/request_admin - Request admin access\n/list_admins - List admins\n/status - System status (admin)\n/feedback <msg> - Send feedback")

async def request_admin(update, context):
    user = update.effective_user
    await save_request(user.id, user.username or "no_username")
    bot = Bot(token=BOT_TOKEN)
    await bot.send_message(chat_id=MASTER_ADMIN_ID, text=f"📢 Admin request from @{user.username or user.id} (ID: {user.id})\nUse /approve_admin {user.id} to approve")
    await update.message.reply_text("✅ Request sent to master admin. You will be notified once approved.")

async def approve_admin(update, context):
    if update.effective_user.id != MASTER_ADMIN_ID:
        await update.message.reply_text("⛔ Only master admin can approve.")
        return
    if not context.args:
        await update.message.reply_text("Usage: /approve_admin <user_id>")
        return
    new_admin_id = context.args[0]
    await add_admin(new_admin_id, MASTER_ADMIN_ID)
    await clear_request(new_admin_id)
    await update.message.reply_text(f"✅ User {new_admin_id} is now an admin.")
    bot = Bot(token=BOT_TOKEN)
    await bot.send_message(chat_id=new_admin_id, text="🎉 You are now an admin! Use /status, /users, /send_alert")

async def revoke_admin(update, context):
    if update.effective_user.id != MASTER_ADMIN_ID:
        await update.message.reply_text("⛔ Only master admin can revoke.")
        return
    if not context.args:
        await update.message.reply_text("Usage: /revoke_admin <user_id>")
        return
    await remove_admin(context.args[0])
    await update.message.reply_text(f"✅ User {context.args[0]} is no longer an admin.")

async def list_admins_cmd(update, context):
    if not await is_admin(update.effective_user.id):
        await update.message.reply_text("⛔ Admins only.")
        return
    rows = await list_admins()
    msg = "👑 **Admins:**\n"
    for r in rows:
        msg += f"• {r['user_id']} (added {r['added_at'][:16]})\n"
    await update.message.reply_text(msg, parse_mode="Markdown")

async def requests_list(update, context):
    if update.effective_user.id != MASTER_ADMIN_ID:
        await update.message.reply_text("⛔ Only master admin.")
        return
    rows = await get_requests()
    if not rows:
        await update.message.reply_text("No pending requests.")
        return
    msg = "📋 **Pending admin requests:**\n"
    for r in rows:
        msg += f"• @{r['username']} (ID: {r['user_id']}) at {r['requested_at'][:16]}\n"
    await update.message.reply_text(msg, parse_mode="Markdown")

async def status(update, context):
    if not await is_admin(update.effective_user.id):
        await update.message.reply_text("⛔ Admins only.")
        return
    db_ok = False
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        await conn.execute('SELECT 1')
        await conn.close()
        db_ok = True
    except: pass
    await update.message.reply_text(f"📡 System Status\nPostgreSQL: {'✅' if db_ok else '❌'}\nBot: ✅ Running")

async def users(update, context):
    if not await is_admin(update.effective_user.id):
        await update.message.reply_text("⛔ Admins only.")
        return
    conn = await asyncpg.connect(DATABASE_URL)
    rows = await conn.fetch('SELECT user_id, username, first_seen FROM users ORDER BY first_seen DESC LIMIT 10')
    await conn.close()
    if not rows:
        await update.message.reply_text("No users yet.")
        return
    msg = "👥 **Recent users:**\n"
    for r in rows:
        msg += f"• {r['username'] or r['user_id']} ({r['first_seen'][:16]})\n"
    await update.message.reply_text(msg, parse_mode="Markdown")

async def feedback(update, context):
    if not context.args:
        await update.message.reply_text("Usage: /feedback <message>")
        return
    msg = " ".join(context.args)
    conn = await asyncpg.connect(DATABASE_URL)
    await conn.execute('INSERT INTO feedback (user_id, username, message, timestamp) VALUES ($1, $2, $3, $4)', str(update.effective_user.id), update.effective_user.username or "no_username", msg, datetime.now().isoformat())
    await conn.close()
    await update.message.reply_text("✅ Thanks for your feedback!")
    bot = Bot(token=BOT_TOKEN)
    admins = await list_admins()
    for a in admins:
        await bot.send_message(chat_id=int(a['user_id']), text=f"📢 New feedback from @{update.effective_user.username or update.effective_user.id}: {msg}")


async def signals(update, context):
    """Check trading signals - /signals"""
    if not await is_admin(update.effective_user.id):
        await update.message.reply_text("⛔ Admins only.")
        return
    await update.message.reply_text("🔄 Fetching latest signals...")
    from signals.engine import check_signals
    result = await check_signals()
    if "error" in result:
        await update.message.reply_text(f"❌ Error: {result['error']}")
        return
    msg = f"""📊 **Trading Signals** (BTC: ${result['btc_price']:,.2f})

**RSI:** {result['rsi']} {'(Neutral)' if 30 < result['rsi'] < 70 else '(Extreme!)'}

**MACD:**
• Line: {result['macd']['line']}
• Signal: {result['macd']['signal']}
• Histogram: {result['macd']['histogram']}

**Signals:**
"""
    if result['signals']:
        for s in result['signals']:
            msg += f"\n• **{s['indicator']}:** {s['signal']} ({s['strength']})\n  {s['reason']}"
    else:
        msg += "\n• No active signals"
    
    await update.message.reply_text(msg, parse_mode="Markdown")


async def send_alert(update, context):
    if not await is_admin(update.effective_user.id):
        await update.message.reply_text("⛔ Admins only.")
        return
    if not context.args:
        await update.message.reply_text("Usage: /send_alert <message>")
        return
    msg = " ".join(context.args)
    bot = Bot(token=BOT_TOKEN)
    admins = await list_admins()
    for a in admins:
        await bot.send_message(chat_id=int(a['user_id']), text=f"📢 ALERT: {msg}")
    await update.message.reply_text("✅ Alert sent to all admins.")

# ------------------- Main -------------------
async def main():
    await init_db()
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("request_admin", request_admin))
    app.add_handler(CommandHandler("approve_admin", approve_admin))
    app.add_handler(CommandHandler("revoke_admin", revoke_admin))
    app.add_handler(CommandHandler("list_admins", list_admins_cmd))
    app.add_handler(CommandHandler("requests", requests_list))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("users", users))
    app.add_handler(CommandHandler("feedback", feedback))
    app.add_handler(CommandHandler("send_alert", send_alert))
    print("🤖 Bot running with admin request system")
    await app.run_polling()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())



