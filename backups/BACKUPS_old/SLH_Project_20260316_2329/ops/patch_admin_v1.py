from pathlib import Path
import re

p = Path("main.py")
s = p.read_text(encoding="utf-8", errors="replace").replace("\r\n","\n")

if "SLH_ADMIN_PANEL_V1" in s:
    print("OK: admin panel already present")
    raise SystemExit(0)

# insert helpers near logger (log = logging.getLogger("slh"))
anchor = 'log = logging.getLogger("slh")'
if anchor not in s:
    raise SystemExit("anchor logger not found")

helpers = r'''
# SLH_ADMIN_PANEL_V1
def is_admin(user_id: int) -> bool:
    return str(user_id) == os.getenv("ADMIN_USER_ID","").strip()

def tail_runtime(n_lines: int = 80) -> str:
    try:
        with open(RUNTIME_LOG, "r", encoding="utf-8", errors="replace") as f:
            lines = f.read().splitlines()[-n_lines:]
        txt = "\n".join(lines)
        return txt[-3500:]  # telegram-safe
    except Exception as e:
        return "tail error: " + repr(e)
'''
s = s.replace(anchor, anchor + "\n" + helpers.strip("\n") + "\n")

# insert /admin handlers before log.info("BOOT: starting")
insert_anchor = 'log.info("BOOT: starting")'
if insert_anchor not in s:
    raise SystemExit("anchor BOOT not found")

admin_block = r'''
    # --- Admin commands
    @dp.message(Command("admin"))
    async def admin_cmd(m: types.Message):
        uid = m.from_user.id if m.from_user else 0
        if not is_admin(uid):
            return await m.answer("Forbidden")
        kb = types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text="Restart", callback_data="adm:restart")],
            [types.InlineKeyboardButton(text="Tail Logs", callback_data="adm:tail")],
            [types.InlineKeyboardButton(text="Stats", callback_data="adm:stats")],
        ])
        await m.answer("Admin panel:", reply_markup=kb)

    @dp.callback_query(F.data == "adm:tail")
    async def adm_tail(cb: types.CallbackQuery):
        uid = cb.from_user.id if cb.from_user else 0
        if not is_admin(uid):
            return await cb.answer("Forbidden", show_alert=True)
        await cb.message.answer(tail_runtime(140))
        await cb.answer()

    @dp.callback_query(F.data == "adm:stats")
    async def adm_stats(cb: types.CallbackQuery):
        uid = cb.from_user.id if cb.from_user else 0
        if not is_admin(uid):
            return await cb.answer("Forbidden", show_alert=True)
        # minimal stats now (we'll expand later)
        await cb.message.answer("Stats: OK (v1)")
        await cb.answer()

    @dp.callback_query(F.data == "adm:restart")
    async def adm_restart(cb: types.CallbackQuery):
        uid = cb.from_user.id if cb.from_user else 0
        if not is_admin(uid):
            return await cb.answer("Forbidden", show_alert=True)
        try:
            import subprocess
            subprocess.Popen(
                ["powershell","-NoProfile","-ExecutionPolicy","Bypass","-File", r"D:\SLH_PROJECT_V2\ops\restart.ps1"],
                creationflags=0x08000000  # CREATE_NO_WINDOW
            )
            await cb.message.answer("Restart requested.")
        except Exception as e:
            await cb.message.answer("Restart failed: " + repr(e))
        await cb.answer()

    @dp.message(Command("broadcast"))
    async def broadcast_cmd(m: types.Message):
        uid = m.from_user.id if m.from_user else 0
        if not is_admin(uid):
            return await m.answer("Forbidden")
        txt = m.text or ""
        parts = txt.split(" ", 1)
        if len(parts) < 2 or not parts[1].strip():
            return await m.answer("Usage: /broadcast <message>")
        msg = parts[1].strip()
        # v1: send to admin only (safe). Next step: user broadcast engine.
        await bot.send_message(uid, "BROADCAST PREVIEW: " + msg)
        await m.answer("Broadcast v1 sent to admin (preview).")
'''
s = s.replace(insert_anchor, admin_block.strip("\n") + "\n\n" + insert_anchor)

p.write_text(s + ("\n" if not s.endswith("\n") else ""), encoding="utf-8", newline="\n")
print("OK: admin panel v1 inserted")
