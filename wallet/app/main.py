import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .db import init_db
from .routers import wallet as wallet_router
from .telegram_bot import router as telegram_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
)

app = FastAPI(title="SLH Community Wallet", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def on_startup():
    init_db()
    # Start Telegram bot in polling mode
    import asyncio
    from .telegram_bot import get_application
    try:
        tg_app = await get_application()
        await tg_app.bot.delete_webhook(drop_pending_updates=True)
        await tg_app.start()
        asyncio.create_task(tg_app.updater.start_polling(drop_pending_updates=True))
        logging.getLogger("slh_wallet").info("Telegram bot started in polling mode")
    except Exception as e:
        logging.getLogger("slh_wallet").error("Failed to start Telegram bot: %s", e)


@app.get("/health")
async def health():
    return {"status": "ok"}


app.include_router(wallet_router.router)
app.include_router(telegram_router)
