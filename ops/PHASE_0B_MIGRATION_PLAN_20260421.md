# Phase 0B — Bot DB Migration Plan

**Started:** 2026-04-21
**Method:** one bot at a time. Each is a separate commit → separate deploy.

## Scope — 16 files use `asyncpg.create_pool` directly

### Individual bot entry points (4 files)
| File | Container | Status |
|------|-----------|--------|
| `academia-bot/bot.py` | slh-academia-bot | ✅ **MIGRATED** 717e3db (container down — needs restart) |
| `nfty-bot/main.py` | slh-nfty | ✅ **MIGRATED** 78a2ee3 |
| `osif-shop/inventory_db.py` | slh-osif-shop | ✅ **MIGRATED** dba134e |
| `expertnet-bot/banking.py` | expertnet stack | ✅ **MIGRATED** e1b560b |

### Root-level API scripts (5 files)
| File | Used by | Status |
|------|---------|--------|
| `broadcast_airdrop.py` | Admin broadcasts | ✅ **MIGRATED** e1b560b (try/fallback) |
| `wellness_scheduler.py` | API startup | ✅ **MIGRATED** e1b560b (try/fallback) |
| `shared/ledger_listener.py` | Ledger audit | ✅ **MIGRATED** e1b560b (try/fallback) |
| `shared/community_api.py` | Community features | ✅ **MIGRATED** e1b560b (try/fallback) |
| `shared/wallet_engine.py` | Wallet flows | ✅ **MIGRATED** e1b560b (try/fallback) |

### Shared library copies — unification target (10 files)
The `shared/slh_payments/` library is COPIED across 7 bots (anti-pattern):
- `shared/slh_payments/db.py` (canonical) ✅ **MIGRATED** e1b560b
- `wallet/shared/slh_payments/db.py` ✅ resynced e1b560b
- `factory/shared/slh_payments/db.py` ✅ resynced e1b560b
- `fun/shared/slh_payments/db.py` ✅ resynced e1b560b
- `admin-bot/shared/slh_payments/db.py` ✅ resynced e1b560b
- `botshop/shared/slh_payments/db.py` 🟡 **blocked** — `botshop` is a git submodule; migration needs a commit in its own repo
- `expertnet-bot/shared/slh_payments/db.py` ✅ resynced e1b560b
- `shared/slh_payments/ledger.py` (canonical) ✅ **MIGRATED** e1b560b
- `admin-bot/shared/slh_payments/ledger.py` ✅ resynced e1b560b
- `expertnet-bot/shared/slh_payments/ledger.py` ✅ resynced e1b560b

**Unification strategy:** canonical updated + resync done. Going forward, bump canonical and `cp` fan-out.

## Migration pattern per bot

```python
# 1. Copy shared_db_core.py into bot's dir (for Docker COPY . .)
# 2. In bot's main entry file:

# ADD import:
from shared_db_core import init_db_pool as _shared_init_db_pool

# REPLACE:
_pool = await asyncpg.create_pool(DATABASE_URL, min_size=1, max_size=5)
# WITH:
_pool = await _shared_init_db_pool(DATABASE_URL)

# 3. py_compile check
# 4. Commit + push (triggers auto-rebuild of that bot's Docker image)
# 5. D:\SLH_CONTROL.ps1 restart (or single-service restart)
```

## Trade-offs accepted

- `max_size` standardized from per-bot values (5, 10, 20) to **4** (from shared_db_core).
  - Rationale: 22 containers × max 4 = 88 connections, fits under Railway Postgres default limit.
  - Per-bot traffic is Telegram-bot level (low), 4 is plenty.
- `min_size` standardized to 1 (cold-start friendly).
- Health check with `SELECT 1` added at pool init — slightly slower boot, worth it.
- On DB connect failure: bot crashes (fail-fast) instead of running without pool.

## What's been done (2026-04-21)

### Evening batch (commit 717e3db)
- ✅ `academia-bot/shared_db_core.py` created (canonical)
- ✅ `academia-bot/bot.py` migrated
- 🟡 `slh-academia-bot` container NOT currently running in docker ps (22/22 healthy, academia missing) — needs `D:\SLH_CONTROL.ps1 restart` or rebuild

### Late-evening batch (commit 78a2ee3 + follow-up)
- ✅ `nfty-bot/shared_db_core.py` + `main.py` migrated (max_size 10→4)
- ✅ `osif-shop/shared_db_core.py` + `inventory_db.py` migrated (max_size 5→4)
- ✅ `routes/academia_ugc.py` — fixed column mismatch `created_at` → `purchased_at`
- ✅ `py_compile` clean on all 3 migrations
- 🟡 `slh-nfty` + `slh-osif-shop` are running — will auto-rebuild on Railway deploy of this commit; for local docker-compose, run `docker compose up -d --build nfty-bot osif-shop`

## Next session order (lowest risk first)

1. ✅ ~~Verify academia-bot restart succeeds~~ — migrated, container needs restart
2. ✅ ~~nfty-bot/main.py~~ — migrated, running
3. ✅ ~~osif-shop/inventory_db.py~~ — migrated, running
4. ✅ ~~expertnet-bot/banking.py~~ — migrated
5. ✅ ~~Canonical `shared/slh_payments/db.py` + resync all 6 bot copies~~ — 5/6 done, botshop submodule pending
6. ✅ ~~Root API scripts~~ — migrated (5/5)

### Remaining
- `botshop/shared/slh_payments/db.py` — submodule, separate commit in its own repo.
- Container restarts / rebuilds so the new code actually loads:
  - `slh-academia-bot` (currently down — `docker compose up -d --build academia-bot`)
  - `slh-nfty`, `slh-osif-shop`, expertnet, wallet, factory, fun, admin-bot after Railway redeploy of main.py (if applicable) and/or `docker compose up -d --build <service>` locally.

## Emergency rollback (per bot)

```bash
cd /d/SLH_ECOSYSTEM
git log --oneline academia-bot/bot.py | head -3
git revert <migration_commit>
git push
D:\SLH_CONTROL.ps1 restart
```

Or, localized:
```bash
git checkout HEAD~1 -- academia-bot/bot.py
rm academia-bot/shared_db_core.py
```
