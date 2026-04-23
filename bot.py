import logging
import os
import sys
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Get environment variables
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
DATABASE_URL = os.getenv('DATABASE_URL')

if not TOKEN:
    logger.error("TELEGRAM_BOT_TOKEN not set!")
    sys.exit(1)

if not DATABASE_URL:
    logger.error("DATABASE_URL not set!")
    sys.exit(1)

def get_db_connection():
    """Get database connection"""
    return psycopg2.connect(DATABASE_URL)

def init_db():
    """Initialize database tables"""
    try:
        conn = get_db_connection()
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
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database init error: {e}")
    finally:
        cur.close()
        conn.close()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when /start is issued."""
    user = update.effective_user
    
    # Save user to database
    try:
        conn = get_db_connection()
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
        f"🤖 שלום {user.first_name}!\n\n"
        f"ברוך הבא לבוט של SLH.co.il\n\n"
        f"📋 פקודות זמינות:\n"
        f"/status - מצב המערכת\n"
        f"/last_roi - ROI אחרון\n"
        f"/feedback - שלח משוב\n"
        f"/request_admin - בקש הרשאות אדמין"
    )

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Check system status"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT COUNT(*) FROM users')
        user_count = cur.fetchone()[0]
        cur.execute('SELECT COUNT(*) FROM roi_records')
        roi_count = cur.fetchone()[0]
        
        await update.message.reply_text(
            f"📊 **System Status**\n\n"
            f"✅ Bot: Online\n"
            f"✅ Database: Connected\n"
            f"👥 Users: {user_count}\n"
            f"💰 ROI Records: {roi_count}\n"
            f"🕐 Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
    except Exception as e:
        logger.error(f"Status error: {e}")
        await update.message.reply_text("❌ Error checking status")
    finally:
        cur.close()
        conn.close()

async def last_roi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show last ROI record"""
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute('''
            SELECT roi_percentage, description, created_at
            FROM roi_records
            ORDER BY created_at DESC
            LIMIT 1
        ''')
        record = cur.fetchone()
        
        if record:
            await update.message.reply_text(
                f"📈 **Last ROI Record**\n\n"
                f"💰 ROI: {record['roi_percentage']}%\n"
                f"📝 Description: {record['description']}\n"
                f"🕐 Time: {record['created_at']}"
            )
        else:
            await update.message.reply_text("No ROI records found")
    except Exception as e:
        logger.error(f"Last ROI error: {e}")
        await update.message.reply_text("❌ Error fetching ROI")
    finally:
        cur.close()
        conn.close()

async def feedback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Collect user feedback"""
    if not context.args:
        await update.message.reply_text("Usage: /feedback <your message>")
        return
    
    feedback_text = ' '.join(context.args)
    user_id = update.effective_user.id
    
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('''
            INSERT INTO feedback (user_id, message)
            VALUES (%s, %s)
        ''', (user_id, feedback_text))
        conn.commit()
        
        await update.message.reply_text("✅ Thank you for your feedback!")
    except Exception as e:
        logger.error(f"Feedback error: {e}")
        await update.message.reply_text("❌ Error saving feedback")
    finally:
        cur.close()
        conn.close()

async def request_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Request admin permissions"""
    user_id = update.effective_user.id
    username = update.effective_user.username
    
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Get all admins
        cur.execute('SELECT user_id FROM users WHERE is_admin = TRUE')
        admins = cur.fetchall()
        
        for admin in admins:
            try:
                await context.bot.send_message(
                    admin[0],
                    f"👑 Admin request from @{username}\n"
                    f"User ID: {user_id}"
                )
            except:
                pass
        
        await update.message.reply_text("✅ Admin request sent")
    except Exception as e:
        logger.error(f"Admin request error: {e}")
        await update.message.reply_text("❌ Error sending request")
    finally:
        cur.close()
        conn.close()

async def main():
    """Start the bot"""
    logger.info("Starting bot...")
    
    # Initialize database
    init_db()
    
    # Create application
    application = Application.builder().token(TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("status", status))
    application.add_handler(CommandHandler("last_roi", last_roi))
    application.add_handler(CommandHandler("feedback", feedback))
    application.add_handler(CommandHandler("request_admin", request_admin))
    
    logger.info("Bot started polling...")
    
    # Start polling
    await application.initialize()
    await application.start()
    await application.updater.start_polling()
    
    # Keep the bot running
    await asyncio.Event().wait()

if __name__ == '__main__':
    asyncio.run(main())
