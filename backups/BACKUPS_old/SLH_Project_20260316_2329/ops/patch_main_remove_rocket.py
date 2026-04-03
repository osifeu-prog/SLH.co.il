from pathlib import Path

p = Path("main.py")
s = p.read_text(encoding="utf-8", errors="replace").splitlines()

out = []
for line in s:
    if "\\U0001f680" in line or "🚀" in line:
        # החלפה נקייה בלי אמוג'י
        out.append("    print('BOT ONLINE')")
    else:
        out.append(line)

p.write_text("\n".join(out) + "\n", encoding="utf-8", newline="\n")
print("OK: rocket removed/replaced in main.py")
