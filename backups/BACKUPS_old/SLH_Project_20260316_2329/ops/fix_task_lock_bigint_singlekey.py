from pathlib import Path

p = Path("app/services/tasks.py")
s = p.read_text(encoding="utf-8", errors="replace").replace("\r\n", "\n")

old = '''            await conn.execute(
                "SELECT pg_advisory_xact_lock($1::integer, $2::integer)"
                , user_id, task_id
            )
'''

new = '''            lock_key = int(user_id) * 1000 + int(task_id)
            await conn.execute(
                "SELECT pg_advisory_xact_lock($1::bigint)",
                lock_key,
            )
'''

if old not in s:
    raise SystemExit("task lock block not found")

s = s.replace(old, new, 1)
p.write_text(s, encoding="utf-8", newline="\n")
print("tasks.py advisory lock migrated to bigint single-key")