from pathlib import Path
import re
import shutil

path = Path(r"D:\SLH_PROJECT_V2\bot_full.py")
backup = Path(r"D:\SLH_PROJECT_V2\bot_full.py.bak_before_H_passthrough")

shutil.copy2(path, backup)
text = path.read_text(encoding="utf-8")

pattern = r'def H\(s: str\) -> str:\s*return s\.encode\("ascii"\)\.decode\("unicode_escape"\)'
replacement = '''def H(s: str) -> str:
    return s'''

new_text, n = re.subn(pattern, replacement, text, count=1)

if n == 0:
    raise SystemExit("H() pattern not found - no changes made")

path.write_text(new_text, encoding="utf-8", newline="\n")
print("Patched H() successfully")
print(f"Backup: {backup}")