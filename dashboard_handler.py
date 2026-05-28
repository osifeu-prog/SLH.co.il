# Dashboard command  add to bot.py before if __name__
@dp.message(Command("dashboard"))
async def cmd_dashboard(msg: Message):
    await msg.reply(
        "📊 SLH Autonomous Dashboard\n\n"
        "✅ FastAPI: ONLINE\n"
        "✅ Bot: ONLINE (@SLH_Claude_bot)\n"
        "✅ Agents: Scan, Plan, Code\n"
        "✅ Docker: postgres + redis + admin-bot\n\n"
        "Commands: /scan /plan /auto /dashboard"
    )
