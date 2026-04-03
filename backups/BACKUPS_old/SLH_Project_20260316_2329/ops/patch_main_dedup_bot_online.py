from pathlib import Path
p=Path("main.py")
lines=p.read_text(encoding="utf-8", errors="replace").splitlines()

out=[]
seen=False
for line in lines:
    if line.strip() in ('print("BOT ONLINE")',"print('BOT ONLINE')"):
        if seen:
            continue
        seen=True
        out.append("    print('BOT ONLINE')")
    else:
        out.append(line)

p.write_text("\n".join(out)+"\n", encoding="utf-8", newline="\n")
print("OK: dedup BOT ONLINE prints")
