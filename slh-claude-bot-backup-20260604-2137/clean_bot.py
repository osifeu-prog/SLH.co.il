import re

with open("bot.py", "r", encoding="utf-8") as f:
    code = f.read()

# פונקציה להסיר כל תו שאינו ASCII, אות עברית, ניקוד, או פיסוק בסיסי
def clean_unicode(text):
    # שמור אותיות עבריות + ASCII + רווחים + פיסוק בסיסי
    return re.sub(r'[^\u0590-\u05FF\u0020-\u007E\u00A0-\u00FF\u200E\u200F\n\r\t]', '', text)

code = clean_unicode(code)

# שמור UTF-8 ללא BOM
with open("bot.py", "w", encoding="utf-8") as f:
    f.write(code)

# וודא BOM לא קיים
with open("bot.py", "rb") as f:
    data = f.read()
if data[:3] == b'\xef\xbb\xbf':
    with open("bot.py", "wb") as f:
        f.write(data[3:])
    print("✅ BOM removed")
else:
    print("✅ No BOM")

print("✅ File cleaned  emojis removed, Hebrew kept")
