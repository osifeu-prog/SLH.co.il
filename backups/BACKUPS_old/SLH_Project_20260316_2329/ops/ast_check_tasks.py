from pathlib import Path
import ast

for p in [Path("app/services/tasks.py"), Path("app/handlers/tasks.py")]:
    text = p.read_text(encoding="utf-8", errors="replace")
    try:
        ast.parse(text, filename=str(p))
        print(f"{p}: AST OK")
    except Exception as e:
        print(f"{p}: AST FAIL -> {e!r}")