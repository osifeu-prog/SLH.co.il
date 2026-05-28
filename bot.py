# bot.py  SLH Claude entrypoint (fixed)
import asyncio, os, logging, httpx
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.types import Message

load_dotenv()
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
dp = Dispatcher()

# === FINAL STABLE COMMANDS ===
try:
    import points_system
except ImportError:
    points_system = None

# /start  ADDED HERE (AFTER except)
@dp.message(Command("start"))
async def cmd_start(msg: Message):
    await msg.reply(
        "Hello Osif 👋\nI am SLH Claude - your AI assistant.\n💎 Tier: free\n\n"
        "/dashboard - System status\n/crowdfunding - Support\n/points - Points\n"
        "/daily - Daily missions\n/backup - Create backup\n/help - Commands",
        parse_mode=None
    )

@dp.message(Command("dashboard"))
async def cmd_dashboard(msg: Message):
    await msg.reply("SLH Dashboard\nFastAPI: ONLINE\nBot: ONLINE\nhttp://localhost:9000", parse_mode=None)

@dp.message(Command("crowdfunding"))
async def cmd_crowdfunding(msg: Message):
    await msg.reply("SLH Crowdfunding\nhttps://slh-nft.com/campaign/\nTON: UQCr...", parse_mode=None)

@dp.message(Command("points"))
async def cmd_points(msg: Message):
    if points_system:
        user = points_system.get_user(str(msg.from_user.id))
        await msg.reply(f"Points: {user['points']}\nTier: {user['tier'].upper()}", parse_mode=None)
    else:
        await msg.reply("Points system in progress", parse_mode=None)

@dp.message(Command("daily"))
async def cmd_daily(msg: Message):
    await msg.reply("Daily missions:\n/checkin - +5 points", parse_mode=None)

@dp.message(Command("help"))
async def cmd_help(msg: Message):
    await msg.reply("Commands:\n/dashboard\n/crowdfunding\n/points\n/daily\n/backup\n/help", parse_mode=None)

async def main():
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    # include routers etc (existing code)  keep minimal for now
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
