from pathlib import Path

TARGET_LINE = 114  # לפי ה-traceback שלך

p = Path("main.py")
lines = p.read_text(encoding="utf-8", errors="replace").splitlines()

if TARGET_LINE <= 0 or TARGET_LINE > len(lines):
    raise SystemExit(f"ERROR: main.py has {len(lines)} lines; cannot patch line {TARGET_LINE}")

old = lines[TARGET_LINE-1]
lines[TARGET_LINE-1] = "    print('BOT ONLINE')"

p.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
print("OK: patched main.py line", TARGET_LINE)
print("OLD:", old[:200])
print("NEW:", lines[TARGET_LINE-1])
