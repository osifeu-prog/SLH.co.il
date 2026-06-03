import random
from aiogram import types, F
from aiogram.filters import Command
from aiogram.types import Message

user_guesses = {}

def register_game(dp):
    @dp.message(Command("game"))
    async def cmd_game(msg: Message):
        uid = msg.from_user.id
        secret = random.randint(1, 20)
        user_guesses[uid] = secret
        await msg.answer("🎲 **Guess the Number!**\nNumber between 1 and 20.\nSend /guess <number>\nCorrect guess wins **50 points**!")

    @dp.message(Command("guess"))
    async def cmd_guess(msg: Message):
        parts = msg.text.split()
        if len(parts) < 2:
            await msg.answer("Usage: /guess 7")
            return
        try:
            guess = int(parts[1])
        except:
            await msg.answer("Invalid number")
            return
        uid = msg.from_user.id
        if uid not in user_guesses:
            await msg.answer("Start a game with /game first")
            return
        secret = user_guesses.pop(uid)
        if guess == secret:
            from bot import pool
            async with pool.acquire() as conn:
                await conn.execute("UPDATE users SET points = points + 50 WHERE telegram_id = ", uid)
                pts = await conn.fetchval("SELECT points FROM users WHERE telegram_id = ", uid)
            await msg.answer(f"🎉 Correct! +50 points. Total: {pts}")
        else:
            hint = "too low" if guess < secret else "too high"
            await msg.answer(f"❌ Wrong: {guess} is {hint}. The number was {secret}.")
