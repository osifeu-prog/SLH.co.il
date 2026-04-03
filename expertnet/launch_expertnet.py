import subprocess
import time
import sys

print("🚀 Starting ExpertNet Core Dual-Engine...")

# הפעלת ה-Dashboard בחלון נפרד
subprocess.Popen(["start", "cmd", "/k", "py scripts\\dashboard.py"], shell=True)

time.sleep(2) # מחכה רגע שהשרת יעלה

# הפעלת הבוט בחלון הנוכחי
print("🤖 Launching Telegram Bot...")
subprocess.run(["py", "scripts\\telegram_bot.py"])