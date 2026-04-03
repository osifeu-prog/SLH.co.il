from pathlib import Path
import re

# files that likely contain UI strings
paths = [
    Path("main.py"),
    Path("handlers/sales.py"),
    Path("app/handlers/claim.py"),
    Path("app/handlers/invite.py"),
    Path("app/handlers/tasks.py"),
]

def ascii_sanitize_string_literal(s: str) -> str:
    # keep only ASCII; replace others with space, then collapse spaces
    t = ''.join(ch if ord(ch) < 128 else ' ' for ch in s)
    t = re.sub(r'\s+', ' ', t).strip()
    return t or "OK"

def patch_file(p: Path):
    if not p.exists():
        return
    text = p.read_text(encoding="utf-8", errors="replace").splitlines()
    out = []
    changed = 0

    # sanitize only string literals to ASCII (best-effort)
    str_re = re.compile(r'(["\'])(.*?)(\1)')
    for line in text:
        def repl(m):
            nonlocal changed
            q = m.group(1)
            body = m.group(2)
            new_body = ascii_sanitize_string_literal(body)
            if new_body != body:
                changed += 1
            return q + new_body + q

        # avoid touching SQL queries too aggressively (basic heuristic)
        if "SELECT " in line or "INSERT " in line or "UPDATE " in line or "DELETE " in line:
            out.append(line)
            continue

        out.append(str_re.sub(repl, line))

    p.write_text("\n".join(out) + "\n", encoding="utf-8", newline="\n")
    print(f"OK: {p} changed_literals={changed}")

for p in paths:
    patch_file(p)

# Add heartbeat to main.py (safe, ASCII)
mp = Path("main.py")
lines = mp.read_text(encoding="utf-8", errors="replace").splitlines()
if not any("HEARTBEAT" in l for l in lines):
    inject = [
        "",
        "# HEARTBEAT (ASCII-only, for ops visibility)",
        "async def _heartbeat():",
        "    while True:",
        "        try:",
        "            print('HEARTBEAT: bot running')",
        "        except Exception:",
        "            pass",
        "        await asyncio.sleep(30)",
        "",
    ]
    # insert after imports block (after load_dotenv usually)
    idx = 0
    for i,l in enumerate(lines):
        if "load_dotenv()" in l:
            idx = i+1
            break
    lines[idx:idx] = inject

# ensure heartbeat task starts inside main()
for i,l in enumerate(lines):
    if re.match(r'^\s*async def main\(\)\s*:', l):
        # find first line after await db.connect()
        insert_at = None
        for j in range(i, min(i+80, len(lines))):
            if "await db.connect()" in lines[j]:
                insert_at = j+1
                break
        if insert_at is not None and not any("_heartbeat" in x for x in lines[i:insert_at+10]):
            indent = "    "
            lines.insert(insert_at, indent + "asyncio.create_task(_heartbeat())")
        break

mp.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
print("OK: main.py heartbeat ensured")
