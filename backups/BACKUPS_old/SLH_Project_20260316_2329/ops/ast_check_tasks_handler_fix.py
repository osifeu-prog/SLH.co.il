from pathlib import Path
import ast

p = Path("app/handlers/tasks.py")
text = p.read_text(encoding="utf-8", errors="replace")
ast.parse(text, filename=str(p))
print("tasks.py AST OK")