import re

with open("bot.py", "r", encoding="utf-8") as f:
    code = f.read()

# הפקודות החדשות
new_commands = r"""
# ====================== System Coordination (Admin) ======================
@dp.message(Command("status"))
async def cmd_status_report(msg: types.Message):
    if msg.from_user.id not in ADMIN_IDS:
        return await msg.answer("⛔ גישת מנהל בלבד.")
    import datetime as dt, glob
    db_ok = pool is not None
    site = "🔴 DOWN"
    try:
        import httpx
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get("https://slh-nft.com/investor-landing/")
            site = f"🟢 {resp.status_code}"
    except:
        pass
    backups = len(glob.glob("backups/*.zip"))
    text = (
        f"📊 <b>דוח מערכת SLH v4.5</b>\n"
        f"🔹 בסיס נתונים: {'✅' if db_ok else '❌'}\n"
        f"🔹 אתר משקיעים: {site}\n"
        f"🔹 גיבויים: {backups} קבצים\n"
        f"🔹 זמן: {dt.datetime.now().strftime('%Y-%m-%d %H:%M')}"
    )
    await msg.answer(text)

@dp.message(Command("backup"))
async def cmd_backup_system(msg: types.Message):
    if msg.from_user.id not in ADMIN_IDS:
        return await msg.answer("⛔ גישת מנהל בלבד.")
    import datetime as dt, zipfile, glob
    await msg.answer("💾 יוצר גיבוי...")
    try:
        ts = dt.datetime.now().strftime("%Y%m%d-%H%M")
        zip_name = f"backups/full_backup_{ts}.zip"
        with zipfile.ZipFile(zip_name, 'w') as zf:
            zf.write('bot.py')
            for f in glob.glob('backups/*.zip'):
                zf.write(f)
        await msg.answer(f"✅ גיבוי נשמר: {zip_name}")
    except Exception as e:
        await msg.answer(f"❌ שגיאה: {str(e)[:200]}")

@dp.message(Command("deploy"))
async def cmd_deploy_system(msg: types.Message):
    if msg.from_user.id not in ADMIN_IDS:
        return await msg.answer("⛔ גישת מנהל בלבד.")
    await msg.answer("🚀 Deploy זמין רק דרך Git. האתר מתעדכן אוטומטית.")
"""

# מיקום: אחרי @dp.message(Command("sales"))
pattern = r"(@dp\.message\(Command\(\"sales\"\)\).*?\n\s*await msg\.answer\(.*?\))"
code = re.sub(pattern, r"\1" + new_commands, code, count=1, flags=re.DOTALL)

with open("bot.py", "w", encoding="utf-8") as f:
    f.write(code)

print("✅ פקודות /status, /backup, /deploy נוספו ל‑bot.py")
