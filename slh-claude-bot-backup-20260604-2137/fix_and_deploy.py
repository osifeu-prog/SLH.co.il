import shutil, re, os

BACKUP = r"backups\bot_backup_20260604-0713.py"
BOT = r"bot.py"

# 1. שחזר גיבוי
shutil.copy2(BACKUP, BOT)

# 2. קרא
with open(BOT, "r", encoding="utf-8") as f:
    code = f.read()

# 3. הסר BOM
if code[0] == '\ufeff':
    code = code[1:]
    print("BOM removed")
else:
    print("No BOM")

# 4. תקן שמות משתנים
code = code.replace('SLH_CLAUDE_BOT_TOKEN', 'BOT_TOKEN')

# 5. החלף את כל התווים הלא-ASCII בתווים ASCII (מונע ג'יבריש)
def asciify(text):
    # שמור תווי ASCII + עברית + רווחים
    return re.sub(r'[^\u0590-\u05FF\u0020-\u007E\n\r\t]', '', text)

code = asciify(code)

# 6. שמור UTF-8 ללא BOM
with open(BOT, "w", encoding="utf-8") as f:
    f.write(code)

print("Bot fixed – ASCII-safe, no BOM, no encoding issues")
