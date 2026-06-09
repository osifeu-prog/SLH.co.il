import re, shutil

shutil.copy2(r"backups\bot_backup_20260604-0713.py", r"bot_clean.py")

with open("bot_clean.py", "r", encoding="utf-8") as f:
    code = f.read()

if code[0] == '\ufeff':
    code = code[1:]

# החלף תווי Unicode ב-ASCII
code = re.sub(r'[^\x00-\x7F]+', '', code)
code = code.replace('SLH_CLAUDE_BOT_TOKEN', 'BOT_TOKEN')

with open("bot.py", "w", encoding="ascii") as f:
    f.write(code)
print("bot.py is now ASCII-only")
