# -*- coding: utf-8 -*-
import os, asyncio, logging
log = logging.getLogger("safe_bot_launcher")

def launch_safely(name, token_var, build_func):
    token = os.getenv(token_var, "")
    if not token or token.strip() == "" or ":" not in token:
        log.warning(f"Skipping {name}  invalid/missing token ({token_var})")
        return
    try:
        app = build_func(token)
        loop = asyncio.get_event_loop()
        loop.create_task(app.run_polling())
        log.info(f"{name} started successfully")
    except Exception as e:
        log.error(f"Failed to start {name}: {e}")





