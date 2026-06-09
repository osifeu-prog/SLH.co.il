import re, os

with open("bot.py", "r", encoding="utf-8") as f:
    c = f.read()

# --- ×ª×™×§×•×Ÿ sysinfo (×‘×œ×™ psutil) ---
old_sys = 'async def cmd_sysinfo(msg):\n    import platform, psutil\n    cpu = psutil.cpu_percent()\n    mem = psutil.virtual_memory()\n    disk = psutil.disk_usage'
new_sys = 'async def cmd_sysinfo(msg):\n    import platform\n    cpu=0; mem_percent=0; mem_used=0; mem_total=0; disk_percent=0\n    try:\n        import psutil\n        cpu = psutil.cpu_percent()\n        mem = psutil.virtual_memory()\n        mem_percent=mem.percent\n        mem_used=mem.used//(1024**2)\n        mem_total=mem.total//(1024**2)\n        disk = psutil.disk_usage'
c = c.replace(old_sys, new_sys)

# --- AI: Groq ×¨××©×™ + Gemini fallback ---
old_ai = '@dp.message(F.text, ~F.text.startswith("/"))\nasync def ai_chat(message: types.Message):\n    await message.answer("AI is thinking... (use /ask for advanced)")'
new_ai = '''@dp.message(F.text, ~F.text.startswith("/"))
async def ai_chat(message: types.Message):
    await bot.send_chat_action(chat_id=message.chat.id, action="typing")
    answer = None
    # 1. Groq (×¨××©×™)
    try:
        import groq
        client = groq.Groq(api_key=os.getenv("GROQ_API_KEY"))
        resp = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role":"user","content":message.text}],
            max_tokens=400, temperature=0.7
        )
        answer = resp.choices[0].message.content
    except Exception as e:
        answer = f"âš ï¸ Groq error: {str(e)[:100]}"
    # 2. Gemini fallback
    if not answer or answer.startswith("âš ï¸"):
        try:
            import google.generativeai as genai
            genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
            model = genai.GenerativeModel("gemini-2.0-flash")
            resp = model.generate_content(message.text)
            answer = resp.text
        except:
            pass
    if not answer:
        answer = "âŒ All AI engines unavailable."
    await message.answer(answer[:4096])'''
if old_ai in c:
    c = c.replace(old_ai, new_ai)
else:
    c = re.sub(
        r'async def ai_chat\(message: types\.Message\):\n.*?(?=\n\n|$)',
        new_ai,
        c,
        flags=re.DOTALL
    )

# --- /simdeposit ---
if "/simdeposit" not in c:
    sim_cmd = '''
@dp.message(Command("simdeposit"))
async def cmd_simdeposit(message: types.Message):
    parts = message.text.split()
    if len(parts) < 2:
        return await message.answer("Usage: /simdeposit <amount_in_ton>")
    try:
        amount = float(parts[1])
    except:
        return await message.answer("Invalid amount.")
    async with pool.acquire() as conn:
        await conn.execute("UPDATE users SET balance = balance + $1 WHERE telegram_id = $2", amount, message.from_user.id)
        new_balance = await conn.fetchval("SELECT balance FROM users WHERE telegram_id = $1", message.from_user.id)
        await conn.execute("UPDATE users SET tier = CASE WHEN $1 >= 29 THEN 'business' WHEN $1 >= 9.9 THEN 'pro' ELSE 'free' END WHERE telegram_id = $2", new_balance, message.from_user.id)
        tier = await conn.fetchval("SELECT tier FROM users WHERE telegram_id = $1", message.from_user.id)
    await message.answer(f"âœ… Simulated deposit: {amount} TON\\nBalance: {new_balance:.2f} TON\\nTier: {tier.upper()}")
'''
    c += sim_cmd

# --- /wallet (×©×™×¤×•×¨) ---
c = c.replace(
    'async def cmd_wallet(msg): await msg.answer("ðŸ’° Wallet (coming soon)")',
    '''async def cmd_wallet(msg):
    async with pool.acquire() as conn:
        bal = await conn.fetchval("SELECT balance FROM users WHERE telegram_id=$1", msg.from_user.id) or 0
        tier = await conn.fetchval("SELECT tier FROM users WHERE telegram_id=$1", msg.from_user.id) or "free"
        await msg.answer(f"ðŸ’° Wallet\\nBalance: {bal:.2f} TON\\nTier: {tier.upper()}")'''
)

with open("bot.py", "w", encoding="utf-8", newline="\n") as f:
    f.write(c)

print("âœ… AI + wallet + simdeposit upgraded.")

