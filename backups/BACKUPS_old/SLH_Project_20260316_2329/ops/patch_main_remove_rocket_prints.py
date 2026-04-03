from pathlib import Path
import re

p = Path("main.py")
lines = p.read_text(encoding="utf-8", errors="replace").splitlines()

out = []
changed = 0
for line in lines:
    # remove any print line containing rocket or escaped rocket or U0001f680
    if re.search(r'^\s*print\s*\(.*(U0001f680|\\U0001f680|🚀).*?\)\s*$', line):
        # preserve indentation of the original line
        indent = re.match(r'^(\s*)', line).group(1)
        out.append(f"{indent}print('BOT ONLINE')")
        changed += 1
    else:
        out.append(line)

p.write_text("\n".join(out) + "\n", encoding="utf-8", newline="\n")
print(f"OK: main.py rocket-print patched, changed={changed}")
