from pathlib import Path

code = r"""# SLH_BOT_STABLE (reset, includes /myid, resilient polling)
import os, sys, asyncio, logging
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import ReplyKeyboardBuilder

# UTF-8 safety (Windows)
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
    handlers=[logging.FileHandler(RUNTIME_LOG, encoding="utf-8"),
              logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger("slh")
logging.getLogger("aiogram").setLevel(logging.INFO)

def main_kb():
    kb = ReplyKeyboardBuilder()
    kb.button(text="Profile")
    kb.button(text="Balance")
    kb.button(text="About")
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
            # Do NOT crash on network disconnects
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
        await m.answer("OK: bot online", reply_markup=main_kb())

    @dp.message(Command("myid"))
    async def myid_cmd(m: types.Message):
        uid = m.from_user.id if m.from_user else 0
        await m.answer(f"MY_ID: {uid}")

    @dp.message(Command("health"))
    async def health_cmd(m: types.Message):
        await m.answer("OK")

    @dp.message(F.text == "About")
    async def about(m: types.Message):
        await m.answer("About: coming soon")

    log.info("BOOT: starting")
    await run_polling_forever(dp, bot)

if __name__ == "__main__":
    asyncio.run(main())
"""
Path("main.py").write_text(code.replace("\r\n","\n") + ("\n" if not code.endswith("\n") else ""), encoding="utf-8", newline="\n")
print("OK: main.py reset to stable version (with /myid)")
