import os, sys

FILE = "bot.py"
with open(FILE, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Ensure FSM imports exist
if "from aiogram.fsm.state import State, StatesGroup" not in content:
    content = content.replace(
        "from aiogram.client.bot import DefaultBotProperties",
        "from aiogram.client.bot import DefaultBotProperties\nfrom aiogram.fsm.state import State, StatesGroup\nfrom aiogram.fsm.context import FSMContext"
    )

# 2. Remove old identity functions (the reply-based ones)
lines = content.split("\n")
new_lines = []
skip = False
for line in lines:
    if "# â”€â”€â”€ /identity flow â”€â”€â”€" in line or "async def cmd_identity(message: types.Message):" in line:
        skip = True
        continue
    if skip and "# â”€â”€â”€ Wallet, Pay, Store, CRM stubs" in line:
        skip = False
        new_lines.append(line)
        continue
    if not skip:
        new_lines.append(line)
content = "\n".join(new_lines)

# 3. Insert the FSM-based identity code
fsm_code = '''
# â”€â”€â”€ Identity FSM â”€â”€â”€
class IdentityForm(StatesGroup):
    name = State()
    vision = State()
    values = State()

@dp.message(Command("identity"))
async def cmd_identity_start(message: types.Message, state: FSMContext):
    await state.set_state(IdentityForm.name)
    await message.answer("ðŸ‘¤ <b>×‘×¨×•×š ×”×‘× ×œ×ž×¡×¢ ×”×—×™×™× ×©×œ SLH</b>\n\n×ž×” ×”×©× ×©×œ×š?")

@dp.message(IdentityForm.name)
async def identity_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text.strip())
    await state.set_state(IdentityForm.vision)
    await message.answer("ðŸŒ± <b>×ž×” ×”×—×–×•×Ÿ ×©×œ×š?</b>\n(×ž×©×¤×˜ ××—×“ ×©×ž×ª××¨ ××ª ×”×ž×˜×¨×” ×”×’×“×•×œ×” ×©×œ×š)")

@dp.message(IdentityForm.vision)
async def identity_vision(message: types.Message, state: FSMContext):
    await state.update_data(vision=message.text.strip())
    await state.set_state(IdentityForm.values)
    await message.answer("ðŸ’Ž <b>×‘×—×¨ 3 ×¢×¨×›×™× ×©×ž× ×—×™× ××•×ª×š:</b>\n(×œ×“×•×’×ž×”: ××”×‘×”, ×—×•×¤×©, ×©×œ×•×, ×¦×“×§, ××•×ž×¥, ×—×›×ž×”)\n×©×œ×— ××ª ×©×œ×•×©×ª× ×ž×•×¤×¨×“×™× ×‘×¤×¡×™×§×™×")

@dp.message(IdentityForm.values)
async def identity_values(message: types.Message, state: FSMContext):
    data = await state.get_data()
    name = data['name']
    vision = data['vision']
    values = [v.strip() for v in message.text.split(",")[:3]]

    async with pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO identity (user_id, name, vision, values) VALUES ($1,$2,$3,$4) ON CONFLICT (user_id) DO UPDATE SET name=$2, vision=$3, values=$4",
            message.from_user.id, name, vision, values
        )
        await conn.execute("UPDATE users SET points = points + 50 WHERE telegram_id=$1", message.from_user.id)

    await state.clear()
    await message.answer(
        f"ðŸŽ‰ <b>×”×–×”×•×ª ×©×œ×š × ×•×¦×¨×”!</b>\n\n"
        f"×©×: {name}\n"
        f"×—×–×•×Ÿ: {vision}\n"
        f"×¢×¨×›×™×: {', '.join(values)}\n\n"
        f"+50 × ×§×•×“×•×ª! ðŸŽ¯\n"
        f"×©×œ×— /myidentity ×›×“×™ ×œ×¨××•×ª ××ª ×”×“×£ ×©×œ×š."
    )

@dp.message(Command("myidentity"))
async def cmd_myidentity(message: types.Message):
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT name, vision, values FROM identity WHERE user_id=$1", message.from_user.id)
        if not row:
            await message.answer("âŒ ×¢×“×™×™×Ÿ ×œ× ×”×’×“×¨×ª ×–×”×•×ª. ×©×œ×— /identity")
            return
        await message.answer(
            f"ðŸ‘¤ <b>{row['name']}</b>\n"
            f"ðŸŒ± ×—×–×•×Ÿ: {row['vision']}\n"
            f"ðŸ’Ž ×¢×¨×›×™×: {', '.join(row['values'])}",
            parse_mode=ParseMode.HTML
        )
'''
content = content.replace("# â”€â”€â”€ Wallet, Pay, Store, CRM stubs", fsm_code + "\n# â”€â”€â”€ Wallet, Pay, Store, CRM stubs")

# 4. Replace ai_chat with Groq version
old_ai = '''@dp.message(F.text, ~F.text.startswith("/"))
async def ai_chat(message: types.Message):
    await message.answer("AI is thinking... (use /ask for advanced)")'''
new_ai = '''@dp.message(F.text, ~F.text.startswith("/"))
async def ai_chat(message: types.Message):
    await bot.send_chat_action(chat_id=message.chat.id, action="typing")
    try:
        import groq
        client = groq.Groq(api_key=os.getenv("GROQ_API_KEY"))
        resp = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": message.text}],
            max_tokens=400,
            temperature=0.7,
        )
        answer = resp.choices[0].message.content
        await message.answer(answer[:4096])
    except Exception as e:
        await message.answer(f"âš ï¸ AI error: {str(e)[:200]}")'''
content = content.replace(old_ai, new_ai)

# 5. Ensure 'import groq' is at top if not present
if "import groq" not in content.split("\n")[0:20]:
    content = "import groq\n" + content

# Save without BOM
with open(FILE, "w", encoding="utf-8", newline="\n") as f:
    f.write(content)

print("âœ… bot.py patched successfully.")
