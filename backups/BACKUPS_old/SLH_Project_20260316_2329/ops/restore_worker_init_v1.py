from pathlib import Path

p = Path("worker.py")
s = p.read_text(encoding="utf-8", errors="replace").replace("\r\n", "\n")

anchor = 'async def render_profile_text(user_id: int) -> str:' + "\n"
if anchor not in s:
    raise SystemExit("anchor not found: render_profile_text")

if 'dp = Dispatcher()' in s or 'bot = Bot(' in s:
    raise SystemExit("init block already exists; stopping to avoid duplicate patch")

insert_block = '''
bot = Bot(BOT_TOKEN)
dp = Dispatcher()

dp.include_router(claim_router)
dp.include_router(tasks_router)
dp.include_router(invite_router)
dp.include_router(withdraw_router)
dp.include_router(withdrawals_router)
dp.include_router(ton_admin_router)

'''

idx = s.index(anchor)
new_s = s[:idx] + insert_block + s[idx:]

p.write_text(new_s, encoding="utf-8", newline="\n")
print("worker.py restored: bot/dp/router init block")