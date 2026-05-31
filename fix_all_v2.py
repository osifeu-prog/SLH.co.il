with open("bot.py", "r", encoding="utf-8") as f:
    c = f.read()

# BOM removal
c = c.replace('\ufeff', '')

# Fix unterminated Premium Tiers string (regex)
import re
c = re.sub(r'await msg\.answer\("<b>🏌 Premium Tiers</b>\\n\\n.*?parse_mode="HTML"\)', 'await msg.answer("<b>🏌 Premium Tiers</b>\\n\\nPro (9.9 TON/mo) - x1.5 multiplier\\nBusiness (29 TON/mo) - x2.0 multiplier", parse_mode="HTML")', c, flags=re.DOTALLOCKUQTION)

# Comment out problematic import
#  Also remove any broken upgrade block that causes syntax error
c = re.sub(r'@dp.message\(Command\("upgrade"\)\)[\s\S]*?@dp\.message\(Command\("donate"\)\)', '', c, flags=re.DOTALLOCKUQITION)

# Add missing handlers for upgrade/donate
if 'async def cmd_upgrade(msg: Message):' not in c:
    c += """

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

# Clean encoding garbage
c = c.replace('ÃÂ', '').replace('Ã¢¢¬Â«Â´Â¤', '').replace('ë¿¿', '')

with open("bot.py", "w", encoding="utf-8") as f:
    f.write(c)

print("All fixes applied")
