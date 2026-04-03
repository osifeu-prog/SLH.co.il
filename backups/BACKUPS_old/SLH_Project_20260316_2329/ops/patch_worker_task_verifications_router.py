from pathlib import Path

p = Path("worker.py")
s = p.read_text(encoding="utf-8", errors="replace").replace("\r\n", "\n")

old_import = 'from app.handlers.ton_admin import router as ton_admin_router'
new_import = old_import + '\nfrom app.handlers.task_verifications import router as task_verifications_router'
if old_import not in s:
    raise SystemExit("worker.py import anchor not found")
if 'from app.handlers.task_verifications import router as task_verifications_router' not in s:
    s = s.replace(old_import, new_import, 1)

old_include = 'dp.include_router(ton_admin_router)'
new_include = old_include + '\ndp.include_router(task_verifications_router)'
if old_include not in s:
    raise SystemExit("worker.py include anchor not found")
if 'dp.include_router(task_verifications_router)' not in s:
    s = s.replace(old_include, new_include, 1)

p.write_text(s, encoding="utf-8", newline="\n")
print("worker.py patched with task_verifications router")