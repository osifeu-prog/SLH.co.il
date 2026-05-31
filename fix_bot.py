# fix_bot.py – תיקון /seed + הוספת מערכת מדריכים
with open("bot.py", "r", encoding="utf-8") as f:
    content = f.read()

# 1. תיקון seed – הסרת עמודת plan
old_seed = 'cur.execute("INSERT INTO payments (user_id, amount, plan, status) VALUES (%s,%s,%s,%s), (%s,%s,%s,%s)", (uid, 9.9, "pro", "confirmed", uid, 29, "business", "pending"))'
new_seed = 'cur.execute("INSERT INTO payments (user_id, amount, status) VALUES (%s,%s,%s), (%s,%s,%s)", (uid, 9.9, "confirmed", uid, 29, "pending"))'
if old_seed in content:
    content = content.replace(old_seed, new_seed)
    print("✓ /seed fixed")

# 2. כפתור Guide בתפריט
old_menu = '[InlineKeyboardButton(text="❓ Help", callback_data="cmd_help")]'
new_menu = '[InlineKeyboardButton(text="📖 Guide", callback_data="cmd_guide"), InlineKeyboardButton(text="❓ Help", callback_data="cmd_help")]'
if old_menu in content:
    content = content.replace(old_menu, new_menu)
    print("✓ Guide button added to menu")

# 3. callback router
old_cb = 'elif data == "cmd_help": await cmd_help(msg)'
new_cb = 'elif data == "cmd_guide": await cmd_guide(msg)\n    elif data == "cmd_help": await cmd_help(msg)'
if old_cb in content:
    content = content.replace(old_cb, new_cb)
    print("✓ Guide callback added")

# 4. הוסף פונקציות guide / faq / tutorial
if "# ═══ GUIDE SYSTEM ═══" not in content:
    guide_code = '''
# ═══ GUIDE SYSTEM ═══
@dp.message(Command("guide"))
async def cmd_guide(msg: Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⭐ How to earn points", callback_data="guide_points")],
        [InlineKeyboardButton(text="💎 How to deposit TON", callback_data="guide_deposit")],
        [InlineKeyboardButton(text="🏆 What is Tier?", callback_data="guide_tier")],
        [InlineKeyboardButton(text="📋 All commands", callback_data="cmd_help")],
    ])
    await msg.answer("<b>📖 SLH Guide</b>\\nChoose a topic:", parse_mode="HTML", reply_markup=kb)

@dp.message(Command("faq"))
async def cmd_faq(msg: Message):
    await msg.answer(
        "<b>FAQ</b>\\n\\n"
        "<b>Q: How to earn points?</b>\\n/checkin daily, /tap, complete /tasks\\n\\n"
        "<b>Q: How to deposit TON?</b>\\n/deposit - send TON with your ID in memo\\n\\n"
        "<b>Q: Premium tiers?</b>\\nPro: 9.9 TON/mo (x1.5) | Business: 29 TON/mo (x2.0)\\n\\n"
        "<b>Q: Referrals?</b>\\n/referral - earn +50 pts per friend",
        parse_mode="HTML"
    )

@dp.message(Command("tutorial"))
async def cmd_tutorial(msg: Message):
    await msg.answer(
        "<b>🎓 Tutorial</b>\\n\\n"
        "1. /register - create account\\n"
        "2. /checkin - earn daily points\\n"
        "3. /deposit - add TON\\n"
        "4. /upgrade - unlock premium\\n"
        "5. /task - set your goals\\n\\n"
        "Questions? /support",
        parse_mode="HTML"
    )

@dp.callback_query(F.data.startswith("guide_"))
async def on_guide_topic(callback: CallbackQuery):
    await callback.answer()
    topics = {
        "guide_points": "<b>⭐ Earning Points</b>\\n\\n/checkin – daily (+5 to +35)\\n/tap – tap button (+5 each)\\n/done – complete task (+10)\\n\\nTip: streak bonus stacks up to 7 days!",
        "guide_deposit": "<b>💎 Depositing TON</b>\\n\\n1. Use /deposit to get wallet address\\n2. Send TON from your wallet\\n3. Include your Telegram ID in memo\\n4. Balance updates after confirmation",
        "guide_tier": "<b>🏆 Tier System</b>\\n\\nFREE – x1.0 multiplier\\nPRO (9.9 TON/mo) – x1.5 multiplier\\nBUSINESS (29 TON/mo) – x2.0 multiplier\\n\\nUpgrade: /upgrade",
    }
    await callback.message.answer(topics.get(callback.data, "Unknown topic"), parse_mode="HTML")

'''
    content = content.replace("# ── CALLBACKS ──", guide_code + "\n# ── CALLBACKS ──")
    print("✓ Guide, FAQ, Tutorial functions added")

# שמירה
with open("bot.py", "w", encoding="utf-8", newline="\n") as f:
    f.write(content)

print("\n✅ ALL FIXES APPLIED! bot.py is ready.")