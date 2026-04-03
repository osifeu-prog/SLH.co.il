from pathlib import Path

p = Path("main.py")
lines = p.read_text(encoding="utf-8", errors="replace").splitlines()

out = []
changed = 0
for line in lines:
    if "U0001f680" in line:   # תופס גם "\U0001f680"
        out.append("    print('BOT ONLINE')")  # ASCII בלבד
        changed += 1
    else:
        out.append(line)

p.write_text("\n".join(out) + "\n", encoding="utf-8", newline="\n")
print(f"OK: replaced {changed} line(s) containing U0001f680 in main.py")
