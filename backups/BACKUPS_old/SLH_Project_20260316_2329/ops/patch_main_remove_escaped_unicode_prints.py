from pathlib import Path
import re

p = Path("main.py")
lines = p.read_text(encoding="utf-8", errors="replace").splitlines()

out = []
changed = 0
for i, line in enumerate(lines, start=1):
    # תופס print שמכיל \UXXXXXXXX או \uXXXX או \N{...}
    if re.search(r'^\s*print\s*\(', line) and (r"\U" in line or r"\u" in line or r"\N{" in line):
        indent = re.match(r'^(\s*)', line).group(1)
        out.append(f"{indent}print('BOT ONLINE')")
        changed += 1
    else:
        out.append(line)

p.write_text("\n".join(out) + "\n", encoding="utf-8", newline="\n")
print(f"OK: replaced {changed} escaped-unicode print line(s) in main.py")
