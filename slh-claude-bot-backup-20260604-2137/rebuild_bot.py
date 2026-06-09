import shutil, re, os

# 1. קרא את הגיבוי
with open(r"backups\bot_backup_20260604-0713.py", "r", encoding="utf-8") as f:
    code = f.read()

# 2. תרגם את תווי ה-Unicode (למשל \U0001f9e0) לתווים ממשיים
#    Python לא מזהה \U בתוך טקסט רגיל, אבל הגיבוי מכיל escape-ים מפורשים.
#    נשתמש ב-regex כדי להמיר.
def unescape_unicode(match):
    return match.group(0).encode().decode('unicode_escape')

# ממיר כל \uXXXX או \UXXXXXXXX
code = re.sub(r'\\[Uu][0-9a-fA-F]{4,8}', lambda m: m.group(0).encode().decode('unicode_escape'), code)

# 3. שמור UTF-8 ללא BOM
with open("bot.py", "w", encoding="utf-8") as f:
    f.write(code)

# 4. וודא BOM לא קיים
with open("bot.py", "rb") as f:
    data = f.read()
if data[:3] == b'\xef\xbb\xbf':
    # לעולם לא אמור להגיע לכאן, אבל ליתר ביטחון
    with open("bot.py", "wb") as f:
        f.write(data[3:])
    print("✅ BOM removed (unexpected)")
else:
    print("✅ No BOM")

# 5. וודא שהתו 🧠 קיים
with open("bot.py", "r", encoding="utf-8") as f:
    content = f.read()
if '🧠' in content:
    print("✅ Hebrew content verified (🧠 found)")
else:
    print("❌ Hebrew not found  trying dump...")
    # dump of first 200 chars
    print(content[:200])
