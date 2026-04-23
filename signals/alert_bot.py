import asyncio
import requests
import json
from datetime import datetime
import asyncpg
import os
from telegram import Bot

DATABASE_URL = os.getenv("DATABASE_URL")
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

async def get_admins():
    conn = await asyncpg.connect(DATABASE_URL)
    rows = await conn.fetch('SELECT user_id FROM admins')
    await conn.close()
    return [int(row["user_id"]) for row in rows]

async def send_signal_alert(signal_data):
    """שליחת התראה על אות מסחר לאדמינים"""
    bot = Bot(token=BOT_TOKEN)
    admins = await get_admins()
    
    if not signal_data.get("signals"):
        return
    
    for sig in signal_data["signals"]:
        msg = f"""🔔 **Trading Signal Alert!**

📊 **Indicator:** {sig["indicator"]}
🎯 **Signal:** {sig["signal"]}
💪 **Strength:** {sig["strength"]}
📝 **Reason:** {sig["reason"]}

💰 **BTC Price:** ${signal_data["btc_price"]:,.2f}
📈 **RSI:** {signal_data["rsi"]}
🕐 **Time:** {signal_data["timestamp"][:19]}

⚠️ This is not financial advice. DYOR!
"""
        for admin in admins:
            try:
                await bot.send_message(chat_id=admin, text=msg, parse_mode="Markdown")
            except:
                pass

async def run_signal_engine():
    """הרצת מנוע האותות ושמירה ב-DB"""
    from signals.engine import check_signals, save_signal_to_db
    
    signal_data = await check_signals()
    
    if "error" not in signal_data:
        await save_signal_to_db(signal_data)
        await send_signal_alert(signal_data)
        print(f"✅ Signals saved at {datetime.now()}")
        if signal_data["signals"]:
            print(f"🚨 Signals found: {signal_data['signals']}")
    
    return signal_data

if __name__ == "__main__":
    asyncio.run(run_signal_engine())
