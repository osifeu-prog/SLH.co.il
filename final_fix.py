import shutil, os, re, ast

# Step 1: Restore clean backup
if os.path.exists("bot.py.final_backup"):
    shutil.copy("bot.py.final_backup", "bot.py")

with open("bot.py", "r", encoding="utf-8") as f:
    content = f.read()

# Step 2: Remove BOM
content = content.replace('\ufeff', '')

# Step 3: Remove admin_panel import
content = re.sub(r"^import admin_panel\s*$", "", content, flags=re.MULTILINE)

# Step 4: Remove broken upgrade/donate block (if any)
content = re.sub(r'@dp\.message\(Command\("upgrade"\)\)[\s\S]*?@dp\.message\(Command\("donate"\)\)', "", content, flags=re.DOTALL)

# Step 5: Add missing handlers for upgrade/donate and callbacks
if "async def cmd_upgrade(msg: Message):" not in content:
    content += """

@dp.message(Command("upgrade"))
async def cmd_upgrade(msg: Message):
    await msg.answer("<b>🌎 Premium Tiers</b>\n\nPro (9.9 TON/mo) – x1.5 multiplier\nBusiness (29 TON/mo) – x2.0 multiplier", parse_mode="HTML")

@dp.message(Command("donate"))
async def cmd_donate(msg: Message):
    await msg.answer(f"<b>💴 Donate to SLH</b>\nSend TON to:\n<code>{TON_WALLET}</code>\nYour ID: <code>{msg.from_user.id}</code>", parse_mode="HTML")

@dp.callback_query(F.data == "cmd_upgrade")
async def on_upgrade_click(callback: CallbackQuery):
    await callback.answer()
    await cmd_upgrade(callback.message)

@dp.callback_query(F.data == "cmd_donate")
async def on_donate_click(callback: CallbackQuery):
    await callback.answer()
    await cmd_donate(callback.message)
"""

# Step 6: Clean encoding garbage
content = content.replace('ÃÂ', '').replace('Ã¢¢¬Â«Â´Â¤', '')

with open("bot.py", "w", encoding="utf-8") as f:
    f.write(content)

print("All fixes applied")
