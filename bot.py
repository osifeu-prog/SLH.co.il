import logging
import os
import sys
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime

# Fix for event loop on Windows
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
DATABASE_URL = os.getenv('DATABASE_URL')

def _serve_static_and_exit():
    # Fallback for Railway services that deploy this repo without TELEGRAM_BOT_TOKEN
    # (e.g. the SLH.co.il service, which is meant to serve the website, not run the bot).
    # Without this fallback, those services crash-loop because railway.json's startCommand
    # is shared across all services in the project.
    import http.server
    import socketserver
    port = int(os.getenv('PORT', '8080'))
    docs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'docs')
    if not os.path.isdir(docs_dir):
        logger.error("No TELEGRAM_BOT_TOKEN and docs/ not present — cannot fall back to static serve")
        sys.exit(1)
    os.chdir(docs_dir)
    handler = http.server.SimpleHTTPRequestHandler
    logger.info(f"TELEGRAM_BOT_TOKEN not set — serving {docs_dir} on :{port}")
    with socketserver.TCPServer(('', port), handler) as httpd:
        httpd.serve_forever()

if not TOKEN:
    _serve_static_and_exit()
if not DATABASE_URL:
    logger.error("DATABASE_URL not set")
    sys.exit(1)

def get_db():
    return psycopg2.connect(DATABASE_URL)

def init_db():
    # Schema matches the existing production database on Railway.
    # first_seen and feedback.timestamp are TEXT (ISO-8601) for legacy compatibility.
    conn = None
    cur = None
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id BIGINT PRIMARY KEY,
                username TEXT,
                first_seen TEXT,
                is_admin BOOLEAN DEFAULT FALSE
            )
        ''')
        cur.execute('''
            CREATE TABLE IF NOT EXISTS roi_records (
                id SERIAL PRIMARY KEY,
                user_id BIGINT,
                roi_percentage FLOAT,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        cur.execute('''
            CREATE TABLE IF NOT EXISTS feedback (
                id SERIAL PRIMARY KEY,
                user_id TEXT,
                username TEXT,
                message TEXT,
                timestamp TEXT
            )
        ''')
        conn.commit()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"DB init error: {e}")
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

# Menu functions
def get_main_menu():
    keyboard = [
        [InlineKeyboardButton("💰 ROI", callback_data="menu_roi"),
         InlineKeyboardButton("💬 משוב", callback_data="menu_feedback")],
        [InlineKeyboardButton("📊 סטטוס", callback_data="menu_status"),
         InlineKeyboardButton("🤖 AI", callback_data="menu_ai")],
        [InlineKeyboardButton("📚 תיעוד", callback_data="menu_docs"),
         InlineKeyboardButton("👑 מנהלים", callback_data="menu_admin")]
    ]
    return InlineKeyboardMarkup(keyboard)

# Command handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    now_iso = datetime.utcnow().isoformat()
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute('''
            INSERT INTO users (user_id, username, first_seen)
            VALUES (%s, %s, %s)
            ON CONFLICT (user_id) DO UPDATE
            SET username = EXCLUDED.username
        ''', (user.id, user.username, now_iso))
        conn.commit()
    except Exception as e:
        logger.error(f"Error saving user: {e}")
    finally:
        cur.close()
        conn.close()

    await update.message.reply_text(
        f"🤖 Welcome {user.first_name}!\n\n"
        f"Send /menu to see all commands"
    )

async def menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🔷 **SLH Macro System - תפריט ראשי** 🔷\n\nבחר אפשרות:",
        reply_markup=get_main_menu(),
        parse_mode='Markdown'
    )

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute('SELECT COUNT(*) FROM users')
        user_count = cur.fetchone()[0]
        cur.execute('SELECT COUNT(*) FROM roi_records')
        roi_count = cur.fetchone()[0]
        await update.message.reply_text(
            f"✅ System Online\n\n"
            f"👥 Users: {user_count}\n"
            f"💰 ROI Records: {roi_count}\n"
            f"🤖 Bot: Active"
        )
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")
    finally:
        cur.close()
        conn.close()

async def add_roi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not context.args:
        await update.message.reply_text("Usage: /add_roi 15.5 [description]")
        return
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute('SELECT is_admin FROM users WHERE user_id = %s', (user_id,))
        row = cur.fetchone()
        if not row or not row[0]:
            await update.message.reply_text("❌ Admin only. Use /make_me_admin first")
            return
        roi = float(context.args[0])
        desc = ' '.join(context.args[1:]) if len(context.args) > 1 else "No description"
        cur.execute('''
            INSERT INTO roi_records (user_id, roi_percentage, description)
            VALUES (%s, %s, %s)
        ''', (user_id, roi, desc))
        conn.commit()
        await update.message.reply_text(f"✅ ROI {roi}% added!\n📝 {desc}")
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")
    finally:
        cur.close()
        conn.close()

async def last_roi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        conn = get_db()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute('SELECT roi_percentage, description, created_at FROM roi_records ORDER BY created_at DESC LIMIT 1')
        record = cur.fetchone()
        if record:
            await update.message.reply_text(f"📊 Last ROI: {record['roi_percentage']}%\n📝 {record['description']}")
        else:
            await update.message.reply_text("No ROI records")
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")
    finally:
        cur.close()
        conn.close()

def _save_feedback(user, tagged_message: str):
    """Insert feedback row with all columns populated (matches prod schema)."""
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO feedback (user_id, username, message, timestamp) VALUES (%s, %s, %s, %s)",
            (
                str(user.id),
                user.username or "no_username",
                tagged_message,
                datetime.utcnow().isoformat(),
            ),
        )
        conn.commit()
    finally:
        cur.close()
        conn.close()

async def feedback_ai(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ Usage: /feedback_ai [your feedback]")
        return
    msg = ' '.join(context.args)
    try:
        _save_feedback(update.effective_user, f"[AI] {msg}")
        await update.message.reply_text("✅ Feedback received!\n\n📝 Thank you for your input!")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")

async def suggest(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ Usage: /suggest [your idea]")
        return
    idea = ' '.join(context.args)
    try:
        _save_feedback(update.effective_user, f"[IDEA] {idea}")
        await update.message.reply_text("✅ Thank you! Your idea has been saved.")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")

async def report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ Usage: /report [issue description]")
        return
    issue = ' '.join(context.args)
    try:
        _save_feedback(update.effective_user, f"[BUG] {issue}")
        await update.message.reply_text("✅ Issue reported. We'll handle it soon.")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")

async def summary_today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # first_seen / feedback.timestamp are ISO-8601 text columns; cast to timestamp before DATE().
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            "SELECT COUNT(*) FROM users "
            "WHERE first_seen IS NOT NULL AND first_seen::timestamp::date = CURRENT_DATE"
        )
        new_users = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM roi_records WHERE DATE(created_at) = CURRENT_DATE")
        today_roi = cur.fetchone()[0]
        cur.execute(
            "SELECT COUNT(*) FROM feedback "
            "WHERE timestamp IS NOT NULL AND timestamp::timestamp::date = CURRENT_DATE"
        )
        today_fb = cur.fetchone()[0]
        await update.message.reply_text(
            f"📊 **Daily Summary**\n\n"
            f"👥 New users: {new_users}\n"
            f"💰 ROI records: {today_roi}\n"
            f"💬 Feedback: {today_fb}",
            parse_mode='Markdown'
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")
    finally:
        cur.close()
        conn.close()

async def roadmap(update: Update, context: ContextTypes.DEFAULT_TYPE):
    roadmap_text = """🗺️ **SLH.co.il Roadmap**

✅ **Completed:**
• Telegram bot
• PostgreSQL DB
• ROI system
• Admin rights

🚧 **In Progress:**
• AI feedback analysis
• Monitor dashboard

📅 **Future:**
• Web app
• Public API
• Slack integration"""
    await update.message.reply_text(roadmap_text, parse_mode='Markdown')

async def docs_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Commands wrapped in backticks so Markdown doesn't strip the underscores
    # (Telegram legacy Markdown treats _word_ as italic; backticks = code span, no parsing).
    docs_text = """📚 **SLH.co.il Documentation**

📖 **Commands:**
`/menu` - Main menu
`/status` - System status
`/add_roi` - Add ROI
`/last_roi` - Last ROI
`/feedback_ai` - Smart feedback
`/suggest` - Suggest improvement
`/report` - Report issue
`/summary_today` - Daily summary
`/roadmap` - Roadmap

🌐 **Web:**
• https://www.slh.co.il
• https://monitor.slh.co.il"""
    await update.message.reply_text(docs_text, parse_mode='Markdown')

async def request_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username
    await update.message.reply_text("✅ Admin request sent. An admin will review your request.")

async def make_me_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute('SELECT COUNT(*) FROM users WHERE is_admin = TRUE')
        admin_count = cur.fetchone()[0]
        
        if admin_count == 0:
            cur.execute('UPDATE users SET is_admin = TRUE WHERE user_id = %s', (user_id,))
            conn.commit()
            await update.message.reply_text("✅ You are now an admin! 🎉")
        else:
            await update.message.reply_text("❌ An admin already exists.")
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")
    finally:
        cur.close()
        conn.close()

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "menu_roi":
        await query.edit_message_text("💰 **ROI:**\n`/add_roi` [amount]\n`/last_roi`", parse_mode='Markdown')
    elif query.data == "menu_feedback":
        await query.edit_message_text("💬 **Feedback:**\n`/feedback_ai` [msg]\n`/suggest` [idea]\n`/report` [issue]", parse_mode='Markdown')
    elif query.data == "menu_status":
        await query.edit_message_text("📊 **Status:**\n`/status`", parse_mode='Markdown')
    elif query.data == "menu_ai":
        await query.edit_message_text("🤖 **AI:**\n`/summary_today`\n`/feedback_ai`", parse_mode='Markdown')
    elif query.data == "menu_docs":
        await query.edit_message_text("📚 **Docs:**\n`/roadmap`\n`/docs`", parse_mode='Markdown')
    elif query.data == "menu_admin":
        await query.edit_message_text("👑 **Admin:**\n`/request_admin`\n`/make_me_admin`", parse_mode='Markdown')

async def main():
    logger.info("Starting bot...")
    init_db()
    app = Application.builder().token(TOKEN).build()
    
    # Add handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("menu", menu_command))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("add_roi", add_roi))
    app.add_handler(CommandHandler("last_roi", last_roi))
    app.add_handler(CommandHandler("feedback_ai", feedback_ai))
    app.add_handler(CommandHandler("suggest", suggest))
    app.add_handler(CommandHandler("report", report))
    app.add_handler(CommandHandler("summary_today", summary_today))
    app.add_handler(CommandHandler("roadmap", roadmap))
    app.add_handler(CommandHandler("docs", docs_cmd))
    app.add_handler(CommandHandler("request_admin", request_admin))
    app.add_handler(CommandHandler("make_me_admin", make_me_admin))
    app.add_handler(CallbackQueryHandler(handle_callback))
    
    logger.info("Bot started polling...")
    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
