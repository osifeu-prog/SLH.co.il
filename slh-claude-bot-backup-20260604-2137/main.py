import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.client.default import DefaultBotProperties
from core.config import Config
from core.db import init_db
from features import register_all_features

bot = Bot(token=Config.BOT_TOKEN, default=DefaultBotProperties(parse_mode=None))
dp = Dispatcher()

# Callback handler גלובלי
@dp.callback_query()
async def global_callback(call: types.CallbackQuery):
    await call.answer()
    data = call.data
    if data == "status":
        from features.rewards import cmd_status
        await cmd_status(call.message)
    elif data == "points":
        from features.rewards import cmd_points
        await cmd_points(call.message)
    elif data == "checkin":
        from features.rewards import cmd_checkin
        await cmd_checkin(call.message)
    elif data == "tap":
        from features.rewards import cmd_tap
        await cmd_tap(call.message)
    elif data == "upgrade":
        from features.premium import cmd_upgrade
        await cmd_upgrade(call.message)
    elif data == "donate":
        from features.premium import cmd_donate
        await cmd_donate(call.message)
    else:
        await call.message.answer("פקודה לא מוכרת")

async def ai_fallback(msg: types.Message):
    if msg.text.startswith('/'):
        return
    from core.config import Config
    import httpx
    await bot.send_chat_action(msg.chat.id, "typing")
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {Config.GROQ_API_KEY}"},
                json={"model": "llama3-8b-8192", "messages": [{"role": "user", "content": msg.text}], "max_tokens": 300}
            )
            reply = resp.json()["choices"][0]["message"]["content"]
            await msg.answer(reply[:2000])
    except Exception as e:
        await msg.answer(f"⚠️ שגיאת AI: {str(e)[:100]}")

dp.message()(ai_fallback)

async def main():
    await init_db()
    register_all_features(dp)
    await bot.delete_webhook(drop_pending_updates=True)
    print("🚀 SLH Spark AI v4.5 - מודולרי, עם 40+ פקודות")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
