from aiogram import Dispatcher

dp = Dispatcher()

def register_handlers():
    from app.bot.handlers.commands.start import start_handler
    dp.message.register(start_handler)