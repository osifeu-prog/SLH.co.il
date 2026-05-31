import shutil, os

# 1. Restore the clean backup (no admin_panel, working)
shutil.copy("bot.py.final_backup", "bot.py")

with open("bot.py", "r", encoding="utf-8") as f:
    c = f.read()

# 2. Remove BOM
c = c.replace('\ufeff', '')

# 3. Fix ADMIN_IDS (replace spaces with commas)
old_admin = 'ADMIN_IDS = [int(x) for x in os.getenv("ADMIN_ID", "").split(",") if x]'
new_admin = 'ADMIN_IDS = [int(x) for x in os.getenv("ADMIN_ID", "").replace(" ", ",").split(",") if x]'
c = c.replace(old_admin, new_admin)

# 4. Replace the current /start with the full one (logo + menu)
old_start = '''@dp.message(Command("start"))
async def cmd_start(msg: Message):
    await msg.answer(
        "Hello Osif! \u263A\\n"
        "I am SLH Claude  your AI assistant.\\n"
        "\U0001f48e Tier: free\\n\\n"
        "Available commands:\\n"
        "/register  Subscribe to updates\\n"
        "/donate  Support the project\\n"
        "/status  Project status\\n"
        "/checkin  Daily check-in (+5 points)\\n"
        "/leaderboard  Top 5\\n"
        "/points  My points\\n"
        "/daily  Daily missions\\n"
        "/backup  Create backup\\n"
        "/broadcast <msg>  (Admin) Send message to all\\n"
        "/help  All commands",
        parse_mode=None
    )'''

new_start = '''@dp.message(Command("start"))
async def cmd_start(msg: Message):
    ensure_user(msg.from_user.id, msg.from_user.full_name or "friend")
    logo = ("<pre>╔══════════════════════════════════╗\\n"
            "║     ███████╗██╗     ██╗  ██╗     ║\\n"
            "║     ██╔════╝██║     ██║  ██║     ║\\n"
            "║     ███████╗██║     ███████║     ║\\n"
            "║     ╚════██║██║     ██╔══██║     ║\\n"
            "║     ███████║███████╗██║  ██║     ║\\n"
            "║     ╚══════╝╚══════╝╚═╝  ╚═╝     ║\\n"
            "║   \U0001f9e0 SLH SPARK AI   v3.2        ║\\n"
            "╚══════════════════════════════════╝</pre>")
    await msg.answer(logo, parse_mode=ParseMode.HTML)
    await msg.answer("<b>\u2705 SLH SPARK AI v3.2 alive!</b>", reply_markup=main_menu())'''

c = c.replace(old_start, new_start)

# 5. Ensure main_menu function exists
if 'def main_menu():' not in c:
    menu_def = '''
def main_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="\U0001f4ca Status", callback_data="cmd_status"),
         InlineKeyboardButton(text="\u2b50 Points", callback_data="cmd_points")],
        [InlineKeyboardButton(text="\u2705 Check-in", callback_data="cmd_checkin"),
         InlineKeyboardButton(text="\u26a1 Tap-to-Earn", callback_data="cmd_tap")],
        [InlineKeyboardButton(text="\U0001f4b0 Crypto", callback_data="cmd_crypto"),
         InlineKeyboardButton(text="\U0001f91d Donate", callback_data="cmd_donate")],
        [InlineKeyboardButton(text="\U0001f4d6 Guide", callback_data="cmd_guide"),
         InlineKeyboardButton(text="\u2753 Help", callback_data="cmd_help")],
    ])
'''
    c += '\n' + menu_def

with open("bot.py", "w", encoding="utf-8") as f:
    f.write(c)

print("\u2705 Full bot restored with logo + menu")
