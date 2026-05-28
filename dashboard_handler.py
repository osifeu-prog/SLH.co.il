׳³ֲײ²ֲ»ײ²ֲ¿# Dashboard command  add to bot.py before if __name__
@dp.message(Command("dashboard"))
async def cmd_dashboard(msg: Message):
    await msg.reply(
        "׳³ֲ ײ²ֲ׳’ג‚¬ֲײ²ֲ SLH Autonomous Dashboard\n\n"
        "׳³ג€™ײ²ֲ׳’ג‚¬ֲ¦ FastAPI: ONLINE\n"
        "׳³ג€™ײ²ֲ׳’ג‚¬ֲ¦ Bot: ONLINE (@SLH_Claude_bot)\n"
        "׳³ג€™ײ²ֲ׳’ג‚¬ֲ¦ Agents: Scan, Plan, Code\n"
        "׳³ג€™ײ²ֲ׳’ג‚¬ֲ¦ Docker: postgres + redis + admin-bot\n\n"
        "Commands: /scan /plan /auto /dashboard"
    )
