×³Â³Ö²ÂŸ×²Â²Ö²Â»×²Â²Ö²Â¿# New commands for bot  English only to avoid encoding issues
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message

router = Router()

@router.message(Command("dashboard"))
async def cmd_dashboard(msg: Message):
    await msg.reply(
        "×³Â³Ö²Â ×²Â²Ö²ÂŸ×³â€™×’â€šÂ¬Ö²Âœ×²Â²Ö²ÂŠ SLH Autonomous Dashboard\n\n"
        "×³Â³×’â‚¬â„¢×²Â²Ö²Âœ×³â€™×’â€šÂ¬Ö²Â¦ FastAPI: ONLINE\n"
        "×³Â³×’â‚¬â„¢×²Â²Ö²Âœ×³â€™×’â€šÂ¬Ö²Â¦ Bot: ONLINE (@SLH_Claude_bot)\n"
        "×³Â³×’â‚¬â„¢×²Â²Ö²Âœ×³â€™×’â€šÂ¬Ö²Â¦ Agents: Scan, Plan, Code\n"
        "×³Â³×’â‚¬â„¢×²Â²Ö²Âœ×³â€™×’â€šÂ¬Ö²Â¦ Docker: postgres + redis + admin-bot\n\n"
        "Commands: /scan /plan /auto /dashboard"
    )

@router.message(Command("crowdfunding"))
async def cmd_crowdfunding(msg: Message):
    await msg.reply(
        "×³Â³Ö²Â ×²Â²Ö²ÂŸ×³â€™×’â€šÂ¬×’â€žÂ¢×²Â²Ö²Â° SLH Crowdfunding Campaign\n\n"
        "We're building an AI that builds itself  and you can be part of it.\n"
        "https://slh-nft.com/crowdfunding\n\n"
        "×³Â³Ö²Â ×²Â²Ö²ÂŸ×²Â²Ö²ÂŽ×²Â²Ö²Â Rewards:\n"
        "×³Â³×’â‚¬â„¢×³â€™×’â‚¬ÂšÖ²Â¬×²Â²Ö²Â¢ Supporter ()  Name on website\n"
        "×³Â³×’â‚¬â„¢×³â€™×’â‚¬ÂšÖ²Â¬×²Â²Ö²Â¢ Builder ()  Early access + badge\n"
        "×³Â³×’â‚¬â„¢×³â€™×’â‚¬ÂšÖ²Â¬×²Â²Ö²Â¢ Founder ()  Vote on features + private Telegram group\n"
        "×³Â³×’â‚¬â„¢×³â€™×’â‚¬ÂšÖ²Â¬×²Â²Ö²Â¢ Visionary ()  1-on-1 call + founding member status\n\n"
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
