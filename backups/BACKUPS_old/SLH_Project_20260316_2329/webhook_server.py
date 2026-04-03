import os
import sys
import logging
from pathlib import Path
from logging.handlers import RotatingFileHandler

from dotenv import load_dotenv
from fastapi import FastAPI, Request, Header
import uvicorn

from app.queue.redis_queue import enqueue_update

ROOT = Path(__file__).resolve().parent
LOG_DIR = ROOT / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

RUNTIME_LOG = str(LOG_DIR / "runtime_webhook.log")

fmt = logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")
fh = RotatingFileHandler(RUNTIME_LOG, maxBytes=2_000_000, backupCount=10, encoding="utf-8")
sh = logging.StreamHandler(sys.stdout)
fh.setFormatter(fmt)
sh.setFormatter(fmt)

logging.getLogger().handlers.clear()
logging.getLogger().addHandler(fh)
logging.getLogger().addHandler(sh)
logging.getLogger().setLevel(logging.INFO)
logger = logging.getLogger("slh.webhook")

load_dotenv(ROOT / ".env", override=True)

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "").strip()
RELEASE_SHA = os.getenv("RELEASE_SHA", "dev")

if not BOT_TOKEN:
    raise SystemExit("BOT_TOKEN missing in .env")

app = FastAPI()

@app.post("/tg/webhook")
async def tg_webhook(
    request: Request,
    x_telegram_bot_api_secret_token: str | None = Header(default=None),
):
    if WEBHOOK_SECRET and x_telegram_bot_api_secret_token != WEBHOOK_SECRET:
        logger.warning("bad webhook secret")
        return {"ok": False, "err": "bad secret"}

    data = await request.json()
    msg_id = await enqueue_update(data)
    logger.info("ENQUEUED update msg_id=%s", msg_id)
    return {"ok": True, "queued": True, "msg_id": msg_id}

@app.get("/healthz")
async def healthz():
    return {"ok": True, "mode": "webhook->redis->worker", "release": RELEASE_SHA}

@app.get("/health")
async def health_alias():
    return await healthz()

@app.get("/readyz")
async def readyz_alias():
    return await healthz()

if __name__ == "__main__":
    uvicorn.run(app, host=os.getenv("HOST", "0.0.0.0"), port=int(os.getenv("PORT", "8080")), log_level="info")
