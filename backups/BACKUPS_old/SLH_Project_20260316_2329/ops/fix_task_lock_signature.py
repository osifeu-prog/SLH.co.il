from pathlib import Path

p = Path("app/services/tasks.py")
s = p.read_text(encoding="utf-8", errors="replace").replace("\r\n", "\n")

old = '                "SELECT pg_advisory_xact_lock($1::bigint, $2::integer)"'
new = '                "SELECT pg_advisory_xact_lock($1::integer, $2::integer)"'

if old not in s:
    raise SystemExit("lock SQL anchor not found")

s = s.replace(old, new, 1)
p.write_text(s, encoding="utf-8", newline="\n")
print("tasks.py lock signature fixed")