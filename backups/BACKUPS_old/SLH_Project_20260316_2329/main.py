raise SystemExit(
    "LEGACY ENTRYPOINT BLOCKED: use ops/start-core.ps1 with webhook_server.py + worker.py, not main.py"
)
# --- UX UPDATE: HELP HANDLER (Task 5) ---
@dp.message_handler(lambda m: m.text and "????" in m.text)
async def smart_help(message: types.Message):
    await message.bot.send_chat_action(message.chat.id, "typing")
    from app.i18n import STRINGS
    lang = "he"
    help_text = f"{STRINGS[lang]['help_title']}\n\n{STRINGS[lang]['help_steps']}"
    await message.answer(help_text, parse_mode='HTML')
