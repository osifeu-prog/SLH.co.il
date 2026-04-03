from pathlib import Path

p = Path("worker.py")
s = p.read_text(encoding="utf-8", errors="replace").replace("\r\n", "\n")

anchor = 'async def render_profile_text(user_id: int) -> str:\n'
if anchor not in s:
    raise SystemExit("anchor not found: render_profile_text")

checks = [
    '@dp.message(Command("start"))',
    '@dp.message(F.text == "About")',
    '@dp.message(F.text == "Health")',
    '@dp.message(F.text == "Balance")',
]
for c in checks:
    if c in s:
        raise SystemExit(f"handler already exists: {c}")

insert_block = '''
@dp.message(Command("start"))
async def start_cmd(m: types.Message, command: CommandObject | None = None):
    uid = m.from_user.id if m.from_user else 0
    username = m.from_user.username if m.from_user else None
    await ensure_user_exists(uid, username)

    ref_code = None
    if command and command.args:
        ref_code = command.args.strip()

    if ref_code:
        await attach_referrer(uid, ref_code)

    logger.info("HANDLER: /start by %s args=%s", uid, ref_code)
    await m.answer("OK: bot online (worker)", reply_markup=main_kb())


@dp.message(F.text == "About")
async def about_btn(m: types.Message):
    logger.info("HANDLER: About btn")
    await m.answer("About: coming soon")


@dp.message(F.text == "Health")
async def health_btn(m: types.Message):
    logger.info("HANDLER: Health btn")
    await m.answer("OK")


@dp.message(F.text == "Balance")
async def balance_btn(m: types.Message):
    uid = m.from_user.id if m.from_user else 0
    username = m.from_user.username if m.from_user else None
    await ensure_user_exists(uid, username)
    bal = await get_balance(uid)
    logger.info("HANDLER: Balance btn by %s", uid)
    await m.answer(
        f"Balance\\n\\nAvailable: {bal['available']:.8f} SLH\\nLocked: {bal['locked']:.8f} SLH"
    )


@dp.message(Command("balance"))
async def balance_cmd(m: types.Message):
    uid = m.from_user.id if m.from_user else 0
    username = m.from_user.username if m.from_user else None
    await ensure_user_exists(uid, username)
    bal = await get_balance(uid)
    logger.info("HANDLER: /balance by %s", uid)
    await m.answer(
        f"Balance\\n\\nAvailable: {bal['available']:.8f} SLH\\nLocked: {bal['locked']:.8f} SLH"
    )


'''

idx = s.index(anchor)
new_s = s[:idx] + insert_block + s[idx:]

p.write_text(new_s, encoding="utf-8", newline="\n")
print("worker.py restored: start/about/health/balance handlers")