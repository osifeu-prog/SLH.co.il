import logging
import os
import sys
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime

# Fix for event loop on Railway/Python 3.11+
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
DATABASE_URL = os.getenv('DATABASE_URL')

if not TOKEN or not DATABASE_URL:
    logger.error("Missing environment variables")
    sys.exit(1)

def get_db():
    return psycopg2.connect(DATABASE_URL)

def init_db():
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id BIGINT PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                is_admin BOOLEAN DEFAULT FALSE,
                registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
                user_id BIGINT,
                message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        logger.info("Database initialized")
    except Exception as e:
        logger.error(f"DB init error: {e}")
    finally:
        cur.close()
        conn.close()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute('''
            INSERT INTO users (user_id, username, first_name)
            VALUES (%s, %s, %s)
            ON CONFLICT (user_id) DO UPDATE
            SET username = %s, first_name = %s
        ''', (user.id, user.username, user.first_name, user.username, user.first_name))
        conn.commit()
    except Exception as e:
        logger.error(f"Error saving user: {e}")
    finally:
        cur.close()
        conn.close()
    
    await update.message.reply_text(
        f"🤖 Welcome {user.first_name}!\n\n"
        f"Commands:\n"
        f"/status - System status\n"
        f"/add_roi <percent> [desc] - Add ROI\n"
        f"/last_roi - Last ROI\n"
        f"/feedback <msg> - Send feedback\n"
        f"/request_admin - Request admin rights"
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
        is_admin = cur.fetchone()
        if not is_admin or not is_admin[0]:
            await update.message.reply_text("❌ Admin only")
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

async def feedback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /feedback <your message>")
        return
    feedback_text = ' '.join(context.args)
    user_id = update.effective_user.id
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute('INSERT INTO feedback (user_id, message) VALUES (%s, %s)', (user_id, feedback_text))
        conn.commit()
        await update.message.reply_text("✅ Thank you for your feedback!")
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")
    finally:
        cur.close()
        conn.close()

async def request_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute('SELECT user_id FROM users WHERE is_admin = TRUE')
        admins = cur.fetchall()
        for admin in admins:
            try:
                await context.bot.send_message(admin[0], f"👑 Admin request from @{username}\nUser ID: {user_id}")
            except:
                pass
        await update.message.reply_text("✅ Admin request sent")
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")
    finally:
        cur.close()
        conn.close()

async def main():
    logger.info("Starting bot...")
    init_db()
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("add_roi", add_roi))
    app.add_handler(CommandHandler("last_roi", last_roi))
    app.add_handler(CommandHandler("feedback", feedback))
    app.add_handler(CommandHandler("request_admin", request_admin))
    logger.info("Bot started polling...")
    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
