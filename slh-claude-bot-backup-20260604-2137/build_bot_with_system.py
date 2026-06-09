import re

with open("bot.py", "r", encoding="utf-8") as f:
    code = f.read()

# --- 1) החלף את cmd_status בגרסה דואלית ---
old_status = r"@dp\.message\(Command\(\"status\"\)\)\s*async def cmd_status.*?\n\s*else:\s*\n\s*await msg\.answer\(\"משתמש לא נמצא\. הקלד /start\"\)"
new_status = """@dp.message(Command("status"))
async def cmd_status_report(msg: types.Message):
    if msg.from_user.id in ADMIN_IDS:
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
            f"📊 <b>דוח מערכת SLH v4.5</b>\\n"
            f"🔹 בסיס נתונים: {'✅' if db_ok else '❌'}\\n"
            f"🔹 אתר משקיעים: {site}\\n"
            f"🔹 גיבויים: {backups} קבצים\\n"
            f"🔹 זמן: {dt.datetime.now().strftime('%Y-%m-%d %H:%M')}"
        )
        await msg.answer(text)
    else:
        uid = msg.from_user.id
        async with pool.acquire() as conn:
            user = await conn.fetchrow("SELECT points, energy, tier FROM users WHERE telegram_id=$1", uid)
            if user:
                await msg.answer(f"📊 <b>סטטוס</b>\\n⭐ נקודות: {user['points']}\\n⚡ אנרגיה: {user['energy']}\\n🏅 רמה: {user['tier']}")
            else:
                await msg.answer("משתמש לא נמצא. הקלד /start")"""
code = re.sub(old_status, new_status, code, flags=re.DOTALL)

# --- 2) החלף את cmd_backup ---
old_backup = r"@dp\.message\(Command\(\"backup\"\)\)\s*async def cmd_backup.*?\n\s*await msg\.answer\(\"💾 גיבוי \(בקרוב\)\"\)"
new_backup = """@dp.message(Command("backup"))
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
        await msg.answer(f"❌ שגיאה: {str(e)[:200]}")"""
code = re.sub(old_backup, new_backup, code, flags=re.DOTALL)

# --- 3) הוסף /deploy ---
if "@dp.message(Command(\"deploy\"))" not in code:
    new_deploy = """
@dp.message(Command("deploy"))
async def cmd_deploy_system(msg: types.Message):
    if msg.from_user.id not in ADMIN_IDS:
        return await msg.answer("⛔ גישת מנהל בלבד.")
    await msg.answer("🚀 Deploy זמין רק דרך Git. האתר מתעדכן אוטומטית.")"""
    code = code.replace("# ====================== AI Fallback ======================", new_deploy + "\n# ====================== AI Fallback ======================")

with open("bot.py", "w", encoding="utf-8") as f:
    f.write(code)

print("✅ /status, /backup, /deploy updated")
