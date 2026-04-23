import os
import requests
import asyncpg
from datetime import datetime
from telegram import Bot
from telegram.ext import Application, CommandHandler

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "8724910039:AAFkZYO_fV5VFdDpzszWHfhYvJRO25b1fDg")
CHAT_ID_OSIF = os.getenv("TELEGRAM_CHAT_ID_OSIF", "584203384")
CHAT_ID_TZVIKA = os.getenv("TELEGRAM_CHAT_ID_TZVIKA", "546671882")
DATABASE_URL = os.getenv("DATABASE_URL")

async def init_db():
    conn = await asyncpg.connect(DATABASE_URL)
    await conn.execute('''
        CREATE TABLE IF NOT EXISTS roi_history (
            id SERIAL PRIMARY KEY,
            roi REAL,
            timestamp TEXT,
            signal_name TEXT
        )
    ''')
    await conn.close()

async def save_roi(roi, signal_name="Signal"):
    conn = await asyncpg.connect(DATABASE_URL)
    await conn.execute(
        'INSERT INTO roi_history (roi, timestamp, signal_name) VALUES ($1, $2, $3)',
        roi, datetime.now().isoformat(), signal_name
    )
    await conn.close()

async def start(update, context):
    await update.message.reply_text("🤖 SLH Macro Bot is alive!\n/roi - Show ROI\n/price - BTC\n/help - Help")

async def roi(update, context):
    conn = await asyncpg.connect(DATABASE_URL)
    row = await conn.fetchrow('SELECT roi, timestamp, signal_name FROM roi_history ORDER BY id DESC LIMIT 1')
    await conn.close()
    if row:
        await update.message.reply_text(f"📊 Last ROI: {row[0]}% from {row[2]} at {row[1]}")
    else:
        await update.message.reply_text("⏳ No ROI data yet")

async def price(update, context):
    try:
        r = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd")
        price = r.json()["bitcoin"]["usd"]
        await update.message.reply_text(f"💰 Bitcoin: ${price:,.0f}")
    except:
        await update.message.reply_text("⚠️ Error fetching price")

async def help_cmd(update, context):
    await update.message.reply_text("/start\n/roi\n/price")

async def send_roi_alert(roi_percent, signal_name="Signal"):
    message = f"📈 {signal_name}\nROI: {roi_percent:.2f}%"
    bot = Bot(token=BOT_TOKEN)
    if CHAT_ID_OSIF:
        await bot.send_message(chat_id=CHAT_ID_OSIF, text=message)
    if CHAT_ID_TZVIKA:
        await bot.send_message(chat_id=CHAT_ID_TZVIKA, text=message)
    await save_roi(roi_percent, signal_name)

async def main():
    await init_db()
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("roi", roi))
    app.add_handler(CommandHandler("price", price))
    app.add_handler(CommandHandler("help", help_cmd))
    print("🤖 Bot running with PostgreSQL")
    await app.run_polling()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
