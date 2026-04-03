from pathlib import Path
import ast
import hashlib

files = [
    Path("app/services/economy.py"),
    Path("app/services/xp.py"),
    Path("app/handlers/claim.py"),
    Path("app/services/bootstrap.py"),
]

for p in files:
    print(f"\n=== FILE: {p} ===")
    data = p.read_bytes()
    print("bytes:", len(data))
    print("sha256:", hashlib.sha256(data).hexdigest())
    text = p.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()

    print("--- first 120 lines (repr) ---")
    for i, line in enumerate(lines[:120], start=1):
        print(f"{i:04d}: {line!r}")

    try:
        ast.parse(text, filename=str(p))
        print("AST: OK")
    except Exception as e:
        print("AST: FAIL", repr(e))