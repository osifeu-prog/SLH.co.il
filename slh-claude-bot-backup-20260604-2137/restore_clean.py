import shutil, os, sys

BACKUP = r"backups\bot_backup_20260604-0713.py"
BOT = r"bot.py"

# 1. שחזור
shutil.copy2(BACKUP, BOT)
print("✅ v4.5 restored")

# 2. הסרת BOM
with open(BOT, "rb") as f:
    data = f.read()
if data[:3] == b'\xef\xbb\xbf':
    with open(BOT, "wb") as f:
        f.write(data[3:])
    print("✅ BOM removed")
else:
    print("✅ No BOM")

# 3. בדיקת Syntax
with open(BOT, "r", encoding="utf-8") as f:
    code = f.read()
import ast
try:
    ast.parse(code)
    print("✅ Syntax OK")
except SyntaxError as e:
    print(f"❌ Syntax Error: {e}")
    sys.exit(1)

print("🚀 Ready to deploy")
