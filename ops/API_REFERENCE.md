# SLH Spark · API Reference
**Purpose:** Catalog of endpoints by group. For full operational context, see [OPS_RUNBOOK.md §3](OPS_RUNBOOK.md).
**Auto-gen:** blocked — Railway hides `/openapi.json` (FastAPI `docs_url=None, openapi_url=None` config). Regenerate manually by reading `api/main.py` + `routes/*.py` decorators.

---

## Base URL
`https://slh-api-production.up.railway.app`

## Auth layers
| Header / body field | Used by | Source of truth |
|--------------------|---------|-----------------|
| `X-Admin-Key: <key>` | admin endpoints | `ADMIN_API_KEYS` env (comma-sep) |
| `X-Broadcast-Key: <key>` | `/api/ops/*`, `/api/broadcast/*` (some) | `ADMIN_BROADCAST_KEY` env (default `slh-broadcast-2026-change-me`) |
| `admin_key` in request body | legacy (`/api/broadcast/send`) | matches either of the above |
| `Authorization: Bearer <jwt>` | user-scoped routes | `JWT_SECRET` env |
| `X-Device-Token: <hmac>` | `/api/esp/*`, device endpoints | per-device in NVS |

---

## Endpoint groups

### Public (no auth)
Most of the 113+ endpoints are public-read or token-gated. Common:
- `GET  /api/health` — liveness + DB status
- `GET  /api/prices` — coin prices (BNB, BTC, ETH, SOL, TON, XRP, DOGE)
- `GET  /api/stats` — ecosystem counters
- `GET  /api/academia/courses` — course catalog
- `GET  /api/community/posts?limit=50` — community feed
- `GET  /api/community/stats` — member + post totals
- `GET  /api/sudoku/leaderboard?period=weekly&limit=5`
- `GET  /api/aic/stats` — AIC token stats
- `GET  /api/events/public?limit=30` — public event feed (live from `event_log`)
- `GET  /api/performance` / `/api/performance/digest` — research data
- `GET  /api/openapi.json` → 404 (intentionally disabled; this file is the reference)

### User-scoped (Bearer or uid param)
- `GET  /api/user/{telegram_id}` — resolve Telegram ID → SLH user
- `GET  /api/wallet/{user_id}` — wallet summary
- `GET  /api/wallet/{user_id}/balances` — token balances
- `GET  /api/wallet/{user_id}/transactions` — tx history
- `GET  /api/staking/positions/{user_id}` — active stakes
- `GET  /api/referral/tree/{user_id}` — referral graph (10 gens)
- `GET  /api/payment/status/{user_id}` — payment history + license state
- `POST /api/registration/unlock` — beta coupon redemption or admin override

### Device (HMAC)
- `POST /api/device/register` — first-boot pairing (phone + 6-digit code flow)
- `POST /api/device/verify` — claim QR pairing
- `GET  /api/esp/commands/{device_id}` — pull next queued command
- `POST /api/esp/commands/{device_id}` — [admin] queue command for device
- `POST /api/device/heartbeat` — last_seen ping

### Admin (X-Admin-Key)
- `GET  /api/admin/devices/list`
- `GET  /api/admin/events?limit=50`
- `GET  /api/admin/dashboard` — admin home
- `POST /api/admin/rotate-key` — rotate admin key in DB
- `POST /api/admin/link-phone-tg` — link phone to Telegram (fixed 2026-04-21)
- `POST /api/broadcast/publish` — multi-network (Telegram/Discord/Twitter/LI/FB) — body `admin_key`
- `POST /api/broadcast/send` — Telegram-only send with `target` / `custom_ids` / `dry_run`
- `POST /api/broadcast/telegram` — Telegram-only shortcut

### Ops (X-Broadcast-Key)
- `GET  /api/ops/reality` — single source of truth admin dump (founders/community/deposits/payments/licenses/courses/broadcasts)
- `POST /api/ops/credit` — manual credit user
- `POST /api/ops/approve-payment` — approve a pending payment
- `POST /api/ops/ban` — ban user

### Ambassador CRM (X-Admin-Key) — **NEW 2026-04-21, pending Railway deploy**
- `POST   /api/ambassador/contacts` — create contact
- `GET    /api/ambassador/contacts?ambassador_id=<tg>&status=<>&search=<>&limit=50&offset=0` — list
- `PATCH  /api/ambassador/contacts/{id}` — partial update (only non-null fields)
- `POST   /api/ambassador/contacts/import` — bulk CSV import (multipart, `ambassador_id` form field)
- `GET    /api/ambassador/stats/{ambassador_id}` — pipeline summary by status

Table: `ambassador_contacts` (created idempotently on first API call).

### Treasury (X-Admin-Key for mutations)
- `GET  /api/treasury/summary` — revenue + buybacks + burns
- `GET  /api/treasury/buybacks` — chronological log
- `GET  /api/treasury/burns` — chronological log
- `POST /api/treasury/buyback/log` — [admin] log manual buyback
- `POST /api/treasury/burn/log` — [admin] log manual burn
- `POST /api/treasury/aic/burn` — [admin] execute AIC burn

### Misc routes (from `routes/*.py`)
Each module declares its own router. Brief list:
- `routes/ai_chat.py` — AI assistant (chat + metered AIC)
- `routes/payments_auto.py` — auto-verify TON/BNB payments
- `routes/payments_monitor.py` — background monitor
- `routes/community_plus.py` — feed + reactions + threads
- `routes/aic_tokens.py` — AIC mint/burn/rewards
- `routes/pancakeswap_tracker.py` — on-chain price/volume tracker
- `routes/sudoku.py` — puzzle engine + leaderboard
- `routes/dating.py` — @G4meb0t_bot matching
- `routes/love_tokens.py` — symbolic tokens
- `routes/creator_economy.py` — creator flows
- `routes/wellness.py` / `routes/threat.py` / `routes/whatsapp.py`
- `routes/system_audit.py` — internal audit endpoints
- `routes/agent_hub.py` — agent orchestration
- `routes/campaign_admin.py` — campaigns
- `routes/academia_ugc.py` — UGC for courses
- `routes/bot_registry.py` — bot metadata
- `routes/admin_rotate.py` — admin key rotation
- `routes/ambassador_crm.py` — **NEW** (see above)

---

## Conventions

### Errors
- `403` = auth required / invalid key
- `404` = endpoint not mounted (Railway deploy stale) OR resource not found
- `422` = pydantic validation error (missing/bad body field)
- `500` = server error (check Railway logs)
- `503` = degraded (DB disconnected — from `/api/health` fail-fast)

### Idempotency
Most DB-writing endpoints use `CREATE TABLE IF NOT EXISTS ...` + `INSERT ... ON CONFLICT ...` — safe to retry on network failures.

### Pagination
`?limit=<1-200>&offset=<N>` is the standard on list endpoints. Default limit varies (usually 50).

### Date format
All timestamps ISO-8601 UTC: `2026-04-22T03:15:00Z`.

---

## Regeneration (manual, since `/openapi.json` is disabled)

```powershell
# Quick: grep all FastAPI decorators
grep -rE '@(app|router)\.(get|post|patch|put|delete)\(' api/main.py routes/ main.py | grep -oE "'[^']+'" | sort -u
```

Automated regeneration is a TODO — `scripts/gen_api_reference.py` not yet written. Would need to:
1. Parse `api/main.py` AST for `@app.<verb>` decorators
2. Read each route module for `@router.<verb>`
3. Combine + emit markdown

For now: when you add a new endpoint, also add a line to this file manually.

---

Last updated: 2026-04-22 (after CRM Phase 0 module added).
