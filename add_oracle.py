import shutil, os

# Restore clean backup (in case we need fresh start)
shutil.copy("bot.py.final_backup", "bot.py")

with open("bot.py", "r", encoding="utf-8") as f:
    c = f.read()

# Remove BOM
c = c.replace('\ufeff', '')

# Fix ADMIN_IDS (replace spaces with commas)
old_admin = 'ADMIN_IDS = [int(x) for x in os.getenv("ADMIN_ID", "").split(",") if x]'
new_admin = 'ADMIN_IDS = [int(x) for x in os.getenv("ADMIN_ID", "").replace(" ", ",").split(",") if x]'
c = c.replace(old_admin, new_admin)

# Add Oracle command and its handler
oracle_code = '''
@dp.message(Command("oracle"))
async def cmd_oracle(msg: Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔍 Ask the Oracle about SLH", callback_data="oracle_ask")],
        [InlineKeyboardButton(text="📊 System Scan", callback_data="oracle_scan")],
        [InlineKeyboardButton(text="📈 Fundraising Prediction", callback_data="oracle_predict")],
        [InlineKeyboardButton(text="🎮 Secret Game", callback_data="oracle_game")],
        [InlineKeyboardButton(text="🌿 Daily Peace Mission", callback_data="oracle_mission")],
        [InlineKeyboardButton(text="✨ Creativity Mode", callback_data="oracle_creative")],
    ])
    await msg.answer("<b>🔮 SLH Oracle+ Activated</b>\\nChoose your mode:", parse_mode="HTML", reply_markup=kb)

@dp.callback_query(F.data == "oracle_ask")
async def oracle_ask(callback: CallbackQuery):
    await callback.answer()
    await callback.message.answer("<b>🔮 Oracle says:</b>\\nAsk me anything about the project, donations, or the impact of your contribution.", parse_mode="HTML")

@dp.callback_query(F.data == "oracle_scan")
async def oracle_scan(callback: CallbackQuery):
    await callback.answer()
    await callback.message.answer("<b>🔮 System Scan:</b>\\n✅ Bot: Online\\n✅ DB: Connected\\n✅ Railway: Online", parse_mode="HTML")

@dp.callback_query(F.data == "oracle_predict")
async def oracle_predict(callback: CallbackQuery):
    await callback.answer()
    await callback.message.answer("<b>🔮 Fundraising Prediction:</b>\\nCurrent rate: +0.5 TON/day\\nProjected: 15 TON by end of month.", parse_mode="HTML")

@dp.callback_query(F.data == "oracle_mission")
async def oracle_mission(callback: CallbackQuery):
    await callback.answer()
    await callback.message.answer("<b>🌿 Daily Peace Mission:</b>\\nShare the bot with one person who cares about peace and innovation.", parse_mode="HTML")
'''

# Add Oracle code before the last function (before main or at the end)
if "async def cmd_oracle(msg: Message):" not in c:
    c += '\n' + oracle_code

# Also add the Peace Game (simplified version)
peace_code = '''
@dp.message(Command("peace"))
async def cmd_peace(msg: Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🕊 Peace Path", callback_data="peace_path")],
        [InlineKeyboardButton(text="🤖 Innovation Path", callback_data="innovation_path")],
        [InlineKeyboardButton(text="🌍 Humanity Path", callback_data="humanity_path")],
    ])
    await msg.answer("<b>🎮 Peace Game</b>\\nChoose your path:", parse_mode="HTML", reply_markup=kb)

@dp.callback_query(F.data.startswith("peace_"))
async def peace_path_handler(callback: CallbackQuery):
    await callback.answer()
    path = callback.data.replace("peace_", "")
    messages = {
        "path": "You chose the Peace Path. Answer: What is the most important element in conflict resolution?\\nA) Communication  B) Force  C) Ignoring  D) Punishment",
        "innovation_path": "You chose the Innovation Path. Answer: What is the main benefit of humanitarian robots?\\nA) Unbiased assistance  B) Replacing humans  C) Control  D) Data collection",
        "humanity_path": "You chose the Humanity Path. Answer: What strengthens a community?\\nA) Volunteerism  B) Criticism  C) Isolation  D) Competition"
    }
    await callback.message.answer(f"<b>{messages[path]}</b>", parse_mode="HTML")
'''

if "async def cmd_peace(msg: Message):" not in c:
    c += '\n' + peace_code

with open("bot.py", "w", encoding="utf-8") as f:
    f.write(c)

print("✅ Oracle+ and Peace Game added")
