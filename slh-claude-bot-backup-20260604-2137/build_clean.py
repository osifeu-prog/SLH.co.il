import shutil, re, os

# שחזר גיבוי נקי
shutil.copy2(r"backups\bot_backup_20260604-0713.py", r"bot_temp.py")

with open("bot_temp.py", "r", encoding="utf-8") as f:
    code = f.read()

# הסר BOM
if code[0] == '\ufeff':
    code = code[1:]

# החלף אמוג'ים בתיאורים טקסטואליים
replacements = {
    '🧠': '[BRAIN]',
    '🛒': '[CART]',
    '💎': '[GEM]',
    '💰': '[COIN]',
    '⚡': '[LIGHTNING]',
    '✅': '[CHECK]',
    '❌': '[CROSS]',
    '📦': '[BOX]',
    '📋': '[LIST]',
    '🏆': '[TROPHY]',
    '👑': '[CROWN]',
    '🔮': '[CRYSTAL]',
    '☮️': '[PEACE]',
    '🔗': '[LINK]',
    '📊': '[CHART]',
    '👛': '[WALLET]',
    '🏅': '[MEDAL]',
    '🤝': '[HANDSHAKE]',
    '❓': '[QUESTION]',
    '⛔': '[NO ENTRY]',
    '💾': '[FLOPPY]',
    '📝': '[PENCIL]',
    '➕': '[PLUS]',
    '🎉': '[PARTY]',
    '💸': '[MONEY]',
    '💳': '[CREDIT CARD]',
    '📘': '[BOOK]',
    '🎓': '[GRADUATION]',
    '📜': '[SCROLL]',
    '📛': '[NAME BADGE]',
    '📄': '[DOCUMENT]',
    '📢': '[SPEAKER]',
    '🌅': '[SUNRISE]',
    '🩺': '[STETHOSCOPE]',
    '📡': '[SATELLITE]',
    '⏰': '[CLOCK]',
    '📅': '[CALENDAR]',
    '🔹': '[BLUE DIAMOND]',
    '🔶': '[ORANGE DIAMOND]',
    '⚠️': '[WARNING]',
    '🚀': '[ROCKET]',
    '⭐': '[STAR]',
    '🔄': '[REFRESH]',
    '💡': '[IDEA]',
    '🔥': '[FIRE]',
    '👍': '[THUMBS UP]',
    '💬': '[SPEECH BUBBLE]',
    '🔧': '[WRENCH]',
    '🧪': '[TEST TUBE]',
}
for emoji, text in replacements.items():
    code = code.replace(emoji, text)

# שמור UTF-8 ללא BOM
with open("bot.py", "w", encoding="utf-8") as f:
    f.write(code)

# וודא BOM לא קיים
with open("bot.py", "rb") as f:
    data = f.read()
if data[:3] == b'\xef\xbb\xbf':
    with open("bot.py", "wb") as f:
        f.write(data[3:])
    print("BOM removed (unexpected)")

# בדוק עברית
if '×' not in code:   # Hebrew character
    print("ERROR: Hebrew not found")
else:
    print("OK: Hebrew present")
os.remove("bot_temp.py")
print("bot.py ready")
