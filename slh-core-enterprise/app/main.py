import asyncio
from aiogram import Bot
from aiogram.client.default import DefaultBotProperties

from app.core.config import settings
from app.core.logging import setup_logging
from app.db.pool import init_db
from app.bot.dispatcher import dp, register_handlers

async def main():
    setup_logging()
    await init_db()

    bot = Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=None)
    )

    register_handlers()

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())