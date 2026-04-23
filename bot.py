import asyncio
import sys
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
import logging
import sys
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
import asyncpg
import asyncio
from datetime import datetime
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Database connection
DATABASE_URL = os.environ.get('DATABASE_URL')
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')

if not TELEGRAM_TOKEN:
    logger.error("TELEGRAM_BOT_TOKEN not set!")
    sys.exit(1)

if not DATABASE_URL:
    logger.error("DATABASE_URL not set!")
    sys.exit(1)

async def init_db():
    """Initialize database tables"""
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id BIGINT PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                is_admin BOOLEAN DEFAULT FALSE,
                registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS roi_records (
                id SERIAL PRIMARY KEY,
                user_id BIGINT,
                roi_percentage FLOAT,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS feedback (
                id SERIAL PRIMARY KEY,
                user_id BIGINT,
                message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        logger.info("Database initialized successfully")
    finally:
        await conn.close()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when /start is issued."""
    user = update.effective_user
    await update.message.reply_text(
        f"🤖 שלום {user.first_name}!\n\n"
        f"ברוך הבא לבוט של SLH.co.il\n\n"
        f"פקודות זמינות:\n"
        f"/status - מצב המערכת\n"
        f"/add_roi - הוסף ROI (אדמין)\n"
        f"/last_roi - ROI אחרון\n"
        f"/feedback - שלח משוב\n"
        f"/request_admin - בקש הרשאות אדמין"
    )
    
    # Save user to database
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        await conn.execute('''
            INSERT INTO users (user_id, username, first_name)
            VALUES ($1, $2, $3)
            ON CONFLICT (user_id) DO UPDATE
            SET username = $2, first_name = $3
        ''', user.id, user.username, user.first_name)
    finally:
        await conn.close()

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Check system status"""
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        user_count = await conn.fetchval('SELECT COUNT(*) FROM users')
        roi_count = await conn.fetchval('SELECT COUNT(*) FROM roi_records')
        
        await update.message.reply_text(
            f"📊 **System Status**\n\n"
            f"✅ Bot: Online\n"
            f"✅ Database: Connected\n"
            f"👥 Users: {user_count}\n"
            f"💰 ROI Records: {roi_count}\n"
            f"🕐 Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
    finally:
        await conn.close()

async def add_roi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Add ROI record (admin only)"""
    user_id = update.effective_user.id
    
    # Check if user is admin
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        is_admin = await conn.fetchval('SELECT is_admin FROM users WHERE user_id = $1', user_id)
        
        if not is_admin:
            await update.message.reply_text("❌ You don't have permission to use this command")
            return
        
        if not context.args or len(context.args) < 1:
            await update.message.reply_text("Usage: /add_roi <percentage> [description]")
            return
        
        roi = float(context.args[0])
        description = ' '.join(context.args[1:]) if len(context.args) > 1 else 'No description'
        
        await conn.execute('''
            INSERT INTO roi_records (user_id, roi_percentage, description)
            VALUES ($1, $2, $3)
        ''', user_id, roi, description)
        
        await update.message.reply_text(f"✅ ROI record added: {roi}%\n📝 {description}")
    finally:
        await conn.close()

async def last_roi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show last ROI record"""
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        record = await conn.fetchrow('''
            SELECT roi_percentage, description, created_at
            FROM roi_records
            ORDER BY created_at DESC
            LIMIT 1
        ''')
        
        if record:
            await update.message.reply_text(
                f"📈 **Last ROI Record**\n\n"
                f"💰 ROI: {record['roi_percentage']}%\n"
                f"📝 Description: {record['description']}\n"
                f"🕐 Time: {record['created_at']}"
            )
        else:
            await update.message.reply_text("No ROI records found")
    finally:
        await conn.close()

async def feedback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Collect user feedback"""
    if not context.args:
        await update.message.reply_text("Usage: /feedback <your message>")
        return
    
    feedback_text = ' '.join(context.args)
    user_id = update.effective_user.id
    
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        await conn.execute('''
            INSERT INTO feedback (user_id, message)
            VALUES ($1, $2)
        ''', user_id, feedback_text)
        
        await update.message.reply_text("✅ Thank you for your feedback!")
        
        # Notify admins
        admins = await conn.fetch('SELECT user_id FROM users WHERE is_admin = TRUE')
        for admin in admins:
            try:
                await context.bot.send_message(
                    admin['user_id'],
                    f"📝 New feedback from user {user_id}:\n{feedback_text}"
                )
            except:
                pass
    finally:
        await conn.close()

async def request_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Request admin permissions"""
    user_id = update.effective_user.id
    username = update.effective_user.username
    
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        # Notify existing admins
        admins = await conn.fetch('SELECT user_id FROM users WHERE is_admin = TRUE')
        for admin in admins:
            try:
                await context.bot.send_message(
                    admin['user_id'],
                    f"👑 Admin request from @{username}\n"
                    f"User ID: {user_id}\n"
                    f"To approve: /approve_admin {user_id}"
                )
            except:
                pass
        
        await update.message.reply_text("✅ Admin request sent to current admins")
    finally:
        await conn.close()

async def approve_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Approve admin request (admin only)"""
    caller_id = update.effective_user.id
    
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        is_admin = await conn.fetchval('SELECT is_admin FROM users WHERE user_id = $1', caller_id)
        
        if not is_admin:
            await update.message.reply_text("❌ You don't have permission to use this command")
            return
        
        if not context.args:
            await update.message.reply_text("Usage: /approve_admin <user_id>")
            return
        
        target_id = int(context.args[0])
        
        await conn.execute('UPDATE users SET is_admin = TRUE WHERE user_id = $1', target_id)
        await update.message.reply_text(f"✅ User {target_id} is now an admin")
        
        # Notify new admin
        try:
            await context.bot.send_message(target_id, "🎉 You've been promoted to admin!")
        except:
            pass
    finally:
        await conn.close()

def main():
    """Start the bot"""
    logger.info("Starting bot...")
    
    # Initialize database
    asyncio.run(init_db())
    
    # Create application
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("status", status))
    application.add_handler(CommandHandler("add_roi", add_roi))
    application.add_handler(CommandHandler("last_roi", last_roi))
    application.add_handler(CommandHandler("feedback", feedback))
    application.add_handler(CommandHandler("request_admin", request_admin))
    application.add_handler(CommandHandler("approve_admin", approve_admin))
    
    logger.info("Bot started polling...")
    
    # Start polling
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()

