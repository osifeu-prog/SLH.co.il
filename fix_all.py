import shutil, os

# 1. Restore the clean backup (no admin_panel)
shutil.copy("bot.py.final_backup", "bot.py")

with open("bot.py", "r", encoding="utf-8") as f:
    c = f.read()

# 2. Remove BOM
c = c.replace('\ufeff', '')

# 3. Fix ADMIN_IDS  replace spaces with commas, no regex
old = 'ADMIN_IDS = [int(x) for x in os.getenv("ADMIN_ID", "").split(",") if x]'
new = 'ADMIN_IDS = [int(x) for x in os.getenv("ADMIN_ID", "").replace(" ", ",").split(",") if x]'
c = c.replace(old, new)

# 4. Delete any broken upgrade/donate block (from first occurrence to end)
lines = c.split('\n')
idx = None
for i, line in enumerate(lines):
    if '@dp.message(Command("upgrade"))' in line:
        idx = i
        break
if idx is not None:
    lines = lines[:idx]

# 5. Append the correct upgrade/donate/callback block
correct = [
    '',
    '@dp.message(Command("upgrade"))',
    'async def cmd_upgrade(msg: Message):',
    '    await msg.answer("<b>💎 Premium Tiers</b>\\n\\nPro (9.9 TON/mo)  x1.5 multiplier\\nBusiness (29 TON/mo)  x2.0 multiplier", parse_mode="HTML")',
    '',
    '@dp.message(Command("donate"))',
    'async def cmd_donate(msg: Message):',
    '    await msg.answer(f"<b>🤝 Donate to SLH</b>\\nSend TON to:\\n<code>{TON_WALLET}</code>\\nYour ID: <code>{msg.from_user.id}</code>", parse_mode="HTML")',
    '',
    '@dp.callback_query(F.data == "cmd_upgrade")',
    'async def on_upgrade_click(callback: CallbackQuery):',
    '    await callback.answer()',
    '    await cmd_upgrade(callback.message)',
    '',
    '@dp.callback_query(F.data == "cmd_donate")',
    'async def on_donate_click(callback: CallbackQuery):',
    '    await callback.answer()',
    '    await cmd_donate(callback.message)',
    ''
]
lines.extend(correct)
c = '\n'.join(lines)

with open("bot.py", "w", encoding="utf-8") as f:
    f.write(c)

print("✅ bot.py fixed  admin_panel removed, handlers added")
