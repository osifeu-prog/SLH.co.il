import shutil, os

# שחזר גיבוי נקי
shutil.copy2(r"backups\bot_backup_20260604-0713.py", r"bot.py")

with open("bot.py", "r", encoding="utf-8") as f:
    code = f.read()

# תקן שמות משתנים
code = code.replace('os.getenv("SLH_CLAUDE_BOT_TOKEN")', 'os.getenv("BOT_TOKEN")')
code = code.replace('"SLH_CLAUDE_BOT_TOKEN"', '"BOT_TOKEN"')

# הסר BOM
if code[0] == '\ufeff':
    code = code[1:]

# החלף אמוג'ים (כמו קודם)
replacements = {
    '\U0001f9e0': '[BRAIN]', '\U0001f6d2': '[CART]', '\U0001f4b0': '[MONEY]',
    '\U0001f4ca': '[CHART]', '\u2b50': '[STAR]', '\u2705': '[CHECK]',
    '\u26a1': '[LIGHTNING]', '\U0001f4e6': '[BOX]', '\U0001f4cb': '[LIST]',
    '\U0001f3c6': '[TROPHY]', '\U0001f451': '[CROWN]', '\U0001f52e': '[CRYSTAL]',
    '\u262e': '[PEACE]', '\U0001f517': '[LINK]', '\U0001f4b3': '[WALLET]',
    '\U0001f3c5': '[MEDAL]', '\U0001f91d': '[HANDSHAKE]', '\u2753': '[QUESTION]',
    '\u26d4': '[NO ENTRY]', '\U0001f4be': '[FLOPPY]', '\U0001f4dd': '[PENCIL]',
    '\u2795': '[PLUS]', '\U0001f389': '[PARTY]', '\U0001f4b8': '[MONEY WINGS]',
    '\U0001f4b3': '[CREDIT CARD]', '\U0001f4d8': '[BOOK]', '\U0001f393': '[GRAD]',
    '\U0001f4dc': '[SCROLL]', '\U0001f4db': '[NAME BADGE]', '\U0001f4c4': '[DOC]',
    '\U0001f4e2': '[SPEAKER]', '\U0001f305': '[SUNRISE]', '\U0001fa7a': '[STETHOSCOPE]',
    '\U0001f4e1': '[SATELLITE]', '\u23f0': '[CLOCK]', '\U0001f4c5': '[CALENDAR]',
    '\U0001f539': '[BLUE DIAMOND]', '\U0001f536': '[ORANGE DIAMOND]',
    '\u26a0': '[WARNING]', '\U0001f680': '[ROCKET]', '\U0001f504': '[REFRESH]',
    '\U0001f4a1': '[IDEA]', '\U0001f525': '[FIRE]', '\U0001f44d': '[THUMBS UP]',
    '\U0001f4ac': '[SPEECH BUBBLE]', '\U0001f527': '[WRENCH]', '\U0001f9ea': '[TEST TUBE]',
}
for old, new in replacements.items():
    code = code.replace(old, new)

# שמור
with open("bot.py", "w", encoding="utf-8") as f:
    f.write(code)

# וודא BOM לא קיים
with open("bot.py", "rb") as f:
    data = f.read()
if data[:3] == b'\xef\xbb\xbf':
    with open("bot.py", "wb") as f:
        f.write(data[3:])
    print("BOM removed")
else:
    print("No BOM")

print("Bot adapted to Railway variables")
