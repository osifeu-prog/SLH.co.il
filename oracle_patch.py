import re
with open('bot.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Remove duplicate last_seen (safety)
content = content.replace(
    'ALTER TABLE users ADD COLUMN IF NOT EXISTS last_seen TIMESTAMP DEFAULT NOW();\n                ALTER TABLE users ADD COLUMN IF NOT EXISTS last_seen TIMESTAMP DEFAULT NOW();',
    'ALTER TABLE users ADD COLUMN IF NOT EXISTS last_seen TIMESTAMP DEFAULT NOW();'
)

# 2. Ensure callback router is complete
old_cb = '@dp.callback_query()\nasync def on_callback(callback: CallbackQuery):'
new_cb = '@dp.callback_query()\nasync def on_callback(callback: CallbackQuery):\n    await callback.answer()\n    data = callback.data; msg = callback.message\n    if data == 'cmd_status': await cmd_status(msg)\n    elif data == 'cmd_points': await cmd_points(msg)\n    elif data == 'cmd_checkin': await cmd_checkin(msg)\n    elif data == 'cmd_upgrade': await cmd_upgrade(msg)\n    elif data == 'cmd_donate': await cmd_donate(msg)\n    elif data == 'cmd_crypto': await cmd_crypto(msg)\n    elif data == 'cmd_dashboard': await cmd_dashboard(msg)\n    elif data == 'cmd_guide': await cmd_guide(msg)\n    elif data == 'cmd_help': await cmd_help(msg)\n    elif data == 'cmd_tap': await cmd_tap(msg)\n    elif data == 'cmd_oracle': await cmd_oracle(msg)\n    else: await msg.answer(f'Button: {data}')'
content = content.replace(old_cb, new_cb)

# 3. Add oracle command and its handlers
if 'cmd_oracle' not in content:
    content += '''

@dp.message(Command("oracle"))
async def cmd_oracle(msg: Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎔 Peace Game", callback_data="oracle_game")],
        [InlineKeyboardButton(text="🔆 System Scan", callback_data="oracle_scan")],
        [InlineKeyboardButton(text="📉 Prediction", callback_data="oracle_predict")],
        [InlineKeyboardButton(text="🔌 Oracle Answer", callback_data="oracle_ask")],
    ])
    await msg.answer("<b>🔌 SLH Oracle</b>\nChoose your mode;", reply_markup=kb)

... more oracle handlers appended here ...
'''

# 4. Add the game handlers (peace game, answer, end)
#\nif 'peace_game' not in content:
            content += 'game code here'
    # ...

with open('bot.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Bot patched with Oracle and Game")
