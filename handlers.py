from aiogram import types
from aiogram.filters import Command
import httpx

async def start_cmd(msg: types.Message):
    await msg.answer("שלום! 👋 אני SLH Spark AI\nמצב: Free Unlimited AI (Groq/Gemini)\n/help לכל הפקודות.")

async def menu_cmd(msg: types.Message):
    await msg.answer(
        "📋 SLH Menu\n\n"
        "/crypto - מחירי קריפטו\n"
        "/donate - תרומה למערכת\n"
        "/about - אודות SLH\n"
        "/links - קישורים חשובים\n"
        "/help - עזרה"
    )

async def crypto_cmd(msg: types.Message):
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            r = await client.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum&vs_currencies=usd")
            d = r.json()
            btc = d.get("bitcoin",{}).get("usd","N/A")
            eth = d.get("ethereum",{}).get("usd","N/A")
            await msg.answer(f"BTC: ${btc}  |  ETH: ${eth}")
        except Exception as e:
            await msg.answer(f"Error: {e}")

async def help_cmd(msg: types.Message):
    await msg.answer("/crypto /donate /about /links /menu /start /help")

async def about_cmd(msg: types.Message):
    await msg.answer("SLH Ecosystem - AI + Web3 + Security. slh-nft.com")

async def links_cmd(msg: types.Message):
    await msg.answer("https://slh-nft.com | @SLH_Claude_bot")

def setup(dp, bot_instance=None):
    dp.message.register(start_cmd, Command("start"))
    dp.message.register(menu_cmd, Command("menu"))
    dp.message.register(crypto_cmd, Command("crypto"))
    dp.message.register(help_cmd, Command("help"))
    dp.message.register(about_cmd, Command("about"))
    dp.message.register(links_cmd, Command("links"))
