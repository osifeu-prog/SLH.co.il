import os
import requests
import sqlite3
from datetime import datetime
from telegram import Bot
from telegram.ext import Application, CommandHandler

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "8724910039:AAFkZYO_fV5VFdDpzszWHfhYvJRO25b1fDg")
CHAT_ID_OSIF = os.getenv("TELEGRAM_CHAT_ID_OSIF", "584203384")
CHAT_ID_TZVIKA = os.getenv("TELEGRAM_CHAT_ID_TZVIKA", "546671882")

roi_history = []

def save_roi(roi):
    conn = sqlite3.connect("roi.db")
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS roi_history (roi REAL, timestamp TEXT)')
    c.execute('INSERT INTO roi_history VALUES (?, ?)', (roi, datetime.now().isoformat()))
    conn.commit()
    conn.close()

async def start(update, context):
    await update.message.reply_text("🤖 SLH Macro Bot is alive!\n/roi - ROI\n/price - BTC")

async def roi(update, context):
    if roi_history:
        last = roi_history[-1]
        await update.message.reply_text(f"📊 Last ROI: {last['roi']:.2f}%")
    else:
        await update.message.reply_text("⏳ No ROI yet")

async def price(update, context):
    try:
        r = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd")
        price = r.json()["bitcoin"]["usd"]
        await update.message.reply_text(f"💰 Bitcoin: ${price:,.0f}")
    except:
        await update.message.reply_text("⚠️ Error")

async def help_cmd(update, context):
    await update.message.reply_text("/start, /roi, /price")

def send_roi_alert(roi_percent, signal_name="Signal"):
    message = f"📈 {signal_name}\nROI: {roi_percent:.2f}%"
    bot = Bot(token=BOT_TOKEN)
    if CHAT_ID_OSIF:
        bot.send_message(chat_id=CHAT_ID_OSIF, text=message)
    if CHAT_ID_TZVIKA:
        bot.send_message(chat_id=CHAT_ID_TZVIKA, text=message)
    roi_history.append({"roi": roi_percent, "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")})
    save_roi(roi_percent)

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("roi", roi))
    app.add_handler(CommandHandler("price", price))
    app.add_handler(CommandHandler("help", help_cmd))
    print("🤖 Bot running...")
    app.run_polling()

if __name__ == "__main__":
    main()
