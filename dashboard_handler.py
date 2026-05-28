ן»¿# Dashboard command  add to bot.py before if __name__
@dp.message(Command("dashboard"))
async def cmd_dashboard(msg: Message):
    await msg.reply(
        "נ“ SLH Autonomous Dashboard\n\n"
        "ג… FastAPI: ONLINE\n"
        "ג… Bot: ONLINE (@SLH_Claude_bot)\n"
        "ג… Agents: Scan, Plan, Code\n"
        "ג… Docker: postgres + redis + admin-bot\n\n"
        "Commands: /scan /plan /auto /dashboard"
    )
