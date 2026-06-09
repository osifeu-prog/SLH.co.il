import re

with open("bot.py", "r", encoding="utf-8") as f:
    code = f.read()

# מוצא את השורה של AI Fallback
marker = "# ====================== AI Fallback ======================"

# מוסיף debug handler מעל
debug_handler = """
@dp.message()
async def debug_all(msg: types.Message):
    print(f"📩 DEBUG: {msg.from_user.id} | {msg.text}")
"""

if "debug_all" not in code:
    code = code.replace(marker, debug_handler + "\n" + marker)

# שמירה UTF-8 ללא BOM
with open("bot.py", "w", encoding="utf-8") as f:
    f.write(code)

# וידוא שאין BOM
with open("bot.py", "rb") as f:
    data = f.read()
if data[:3] == b'\xef\xbb\xbf':
    with open("bot.py", "wb") as f:
        f.write(data[3:])
    print("✅ BOM removed after edit")
else:
    print("✅ No BOM")

print("✅ Debug handler added")
