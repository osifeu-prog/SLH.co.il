Ã—Â³Ã‚Â³Ã–Â²Ã‚Å¸Ã—Â²Ã‚Â²Ã–Â²Ã‚Â»Ã—Â²Ã‚Â²Ã–Â²Ã‚Â¿# New commands for bot  English only to avoid encoding issues
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message

router = Router()

@router.message(Command("dashboard"))
async def cmd_dashboard(msg: Message):
    await msg.reply(
        "Ã—Â³Ã‚Â³Ã–Â²Ã‚Â Ã—Â²Ã‚Â²Ã–Â²Ã‚Å¸Ã—Â³Ã¢â‚¬â„¢Ã—â€™Ã¢â‚¬Å¡Ã‚Â¬Ã–Â²Ã‚Å“Ã—Â²Ã‚Â²Ã–Â²Ã‚Å  SLH Autonomous Dashboard\n\n"
        "Ã—Â³Ã‚Â³Ã—â€™Ã¢â€šÂ¬Ã¢â€žÂ¢Ã—Â²Ã‚Â²Ã–Â²Ã‚Å“Ã—Â³Ã¢â‚¬â„¢Ã—â€™Ã¢â‚¬Å¡Ã‚Â¬Ã–Â²Ã‚Â¦ FastAPI: ONLINE\n"
        "Ã—Â³Ã‚Â³Ã—â€™Ã¢â€šÂ¬Ã¢â€žÂ¢Ã—Â²Ã‚Â²Ã–Â²Ã‚Å“Ã—Â³Ã¢â‚¬â„¢Ã—â€™Ã¢â‚¬Å¡Ã‚Â¬Ã–Â²Ã‚Â¦ Bot: ONLINE (@SLH_Claude_bot)\n"
        "Ã—Â³Ã‚Â³Ã—â€™Ã¢â€šÂ¬Ã¢â€žÂ¢Ã—Â²Ã‚Â²Ã–Â²Ã‚Å“Ã—Â³Ã¢â‚¬â„¢Ã—â€™Ã¢â‚¬Å¡Ã‚Â¬Ã–Â²Ã‚Â¦ Agents: Scan, Plan, Code\n"
        "Ã—Â³Ã‚Â³Ã—â€™Ã¢â€šÂ¬Ã¢â€žÂ¢Ã—Â²Ã‚Â²Ã–Â²Ã‚Å“Ã—Â³Ã¢â‚¬â„¢Ã—â€™Ã¢â‚¬Å¡Ã‚Â¬Ã–Â²Ã‚Â¦ Docker: postgres + redis + admin-bot\n\n"
        "Commands: /scan /plan /auto /dashboard"
    )

@router.message(Command("crowdfunding"))
async def cmd_crowdfunding(msg: Message):
    await msg.reply(
        "Ã—Â³Ã‚Â³Ã–Â²Ã‚Â Ã—Â²Ã‚Â²Ã–Â²Ã‚Å¸Ã—Â³Ã¢â‚¬â„¢Ã—â€™Ã¢â‚¬Å¡Ã‚Â¬Ã—â€™Ã¢â‚¬Å¾Ã‚Â¢Ã—Â²Ã‚Â²Ã–Â²Ã‚Â° SLH Crowdfunding Campaign\n\n"
        "We're building an AI that builds itself  and you can be part of it.\n"
        "https://slh-nft.com/crowdfunding\n\n"
        "Ã—Â³Ã‚Â³Ã–Â²Ã‚Â Ã—Â²Ã‚Â²Ã–Â²Ã‚Å¸Ã—Â²Ã‚Â²Ã–Â²Ã‚Å½Ã—Â²Ã‚Â²Ã–Â²Ã‚Â Rewards:\n"
        "Ã—Â³Ã‚Â³Ã—â€™Ã¢â€šÂ¬Ã¢â€žÂ¢Ã—Â³Ã¢â‚¬â„¢Ã—â€™Ã¢â€šÂ¬Ã‚Å¡Ã–Â²Ã‚Â¬Ã—Â²Ã‚Â²Ã–Â²Ã‚Â¢ Supporter ()  Name on website\n"
        "Ã—Â³Ã‚Â³Ã—â€™Ã¢â€šÂ¬Ã¢â€žÂ¢Ã—Â³Ã¢â‚¬â„¢Ã—â€™Ã¢â€šÂ¬Ã‚Å¡Ã–Â²Ã‚Â¬Ã—Â²Ã‚Â²Ã–Â²Ã‚Â¢ Builder ()  Early access + badge\n"
        "Ã—Â³Ã‚Â³Ã—â€™Ã¢â€šÂ¬Ã¢â€žÂ¢Ã—Â³Ã¢â‚¬â„¢Ã—â€™Ã¢â€šÂ¬Ã‚Å¡Ã–Â²Ã‚Â¬Ã—Â²Ã‚Â²Ã–Â²Ã‚Â¢ Founder ()  Vote on features + private Telegram group\n"
        "Ã—Â³Ã‚Â³Ã—â€™Ã¢â€šÂ¬Ã¢â€žÂ¢Ã—Â³Ã¢â‚¬â„¢Ã—â€™Ã¢â€šÂ¬Ã‚Å¡Ã–Â²Ã‚Â¬Ã—Â²Ã‚Â²Ã–Â²Ã‚Â¢ Visionary ()  1-on-1 call + founding member status\n\n"
        "Send TON to:\n"
        "UQCr743gEr_nqV_0SBkSp3CtYS_15R3LDLBvLmKeEv7XdGvp\n"
        "Include TX hash via bot to receive rewards."
    )

# You can add /scan, /plan, /auto here but they rely on local agents  placeholders
@router.message(Command("scan"))
async def cmd_scan(msg: Message):
    await msg.reply("Scanning requires local agent running. Use dashboard or local machine.")

@router.message(Command("plan"))
async def cmd_plan(msg: Message):
    await msg.reply("Planning requires local agent. Use dashboard or local machine.")

@router.message(Command("auto"))
async def cmd_auto(msg: Message):
    await msg.reply("Auto mode requires local agent. Use dashboard or local machine.")


