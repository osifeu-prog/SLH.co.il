×³Â³Ö²ÂŸ×²Â²Ö²Â»×²Â²Ö²Â¿# Dashboard command  add to bot.py before if __name__
@dp.message(Command("dashboard"))
async def cmd_dashboard(msg: Message):
    await msg.reply(
        "×³Â³Ö²Â ×²Â²Ö²ÂŸ×³â€™×’â€šÂ¬Ö²Âœ×²Â²Ö²ÂŠ SLH Autonomous Dashboard\n\n"
        "×³Â³×’â‚¬â„¢×²Â²Ö²Âœ×³â€™×’â€šÂ¬Ö²Â¦ FastAPI: ONLINE\n"
        "×³Â³×’â‚¬â„¢×²Â²Ö²Âœ×³â€™×’â€šÂ¬Ö²Â¦ Bot: ONLINE (@SLH_Claude_bot)\n"
        "×³Â³×’â‚¬â„¢×²Â²Ö²Âœ×³â€™×’â€šÂ¬Ö²Â¦ Agents: Scan, Plan, Code\n"
        "×³Â³×’â‚¬â„¢×²Â²Ö²Âœ×³â€™×’â€šÂ¬Ö²Â¦ Docker: postgres + redis + admin-bot\n\n"
        "Commands: /scan /plan /auto /dashboard"
    )
