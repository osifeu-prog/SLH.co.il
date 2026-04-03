from pathlib import Path
import re

p = Path("main.py")
s = p.read_text(encoding="utf-8", errors="replace")

# 1) Insert UTF-8 stdout/stderr reconfigure once (right after imports)
if "sys.stdout.reconfigure" not in s:
    patch = (
        "import sys\n"
        "try:\n"
        "    sys.stdout.reconfigure(encoding='utf-8', errors='replace')\n"
        "    sys.stderr.reconfigure(encoding='utf-8', errors='replace')\n"
        "except Exception:\n"
        "    pass\n"
    )
    lines = s.splitlines()
    insert_at = 0
    for i, line in enumerate(lines[:160]):
        if line.startswith("import ") or line.startswith("from "):
            insert_at = i + 1
    lines.insert(insert_at, patch)
    s = "\n".join(lines) + "\n"

# 2) Remove/replace any print line that contains rocket (literal or escape)
#    - matches "🚀" OR "U0001f680"
s = re.sub(r"(?m)^\s*print\(.*(🚀|U0001f680).*?\)\s*$", "print('BOT ONLINE')", s)

p.write_text(s, encoding="utf-8", newline="\n")
print("OK: patched main.py (UTF-8 + removed rocket prints).")
