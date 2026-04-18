import asyncio
import logging
from aiogram import Bot, Dispatcher
from handlers.tamagotchi import register_handlers_tamagotchi, init_db, send_reminders

TOKEN = "7998856873:AAEbgyrdCAWWcjZgt-RvMyLZ9cFIbrHrfSo"

async def main():
    logging.basicConfig(level=logging.INFO)
    init_db()
    bot = Bot(token=TOKEN)
    dp = Dispatcher()
    register_handlers_tamagotchi(dp)
    asyncio.create_task(send_reminders(bot))
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
