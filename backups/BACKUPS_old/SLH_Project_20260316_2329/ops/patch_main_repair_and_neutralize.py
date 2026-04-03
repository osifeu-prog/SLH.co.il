from pathlib import Path
import re

p = Path("main.py")
lines = p.read_text(encoding="utf-8", errors="replace").splitlines()

# 1) לתקן את השבירה: במקרה שלנו נכנסה שורה "print('BOT ONLINE')" במקום הסוגר של stats
# מזהים את התבנית שהראית: print('BOT ONLINE') ואז await message.answer(stats,...)
for i in range(len(lines)-1):
    if lines[i].strip() == "print('BOT ONLINE')" and "await message.answer(stats" in lines[i+1]:
        # מחזירים את הסוגר בסגנון המקורי (8 רווחים)
        lines[i] = "        )"
        break

# 2) לנטרל כל print שמכיל rocket escaped (הופעות של \U0001f680) אם קיימות בקובץ בפועל
for i, line in enumerate(lines):
    if "print(" in line and ("\\U0001f680" in line or "U0001f680" in line or "🚀" in line):
        indent = re.match(r'^(\s*)', line).group(1)
        lines[i] = indent + "print('BOT ONLINE')"  # ASCII בלבד

# 3) להבטיח שיש print BOT ONLINE אחד לפני start_polling (בסוף הקובץ)
# (לא חובה, אבל עוזר לוודא שהבוט עלה)
for i, line in enumerate(lines):
    if "await dp.start_polling" in line:
        # אם השורה הקודמת לא print('BOT ONLINE'), נכניס אחת
        if i > 0 and "print('BOT ONLINE')" not in lines[i-1]:
            indent = re.match(r'^(\s*)', line).group(1)
            lines.insert(i, indent + "print('BOT ONLINE')")
        break

p.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
print("OK: main.py repaired (restored stats closing + neutralized rocket prints if present).")
