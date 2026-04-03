from pathlib import Path

p = Path("webhook_server.py")
s = p.read_text(encoding="utf-8")

if '@app.get("/health")' not in s:
    block = '''

@app.get("/health")
async def health_alias():
    return await healthz()

@app.get("/readyz")
async def readyz_alias():
    return await healthz()
'''
    s = s.rstrip() + block + "\n"

p.write_text(s, encoding="utf-8", newline="\n")
print("PATCHED webhook_server.py")
