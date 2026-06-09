import shutil, os

# 1. שחזר גיבוי
src = r"backups\bot_backup_20260604-0713.py"
dst = r"bot.py"
shutil.copy2(src, dst)
print("✅ v4.5 restored")

# 2. וודא UTF-8 ללא BOM
with open(dst, "rb") as f:
    data = f.read()
if data[:3] == b'\xef\xbb\xbf':
    with open(dst, "wb") as f:
        f.write(data[3:])
    print("✅ BOM removed")
else:
    print("✅ No BOM found")

# 3. בדיקת Syntax
with open(dst, "r", encoding="utf-8") as f:
    code = f.read()
import ast
ast.parse(code)
print("✅ Syntax OK")
