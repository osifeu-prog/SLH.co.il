from pathlib import Path
import re

p = Path("main.py")
lines = p.read_text(encoding="utf-8", errors="replace").splitlines()

out = []
changed = 0
hits = []

for i, line in enumerate(lines, start=1):
    # תופס כל print(...) שיש בו תווים לא-ASCII (עברית/אמוג'י וכו')
    if re.search(r'^\s*print\s*\(', line) and any(ord(ch) > 127 for ch in line):
        indent = re.match(r'^(\s*)', line).group(1)
        out.append(f"{indent}print('BOT ONLINE')")
        changed += 1
        hits.append((i, line))
    else:
        out.append(line)

p.write_text("\n".join(out) + "\n", encoding="utf-8", newline="\n")

print(f"OK: replaced {changed} non-ascii print line(s) in main.py")
if hits:
    print("Changed lines:")
    for i, l in hits[:20]:
        print(f"  L{i}: {l[:160]}")
