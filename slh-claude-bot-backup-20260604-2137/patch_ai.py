import re, sys

with open("bot.py", "r", encoding="utf-8") as f:
    content = f.read()

# 1. ×•×“× imports
for lib, imp in [("google.generativeai", "import google.generativeai as genai\n"), ("anthropic", "import anthropic\n")]:
    if lib not in content:
        content = content.replace("import groq\n", "import groq\n" + imp)

# 2. ×”×—×œ×£ ××ª ×¤×•× ×§×¦×™×™×ª ai_chat ×”×™×©× ×” ×‘×—×“×©×”
old_ai = r'''@dp.message(F.text, ~F.text.startswith("/"))
async def ai_chat(message: types.Message):
    await message.answer("AI is thinking... (use /ask for advanced)")'''

new_ai = '''@dp.message(F.text, ~F.text.startswith("/"))
async def ai_chat(message: types.Message):
    await bot.send_chat_action(chat_id=message.chat.id, action="typing")
    providers = []
    if os.getenv("GROQ_API_KEY"): providers.append("groq")
    if os.getenv("GEMINI_API_KEY"): providers.append("gemini")
    if os.getenv("ANTHROPIC_API_KEY"): providers.append("claude")
    for provider in providers:
        try:
            if provider == "groq":
                client = groq.Groq(api_key=os.getenv("GROQ_API_KEY"))
                resp = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "user", "content": message.text}],
                    max_tokens=400, temperature=0.7
                )
                answer = resp.choices[0].message.content
            elif provider == "gemini":
                genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
                model = genai.GenerativeModel("gemini-2.0-flash")
                answer = model.generate_content(message.text).text
            elif provider == "claude":
                client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
                resp = client.messages.create(
                    model="claude-3-haiku-20240307",
                    max_tokens=400,
                    messages=[{"role": "user", "content": message.text}]
                )
                answer = resp.content[0].text
            if answer:
                await message.answer(answer[:4096])
                return
        except:
            continue
    await message.answer("âš ï¸ All AI engines unavailable. Try later.")'''

if old_ai in content:
    content = content.replace(old_ai, new_ai)
else:
    # Fallback: insert before callback handler
    content = content.replace("# â”€â”€â”€ Callback handler", new_ai + "\n\n# â”€â”€â”€ Callback handler")

# 3. ×ª×™×§×•×Ÿ ×ž×—×¨×•×–×•×ª ×œ× ×¡×’×•×¨×•×ª (×× ×™×©)
content = content.replace(
    'await message.answer("ðŸ‘¤ <b>×‘×¨×•×š ×”×‘× ×œ×ž×¡×¢ ×”×—×™×™× ×©×œ SLH</b>\n\n×ž×” ×”×©× ×©×œ×š?\n(×¤×©×•×˜ ×©×œ×— ×”×•×“×¢×” ×¢× ×”×©×)", parse_mode=ParseMode.HTML)',
    'await message.answer("ðŸ‘¤ Welcome! What is your name?")'
)

with open("bot.py", "w", encoding="utf-8", newline="\n") as f:
    f.write(content)

print("âœ… AI function patched.")

