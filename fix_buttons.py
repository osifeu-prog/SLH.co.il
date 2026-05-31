with open("bot.py", "r", encoding="utf-8") as f:
    c = f.read()

# 1. Remove duplicate last_seen line
c = c.replace(
    "ALTER TABLE users ADD COLUMN IF NOT EXISTS last_seen TIMESTAMP DEFAULT NOW();\n                ALTER TABLE users ADD COLUMN IF NOT EXISTS last_seen TIMESTAMP DEFAULT NOW();",
    "ALTER TABLE users ADD COLUMN IF NOT EXISTS last_seen TIMESTAMP DEFAULT NOW();"
)

# 2. Replace the broken on_callback function with a complete one
old = "@dp.callback_query()\nasync def on_callback(callback: CallbackQuery):"
new = """@dp.callback_query()
async def on_callback(callback: CallbackQuery):
    await callback.answer()
    data = callback.data; msg = callback.message
    if data == "cmd_status": await cmd_status(msg)
    elif data == "cmd_points": await cmd_points(msg)
    elif data == "cmd_checkin": await cmd_checkin(msg)
    elif data == "cmd_upgrade": await cmd_upgrade(msg)
    elif data == "cmd_donate": await cmd_donate(msg)
    elif data == "cmd_crypto": await cmd_crypto(msg)
    elif data == "cmd_dashboard": await cmd_dashboard(msg)
    elif data == "cmd_guide": await cmd_guide(msg)
    elif data == "cmd_help": await cmd_help(msg)
    elif data == "cmd_tap": await cmd_tap(msg)
    else: await msg.answer(f"Button: {data}")"""

c = c.replace(old, new)

# 3. Add dummy cmd_upgrade / cmd_donate if they don't exist
if "async def cmd_upgrade(msg: Message):" not in c:
    c += """
@dp.message(Command("upgrade"))
async def cmd_upgrade(msg: Message):
    await msg.answer("<b>🌎 Premium Tiers</b>\\n\\nPro (9.9 TON/mo) – x1.5 multiplier\\nBusiness (29 TON/mo) – x2.0 multiplier", parse_mode="HTML")

@dp.message(Command("donate"))
async def cmd_donate(msg: Message):
    await msg.answer(f"<b>💄 Donate</b>\\nSend TON to:\\n<code>{TON_WALLET}</code>\\nYour ID: <code>{msg.from_user.id}</code>", parse_mode="HTML")
"""

with open("bot.py", "w", encoding="utf-8") as f:
    f.write(c)

print("🄅 bot.py patched")