import shutil, os, sys, subprocess, time

BACKUP = r"backups\bot_backup_20260604-0713.py"
BOT = r"bot.py"

# 1. restore
shutil.copy2(BACKUP, BOT)
print("? v4.5 restored")

# 2. strip BOM
with open(BOT, "rb") as f:
    data = f.read()
if data[:3] == b'\xef\xbb\xbf':
    with open(BOT, "wb") as f:
        f.write(data[3:])
    print("? BOM removed")

# 3. syntax check
import ast
with open(BOT, "r", encoding="utf-8") as f:
    code = f.read()
ast.parse(code)
print("? Syntax OK")

# 4. deploy
print("?? Deploying...")
subprocess.run(["railway", "down", "--service", "slh-AI-bot", "-y"])
time.sleep(5)
result = subprocess.run(["railway", "up", "--detach"], capture_output=True, text=True)
if "Build Logs:" in result.stdout or "Uploaded" in result.stdout:
    print("? Deploy started")
else:
    print("? Deploy failed:", result.stderr)
