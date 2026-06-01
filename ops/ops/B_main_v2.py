"""
SLH Ecosystem API — FastAPI Backend v2.0
Modular entry point. All logic lives in routes/ and shared/.
This file: config, middleware, router registration, lifespan only.

Deploy: Railway builds from ROOT main.py — always sync:
  cp api/main.py main.py
"""
from __future__ import annotations

import asyncio
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from shared_db_core import init_db_pool, db_health

# ── Config ────────────────────────────────────────────────────────────────────

DATABASE_URL  = os.getenv("DATABASE_URL", "postgresql://postgres:slh_secure_2026@localhost:5432/slh_main")
JWT_SECRET    = os.getenv("JWT_SECRET", "")
ADMIN_USER_ID = int(os.getenv("ADMIN_USER_ID", "224223270"))
CORS_ORIGINS  = os.getenv(
    "CORS_ORIGINS",
    "https://slh-nft.com,http://localhost:8899,http://localhost:3000"
).split(",")

_ENV     = (os.getenv("ENV") or os.getenv("ENVIRONMENT") or "development").lower()
_IS_PROD = _ENV in ("prod", "production")
_DOCS    = os.getenv("DOCS_ENABLED", "0" if _IS_PROD else "1") == "1"

if not JWT_SECRET:
    import logging
    logging.warning("[Startup][WARN] JWT_SECRET is empty — auth endpoints will be degraded")

# ── Router imports ─────────────────────────────────────────────────────────────
# Each router owns its own set_pool() and optional init_tables().
# Pattern: from routes.X import router as X_router, set_pool as _X_pool [, init_tables as _X_init]

# — External routes/ files (already modular) —
from routes.ai_chat          import router as ai_chat_router,         set_aic_pool as _ai_chat_pool
from routes.payments_auto    import router as payments_router,         set_pool as _payments_pool
from routes.payments_monitor import router as payments_monitor_router, set_pool as _pm_pool, start_monitor as _pm_start
from routes.community_plus   import router as community_router,        set_pool as _community_pool
from routes.aic_tokens       import router as aic_router, admin_router as aic_admin_router, set_pool as _aic_pool
from routes.pancakeswap_tracker import router as ps_router,            set_pool as _ps_pool
from routes.sudoku           import router as sudoku_router,           set_pool as _sudoku_pool
from routes.dating           import router as dating_router,           set_pool as _dating_pool
from routes.broadcast        import router as broadcast_router,        set_pool as _broadcast_pool
from routes.love_tokens      import router as love_router,             set_pool as _love_pool
from routes.treasury         import router as treasury_router,         set_pool as _treasury_pool
from routes.creator_economy  import router as creator_router,          set_pool as _creator_pool
from routes.wellness         import router as wellness_router,         set_pool as _wellness_pool,    init_wellness_tables as _wellness_init
from routes.arkham_bridge    import router as threat_router,           set_pool as _threat_pool,      init_threat_tables as _threat_init
from routes.whatsapp         import router as whatsapp_router,         set_pool as _whatsapp_pool,    init_whatsapp_tables as _whatsapp_init
from routes.system_audit     import router as system_audit_router,     set_pool as _audit_pool
from routes.agent_hub        import router as agent_hub_router,        set_pool as _agent_hub_pool,   init_agent_hub_tables as _agent_hub_init
from routes.system_status    import router as system_status_router,    set_pool as _system_status_pool
from routes.investor_engine  import router as investor_router,         set_pool as _investor_pool
from routes.courses          import router as courses_router,          set_pool as _courses_pool
from routes.esp_events       import router as esp_events_router,       set_pool as _esp_pool
from routes.campaign_admin   import router as campaign_admin_router,   set_pool as _campaign_admin_pool
from routes.academia_ugc     import router as academia_ugc_router,     set_pool as _academia_ugc_pool, init_academia_ugc_tables as _academia_ugc_init
from routes.ambassador_crm   import router as ambassador_router,       set_pool as _ambassador_pool
from routes.therapists       import router as therapists_router,       set_pool as _therapists_pool
from routes.device_inventory import router as device_router,           set_pool as _device_pool
from routes.tasks            import router as tasks_router,            set_pool as _tasks_pool
from routes.bot_registry     import router as bot_registry_router,     set_pool as _bot_registry_pool, init_tables as _bot_registry_init
from routes.rotation_pipeline import router as rotation_router
from routes.admin_rotate     import (
    router as admin_rotate_router,
    set_pool as _admin_rotate_pool,
    init_admin_secrets_table as _admin_rotate_init,
    check_db_admin_key as _check_db_admin_key,
)

# — Inline routes extracted from main.py (NEW — see routes/TODO below) —
from routes.users            import router as users_router            # /api/user/*, /api/auth/*
from routes.staking          import router as staking_router          # /api/staking/*
from routes.wallet_routes    import router as wallet_router           # /api/wallet/*
from routes.marketplace      import router as marketplace_router      # /api/marketplace/*
from routes.tokenomics       import router as tokenomics_router       # /api/tokenomics/*
from routes.guardian         import router as guardian_router         # /api/guardian/*
from routes.reputation       import router as rep_router              # /api/rep/*
from routes.p2p              import router as p2p_router              # /api/p2p/*
from routes.experts          import router as experts_router          # /api/experts/*
from routes.bugs             import router as bugs_router             # /api/bugs/*
from routes.bank_transfer    import router as bank_router             # /api/bank-transfer/*
from routes.admin_ops        import router as admin_ops_router        # /api/admin/*, /api/ops/*
from routes.esp_devices      import router as esp_devices_router      # /api/esp/*, /api/device/*
from routes.analytics        import router as analytics_router        # /api/analytics/*
from routes.referral         import router as referral_router         # /api/referral/*
from routes.launch           import router as launch_router           # /api/launch/*
from routes.registration     import router as registration_router     # /api/registration/*
from routes.cex              import router as cex_router              # /api/cex/*
from routes.brokers          import router as brokers_router          # /api/brokers/, /api/deposits/*
from routes.member_card      import router as member_card_router      # /api/member-card/*
from routes.stats            import router as stats_router            # /api/stats, /api/prices, /api/health

from wellness_scheduler import init_wellness_scheduler

# ── Optional modules (fail-safe) ─────────────────────────────────────────────

def _try_import(module_path: str):
    """Import optional module — returns (module | None, bool)."""
    try:
        import importlib
        mod = importlib.import_module(module_path)
        return mod, True
    except Exception as e:
        import logging
        logging.warning("optional module %s unavailable: %s", module_path, e)
        return None, False

_telegram_gateway, _GATEWAY  = _try_import("api.telegram_gateway")
_swarm,            _SWARM    = _try_import("api.swarm")
_bots_catalog,     _CATALOG  = _try_import("api.admin_bots_catalog")
_expenses,         _EXPENSES = _try_import("api.expenses")
_secrets_vault,    _VAULT    = _try_import("api.admin_secrets_catalog")
_secret_alerts,    _ALERTS   = _try_import("api.admin_secret_alerts")
_public_security,  _PUBSEC   = _try_import("api.public_security_status")

# ── Rate limiter ──────────────────────────────────────────────────────────────
from collections import defaultdict, deque
import time as _time

_RL_MAX    = int(os.getenv("RATE_LIMIT_PER_MIN", "180"))
_RL_WIN    = 60.0
_RL_BYPASS = ("/api/health", "/docs", "/redoc", "/openapi.json", "/favicon")
_RL_BUCKETS: dict[str, deque] = defaultdict(deque)

# ── Lifespan ──────────────────────────────────────────────────────────────────

# All route modules that need a DB pool + optional init coroutine
_POOL_SETTERS = [
    _payments_pool, _pm_pool, _community_pool, _aic_pool,
    _ps_pool, _ai_chat_pool, _sudoku_pool, _dating_pool,
    _broadcast_pool, _love_pool, _treasury_pool, _creator_pool,
    _wellness_pool, _threat_pool, _whatsapp_pool, _audit_pool,
    _agent_hub_pool, _system_status_pool, _investor_pool,
    _courses_pool, _esp_pool, _campaign_admin_pool, _academia_ugc_pool,
    _ambassador_pool, _therapists_pool, _device_pool, _tasks_pool,
    _bot_registry_pool, _admin_rotate_pool,
]

_INIT_TABLES = [
    ("wellness",      _wellness_init),
    ("threat",        _threat_init),
    ("whatsapp",      _whatsapp_init),
    ("agent_hub",     _agent_hub_init),
    ("academia_ugc",  _academia_ugc_init),
    ("bot_registry",  _bot_registry_init),
    ("admin_rotate",  _admin_rotate_init),
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: init DB pool, wire all routes, run migrations. Shutdown: close pool."""
    pool = None
    try:
        pool = await init_db_pool(DATABASE_URL)
        app.state.db_pool = pool
    except Exception as e:
        import logging
        logging.critical("[Startup] DB pool failed: %r — API will degrade", e)

    if pool is not None:
        # Wire pool to all route modules
        for setter in _POOL_SETTERS:
            try:
                setter(pool)
            except Exception as e:
                import logging
                logging.warning("[Startup] set_pool %s failed: %r", setter.__name__, e)

        # Run table init (each isolated — one failure doesn't block others)
        for name, coro in _INIT_TABLES:
            try:
                await asyncio.wait_for(coro(), timeout=15.0)
                print(f"[Startup] {name} tables ✓")
            except Exception as e:
                print(f"[Startup][WARN] init_{name} failed: {e!r}")

        # Optional module pool wiring
        for mod, attr in [
            (_bots_catalog,    "set_pool"),
            (_expenses,        "set_pool"),
            (_secrets_vault,   "set_pool"),
            (_secret_alerts,   "set_pool"),
            (_public_security, "set_pool"),
        ]:
            if mod and hasattr(mod, attr):
                try:
                    getattr(mod, attr)(pool)
                except Exception:
                    pass

        # Wellness scheduler (APScheduler)
        try:
            await asyncio.wait_for(init_wellness_scheduler(DATABASE_URL), timeout=10.0)
            print("[Startup] Wellness scheduler ✓")
        except Exception as e:
            print(f"[Startup][WARN] wellness scheduler: {e!r}")

        # Payments monitor (background task)
        try:
            await _pm_start()
        except Exception as e:
            print(f"[Startup][WARN] payments monitor: {e!r}")

    yield  # ← app runs here

    if pool:
        await pool.close()
        print("[Shutdown] DB pool closed")


# ── App ───────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="SLH Ecosystem API",
    description="Backend for SLH Digital Investment House — Anti-Fraud DeFi Ecosystem",
    version="2.0.0",
    docs_url="/docs"  if _DOCS else None,
    redoc_url="/redoc" if _DOCS else None,
    openapi_url="/openapi.json" if _DOCS else None,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-Admin-Key", "X-Requested-With"],
)


# ── Rate limit middleware ─────────────────────────────────────────────────────

@app.middleware("http")
async def rate_limit(request, call_next):
    if not any(request.url.path.startswith(p) for p in _RL_BYPASS):
        ip  = request.client.host if request.client else "unknown"
        key = f"{ip}:{request.url.path.split('/')[2] if len(request.url.path.split('/')) > 2 else 'root'}"
        now = _time.monotonic()
        dq  = _RL_BUCKETS[key]
        while dq and dq[0] < now - _RL_WIN:
            dq.popleft()
        if len(dq) >= _RL_MAX:
            from fastapi.responses import JSONResponse
            return JSONResponse({"error": "rate_limited"}, status_code=429)
        dq.append(now)
    return await call_next(request)


# ── Register routers ──────────────────────────────────────────────────────────

# Extracted from main.py (new route files — see TODO section below)
for _r in [
    users_router,        # /api/user/*, /api/auth/*
    staking_router,      # /api/staking/*
    wallet_router,       # /api/wallet/*
    marketplace_router,  # /api/marketplace/*
    tokenomics_router,   # /api/tokenomics/*
    guardian_router,     # /api/guardian/*
    rep_router,          # /api/rep/*
    p2p_router,          # /api/p2p/*
    experts_router,      # /api/experts/*
    bugs_router,         # /api/bugs/*
    bank_router,         # /api/bank-transfer/*
    admin_ops_router,    # /api/admin/*, /api/ops/*
    esp_devices_router,  # /api/esp/*, /api/device/*
    analytics_router,    # /api/analytics/*
    referral_router,     # /api/referral/*
    launch_router,       # /api/launch/*
    registration_router, # /api/registration/*
    cex_router,          # /api/cex/*
    brokers_router,      # /api/brokers/, /api/deposits/*
    member_card_router,  # /api/member-card/*
    stats_router,        # /api/stats, /api/prices, /api/health
]:
    app.include_router(_r)

# Existing routes/ files
for _r in [
    ai_chat_router, payments_router, payments_monitor_router,
    community_router, aic_router, aic_admin_router, ps_router,
    sudoku_router, dating_router, broadcast_router, love_router,
    treasury_router, creator_router, wellness_router, threat_router,
    whatsapp_router, system_audit_router, agent_hub_router,
    system_status_router, investor_router, courses_router,
    esp_events_router, campaign_admin_router, academia_ugc_router,
    ambassador_router, therapists_router, device_router, tasks_router,
    bot_registry_router, rotation_router, admin_rotate_router,
]:
    app.include_router(_r)

# Optional module routers
for _mod, _attr in [
    (_swarm,          "router"),
    (_bots_catalog,   "router"),
    (_expenses,       "router"),
    (_secrets_vault,  "router"),
    (_secret_alerts,  "router"),
    (_public_security,"router"),
]:
    if _mod and hasattr(_mod, _attr):
        app.include_router(getattr(_mod, _attr))
