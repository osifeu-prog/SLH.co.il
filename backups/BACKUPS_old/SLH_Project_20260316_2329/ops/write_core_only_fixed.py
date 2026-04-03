from pathlib import Path

code = r"""# SLH_BOT_CORE_ONLY (stable core, admin ops, polling retry)
import os, sys, asyncio, logging
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import ReplyKeyboardBuilder

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

LOG_DIR = os.path.join(os.path.dirname(__file__), "logs")
os.makedirs(LOG_DIR, exist_ok=True)
RUNTIME_LOG = os.path.join(LOG_DIR, "runtime.log")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    handlers=[
        logging.FileHandler(RUNTIME_LOG, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger("slh")
logging.getLogger("aiogram").setLevel(logging.INFO)

def is_admin(user_id: int) -> bool:
    return str(user_id) == os.getenv("ADMIN_USER_ID","").strip()

def tail_runtime(n_lines: int = 120) -> str:
    try:
        with open(RUNTIME_LOG, "r", encoding="utf-8", errors="replace") as f:
            lines = f.read().splitlines()[-n_lines:]
        txt = "\n".join(lines)
        return txt[-3500:]
    except Exception as e:
        return "tail error: " + repr(e)

def main_kb():
    kb = ReplyKeyboardBuilder()
    kb.button(text="About")
    kb.button(text="Health")
    kb.adjust(2)
    return kb.as_markup(resize_keyboard=True)

async def run_polling_forever(dp: Dispatcher, bot: Bot):
    delay = 1
    while True:
        try:
            log.info("POLLING: start (delay=%s)", delay)
            await dp.start_polling(bot)
            delay = 1
        except Exception as e:
            log.error("POLLING ERROR: %s", repr(e))
            await asyncio.sleep(delay)
            delay = min(delay * 2, 60)

async def main():
    load_dotenv()
    token = os.getenv("BOT_TOKEN","").strip()
    if not token:
        raise SystemExit("BOT_TOKEN missing in .env")

    bot = Bot(token=token)
    dp = Dispatcher()

    @dp.message(Command("start"))
    async def start_cmd(m: types.Message):
        await m.answer("OK: bot online (core-only)", reply_markup=main_kb())

    @dp.message(Command("myid"))
    async def myid_cmd(m: types.Message):
        uid = m.from_user.id if m.from_user else 0
        await m.answer(f"MY_ID: {uid}")

    @dp.message(Command("health"))
    async def health_cmd(m: types.Message):
        await m.answer("OK")

    @dp.message(F.text == "Health")
    async def health_btn(m: types.Message):
        await m.answer("OK")

    @dp.message(F.text == "About")
    async def about_btn(m: types.Message):
        await m.answer("About: coming soon")

    @dp.message(Command("admin"))
    async def admin_cmd(m: types.Message):
        uid = m.from_user.id if m.from_user else 0
        if not is_admin(uid):
            return await m.answer("Forbidden")
        kb = types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text="Restart", callback_data="adm:restart")],
            [types.InlineKeyboardButton(text="Tail Logs", callback_data="adm:tail")],
        ])
        await m.answer("Admin panel:", reply_markup=kb)

    @dp.callback_query(F.data == "adm:tail")
    async def adm_tail(cb: types.CallbackQuery):
        uid = cb.from_user.id if cb.from_user else 0
        if not is_admin(uid):
            return await cb.answer("Forbidden", show_alert=True)
        await cb.message.answer(tail_runtime(160))
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
                creationflags=0x08000000
            )
            await cb.message.answer("Restart requested.")
        except Exception as e:
            await cb.message.answer("Restart failed: " + repr(e))
        await cb.answer()

    log.info("BOOT: starting core-only")
    await run_polling_forever(dp, bot)

if __name__ == "__main__":
    asyncio.run(main())
"""

Path("main.py").write_text(code.replace("\r\n","\n") + ("\n" if not code.endswith("\n") else ""), encoding="utf-8", newline="\n")
print("OK: wrote correct CORE-ONLY main.py")
