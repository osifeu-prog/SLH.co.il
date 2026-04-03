from pathlib import Path
import re

p = Path("webhook_server.py")
s = p.read_text(encoding="utf-8").replace("\r\n", "\n")

# remove misplaced aliases from end of file
s = re.sub(
    r'\n@app\.get\("/health"\)\nasync def health_alias\(\):\n    return await healthz\(\)\n\n@app\.get\("/readyz"\)\nasync def readyz_alias\(\):\n    return await healthz\(\)\n?',
    '\n',
    s,
    flags=re.MULTILINE
)

anchor = '''@app.get("/healthz")
async def healthz():
    return {"ok": True, "mode": "webhook->redis->worker"}
'''

insert = anchor + '''
@app.get("/health")
async def health_alias():
    return await healthz()

@app.get("/readyz")
async def readyz_alias():
    return await healthz()
'''

if anchor not in s:
    raise SystemExit("healthz anchor not found")

s = s.replace(anchor, insert, 1)

p.write_text(s, encoding="utf-8", newline="\n")
print("FIXED webhook_server.py")
