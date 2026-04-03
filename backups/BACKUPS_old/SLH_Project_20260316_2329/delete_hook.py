import asyncio
import os
from dotenv import load_dotenv
from aiogram import Bot

load_dotenv(".env", override=True)

async def main():
    token = os.getenv("BOT_TOKEN")
    print("USING TOKEN:", repr(token))
    bot = Bot(token=token)
    result = await bot.delete_webhook(drop_pending_updates=True)
    print("delete_webhook:", result)
    await bot.session.close()

asyncio.run(main())
