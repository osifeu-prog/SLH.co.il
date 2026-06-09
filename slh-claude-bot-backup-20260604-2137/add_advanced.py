import re, os

with open("bot.py", "r", encoding="utf-8") as f:
    c = f.read()

# â”€â”€â”€ 1. GUIDE ×ž×•×¨×—×‘ â”€â”€â”€
old_guide = '''@dp.message(Command("guide"))
async def cmd_guide(message: types.Message):
    kb = InlineKeyboardBuilder()
    kb.row(types.InlineKeyboardButton(text="â­ Earning Points", callback_data="guide_points"))
    kb.row(types.InlineKeyboardButton(text="ðŸ’Ž TON Deposits", callback_data="guide_deposit"))
    kb.row(types.InlineKeyboardButton(text="ðŸ† Tiers", callback_data="guide_tier"))
    kb.row(types.InlineKeyboardButton(text="â“ All Commands", callback_data="help"))
    kb.row(types.InlineKeyboardButton(text="â†©ï¸ Main Menu", callback_data="start"))
    await message.answer("ðŸ“– SLH Guide - Choose topic:", reply_markup=kb.as_markup())'''

new_guide = '''@dp.message(Command("guide"))
async def cmd_guide(message: types.Message):
    kb = InlineKeyboardBuilder()
    kb.row(types.InlineKeyboardButton(text="â­ Earning Points", callback_data="guide_points"))
    kb.row(types.InlineKeyboardButton(text="ðŸ’Ž TON Deposits", callback_data="guide_deposit"))
    kb.row(types.InlineKeyboardButton(text="ðŸ† Tiers", callback_data="guide_tier"))
    kb.row(types.InlineKeyboardButton(text="ðŸ‘¥ VIP Groups", callback_data="guide_vip"))
    kb.row(types.InlineKeyboardButton(text="ðŸ“ˆ Trading Signals", callback_data="guide_signals"))
    kb.row(types.InlineKeyboardButton(text="â“ All Commands", callback_data="help"))
    kb.row(types.InlineKeyboardButton(text="â†©ï¸ Main Menu", callback_data="start"))
    await message.answer("ðŸ“– SLH Guide - Choose topic:", reply_markup=kb.as_markup())'''

c = c.replace(old_guide, new_guide)

# â”€â”€â”€ 2. GUIDE CALLBACK ×ž×•×¨×—×‘ â”€â”€â”€
old_guide_cb = '''@dp.callback_query(F.data.startswith("guide_"))
async def guide_callback(callback: types.CallbackQuery):
    d = callback.data
    topics = {"guide_points":"â­ Earn points: /checkin daily, /tap, complete tasks.","guide_deposit":"ðŸ’Ž Deposit TON: send TON to the wallet with your Telegram ID in memo.","guide_tier":"ðŸ† Tiers: Free (x1.0), Pro (9.9 TON) x1.5, Business (29 TON) x2.0."}
    await callback.message.answer(topics.get(d, "Unknown"))
    await callback.answer()'''

new_guide_cb = '''@dp.callback_query(F.data.startswith("guide_"))
async def guide_callback(callback: types.CallbackQuery):
    d = callback.data
    topics = {
        "guide_points": "â­ <b>Earn Points</b>\n\nâ€¢ /checkin  Daily check-in (+10-24 pts)\nâ€¢ /tap  Tap-to-Earn (coming soon)\nâ€¢ /simdeposit  Try TON wallet\nâ€¢ /referral  Invite friends (+50 pts each)",
        "guide_deposit": "ðŸ’Ž <b>TON Deposits</b>\n\n1. Send any amount of TON to:\n<code>UQCr743gEr_nqV_0SBkSp3CtYS_15R3LDLBvLmKeEv7XdGvp</code>\n2. In the memo, put your Telegram ID\n3. Wait ~1 minute  you'll get a confirmation!",
        "guide_tier": "ðŸ† <b>Tiers</b>\n\nâ€¢ FREE  x1.0 multiplier\nâ€¢ PRO  9.9 TON/month  x1.5\nâ€¢ BUSINESS  29 TON/month  x2.0\n\nUpgrade automatically when you deposit enough TON!",
        "guide_vip": "ðŸ‘¥ <b>VIP Groups</b>\n\nâ€¢ Free Community: https://t.me/+HIzvM8sEgh1kNWY0\nâ€¢ VIP Trading (18 ): https://t.me/+KLKB9-JdO85kNWJk\n\nVIP includes:\nðŸ“ˆ Daily trading signals\nðŸ’¬ Private chat\nðŸŽ Exclusive rewards\n\nTo join VIP: send 18  worth of TON to the wallet with your ID, then use /vip",
        "guide_signals": "ðŸ“ˆ <b>Trading Signals</b>\n\nVIP members receive:\nâ€¢ Daily market analysis\nâ€¢ Entry/exit points\nâ€¢ Risk management tips\nâ€¢ Portfolio suggestions\n\nJoin VIP: /vip"
    }
    await callback.message.answer(topics.get(d, "Unknown"), parse_mode="HTML", disable_web_page_preview=True)
    await callback.answer()'''

c = c.replace(old_guide_cb, new_guide_cb)

# â”€â”€â”€ 3. VIP â”€â”€â”€
vip_code = '''
@dp.message(Command("vip"))
async def cmd_vip(msg):
    await msg.answer(
        "ðŸ’Ž <b>SLH VIP Group</b>\\n\\n"
        "ðŸ”’ <b>Private Trading Community</b>\\n"
        "ðŸ’° Cost: <b>18 </b> (one-time)\\n\\n"
        "<b>What you get:</b>\\n"
        "ðŸ“ˆ Daily trading signals (crypto & stocks)\\n"
        "ðŸ’¬ Private chat with experts\\n"
        "ðŸŽ Exclusive rewards & airdrops\\n"
        "ðŸ›¡ Priority support\\n\\n"
        "<b>How to join:</b>\\n"
        "1. Send 18  worth of TON to:\\n"
        "<code>UQCr743gEr_nqV_0SBkSp3CtYS_15R3LDLBvLmKeEv7XdGvp</code>\\n"
        "2. In memo, write: <code>VIP</code> + your Telegram ID\\n"
        "3. You'll receive an invite link automatically!\\n\\n"
        "Already paid? Use /vipstatus to check.",
        parse_mode="HTML"
    )

@dp.message(Command("vipstatus"))
async def cmd_vipstatus(msg):
    await msg.answer("ðŸ” <b>VIP Status:</b>\\nSoon we will show your payment status here.")
'''
if "/vip" not in c:
    c += vip_code

# â”€â”€â”€ 4. CRM â”€â”€â”€
crm_code = '''
@dp.message(Command("crm"))
async def cmd_crm(msg):
    await msg.answer(
        "ðŸ“‡ <b>SLH CRM</b>\\n\\n"
        "Manage your customers:\\n"
        "/addcustomer <name> <phone>  Add a customer\\n"
        "/customers  List your customers\\n"
        "/addnote <customer_id> <text>  Add a note\\n"
        "/notes <customer_id>  View notes",
        parse_mode="HTML"
    )

@dp.message(Command("addcustomer"))
async def cmd_addcustomer(message: types.Message):
    parts = message.text.split(" ", 2)
    if len(parts) < 3:
        return await message.answer("Usage: /addcustomer <name> <phone>")
    name, phone = parts[1], parts[2]
    async with pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO crm_notes (user_id, note) VALUES ($1, $2)",
            message.from_user.id,
            f"CUSTOMER: {name} | PHONE: {phone}"
        )
    await message.answer(f"âœ… Customer {name} added!")

@dp.message(Command("customers"))
async def cmd_customers(message: types.Message):
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT id, note, created_at FROM crm_notes WHERE user_id=$1 AND note LIKE 'CUSTOMER:%' ORDER BY created_at DESC LIMIT 20",
            message.from_user.id
        )
        if not rows:
            return await message.answer("No customers yet.")
        text = "ðŸ“‡ <b>Your Customers:</b>\\n\\n"
        for i, r in enumerate(rows, 1):
            text += f"{i}. {r['note']} | {r['created_at'].strftime('%d/%m/%Y')}\\n"
        await message.answer(text, parse_mode="HTML")

@dp.message(Command("addnote"))
async def cmd_addnote(message: types.Message):
    parts = message.text.split(" ", 2)
    if len(parts) < 3:
        return await message.answer("Usage: /addnote <customer_id> <text>")
    cid, note = parts[1], parts[2]
    async with pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO crm_notes (user_id, note) VALUES ($1, $2)",
            message.from_user.id,
            f"NOTE:{cid}:{note}"
        )
    await message.answer("âœ… Note added.")

@dp.message(Command("notes"))
async def cmd_notes(message: types.Message):
    parts = message.text.split(" ", 1)
    if len(parts) < 2:
        return await message.answer("Usage: /notes <customer_id>")
    cid = parts[1]
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT note, created_at FROM crm_notes WHERE user_id=$1 AND note LIKE $2 ORDER BY created_at DESC LIMIT 10",
            message.from_user.id,
            f"NOTE:{cid}:%"
        )
        if not rows:
            return await message.answer("No notes for this customer.")
        text = f"ðŸ“ <b>Notes for customer {cid}:</b>\\n\\n"
        for r in rows:
            note_text = r['note'].split(":", 2)[-1]
            text += f"[{r['created_at'].strftime('%d/%m %H:%M')}] {note_text}\\n"
        await message.answer(text, parse_mode="HTML")
'''
if "/addcustomer" not in c:
    c += crm_code

# â”€â”€â”€ 5. INVITE â”€â”€â”€
invite_code = '''
@dp.message(Command("invite"))
async def cmd_invite(message: types.Message):
    ref_link = f"https://t.me/SLH_Claude_bot?start=ref{message.from_user.id}"
    async with pool.acquire() as conn:
        count = await conn.fetchval(
            "SELECT COUNT(*) FROM users WHERE referred_by = $1",
            message.from_user.id
        ) or 0
    await message.answer(
        f"ðŸ”— <b>Your Invite Link:</b>\\n{ref_link}\\n\\n"
        f"ðŸ‘¥ Friends joined: {count}\\n"
        f"â­ You earn 50 points per friend!\\n\\n"
        f"Share this link to grow the community!",
        parse_mode="HTML"
    )
'''
if "/invite" not in c:
    c += invite_code

with open("bot.py", "w", encoding="utf-8", newline="\n") as f:
    f.write(c)

print("âœ… Advanced features added.")

