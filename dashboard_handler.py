Ã—Â³Ã‚Â³Ã–Â²Ã‚Å¸Ã—Â²Ã‚Â²Ã–Â²Ã‚Â»Ã—Â²Ã‚Â²Ã–Â²Ã‚Â¿# Dashboard command  add to bot.py before if __name__
@dp.message(Command("dashboard"))
async def cmd_dashboard(msg: Message):
    await msg.reply(
        "Ã—Â³Ã‚Â³Ã–Â²Ã‚Â Ã—Â²Ã‚Â²Ã–Â²Ã‚Å¸Ã—Â³Ã¢â‚¬â„¢Ã—â€™Ã¢â‚¬Å¡Ã‚Â¬Ã–Â²Ã‚Å“Ã—Â²Ã‚Â²Ã–Â²Ã‚Å  SLH Autonomous Dashboard\n\n"
        "Ã—Â³Ã‚Â³Ã—â€™Ã¢â€šÂ¬Ã¢â€žÂ¢Ã—Â²Ã‚Â²Ã–Â²Ã‚Å“Ã—Â³Ã¢â‚¬â„¢Ã—â€™Ã¢â‚¬Å¡Ã‚Â¬Ã–Â²Ã‚Â¦ FastAPI: ONLINE\n"
        "Ã—Â³Ã‚Â³Ã—â€™Ã¢â€šÂ¬Ã¢â€žÂ¢Ã—Â²Ã‚Â²Ã–Â²Ã‚Å“Ã—Â³Ã¢â‚¬â„¢Ã—â€™Ã¢â‚¬Å¡Ã‚Â¬Ã–Â²Ã‚Â¦ Bot: ONLINE (@SLH_Claude_bot)\n"
        "Ã—Â³Ã‚Â³Ã—â€™Ã¢â€šÂ¬Ã¢â€žÂ¢Ã—Â²Ã‚Â²Ã–Â²Ã‚Å“Ã—Â³Ã¢â‚¬â„¢Ã—â€™Ã¢â‚¬Å¡Ã‚Â¬Ã–Â²Ã‚Â¦ Agents: Scan, Plan, Code\n"
        "Ã—Â³Ã‚Â³Ã—â€™Ã¢â€šÂ¬Ã¢â€žÂ¢Ã—Â²Ã‚Â²Ã–Â²Ã‚Å“Ã—Â³Ã¢â‚¬â„¢Ã—â€™Ã¢â‚¬Å¡Ã‚Â¬Ã–Â²Ã‚Â¦ Docker: postgres + redis + admin-bot\n\n"
        "Commands: /scan /plan /auto /dashboard"
    )


