# SLH Operations Runbook — 2026-04-21

Operational reference for the SLH Spark ecosystem. If something is broken, start here.

---

## 1. Start / stop the stack

### Full start (local)
```powershell
powershell -File D:\SLH_ECOSYSTEM\ops\slh-start.ps1
```
Runs: prereq check → git pull (non-destructive) → docker compose up → wait for Postgres + Redis → health matrix.

### Verify only (no restart)
```powershell
powershell -File D:\SLH_ECOSYSTEM\ops\slh-start.ps1 -Verify
```

### Stop
```powershell
powershell -File D:\SLH_ECOSYSTEM\ops\slh-start.ps1 -Stop
```
Runs `docker compose down` and kills any stuck `pio.exe` monitor processes.

### Skip flags
- `-SkipGit` — don't pull (use current local code)
- `-SkipDocker` — don't restart containers (use when you only need health-check)

---

## 2. System map (what runs where)

| Layer | Service | Location | Owner |
|-------|---------|----------|-------|
| Frontend (public) | slh-nft.com | GitHub Pages, repo `osifeu-prog/osifeu-prog.github.io` branch `main` | auto on push |
| Frontend (Mini Apps) | slh-nft.com/miniapp/* | Same GitHub Pages repo | auto on push |
| API | slh-api-production.up.railway.app | Railway, repo `osifeu-prog/slh-api` branch `master`, builds from **root** `main.py` | auto on push |
| Telegram bots (25) | Local docker compose + 2 on Railway | `D:\SLH_ECOSYSTEM\docker-compose.yml` | manual `docker compose up -d` |
| Postgres | `slh-postgres` container | docker compose | auto |
| Redis | `slh-redis` container | docker compose | auto |
| ESP32 devices | User premises | Firmware at `device-registry/esp32-cyd-work/firmware/slh-device-v3/` | flash via PlatformIO |
| Memory / Auto-memory | `C:\Users\Giga Store\.claude\projects\D--\memory\` | Claude Code sessions | per-session writes |

Repo sync rule: **Railway builds from root `main.py`, NOT `api/main.py`.** Always sync both before push:
```powershell
cp api\main.py main.py
git add main.py api\main.py
git commit -m "..."
git push
```

---

## 3. Core API reference (114 endpoints — top hits)

Public (no auth):
- `GET /api/health` — liveness + db status
- `GET /api/prices` — external coin prices `{BNB/BTC/ETH/SOL/TON/...}` as `{ils, usd}`
- `GET /api/stats` — ecosystem stats
- `GET /api/academia/courses` — course catalog
- `GET /api/events/public` — public event feed (currently `event_log_unavailable`; P0 fix pending)

User-scoped:
- `GET /api/user/{telegram_id}` — resolve Telegram ID to SLH user
- `GET /api/wallet/{user_id}` — wallet summary
- `GET /api/wallet/{user_id}/balances` — SLH/MNH/ZVK/REP balances
- `GET /api/wallet/{user_id}/transactions` — transaction history
- `GET /api/staking/positions/{user_id}` — active stakes
- `GET /api/referral/tree/{user_id}` — referral downline

Admin (requires `X-Admin-Key`):
- `GET /api/admin/devices/list` — registered ESP32 devices
- `GET /api/admin/dashboard` — admin home data
- `POST /api/broadcast/send` — send Telegram broadcast

Device:
- `POST /api/device/register` — ESP32 first boot
- `POST /api/device/verify` — QR pairing claim
- `GET /api/device/claim/{device_id}` — device status
- `POST /api/device/command/{device_id}` — queue command for device

Telegram Gateway (NEW — not wired yet):
- `api/telegram_gateway.py` — validates Mini App `initData` via HMAC-SHA256
- FastAPI dependencies: `verify_miniapp_request`, `verify_bot_request`, `require_admin`
- Not yet imported into `main.py` — next session task

---

## 4. Health matrix

| Service | Endpoint / Check | Expected | Current (2026-04-21) |
|---------|------------------|----------|----------------------|
| API liveness | `GET /api/health` | 200 + `db: connected` | ok |
| API prices | `GET /api/prices` | 200 + 7+ coins | ok |
| API stats | `GET /api/stats` | 200 | ok |
| Events feed | `GET /api/events/public` | 200 | **event_log_unavailable** — P0 bug |
| Performance feed | `GET /api/performance` | 200 + rows | **available: false** — CSV not on Railway |
| Website | `https://slh-nft.com` | 200 | ok |
| Mini App dashboard | `https://slh-nft.com/miniapp/dashboard.html` | 200 | **not deployed yet** — on slh-nft.com this path 404s until commit + push |
| Postgres (local) | `docker exec slh-postgres pg_isready` | exit 0 | check via slh-start |
| Redis (local) | `docker exec slh-redis redis-cli ping` | `PONG` | check via slh-start |

---

## 5. Data integrity rules (MUST follow)

These are non-negotiable. Per owner preference, any violation should be fixed on sight:

1. **No fake fallback data.** If an API returns nothing, render `--` or an error card — never invent values.
2. **No hardcoded numbers in UI for business metrics.** Balances, prices, counts must come from the API.
3. **No mock data in production pages.** Use `[DEMO]` or `test_` prefix if a demo is truly needed.
4. **All monetary operations are server-side.** Bot handlers and Mini Apps never compute balances, prices, or fees locally.
5. **Every Gateway-entered request audits to `event_log`.** Once `event_log` is online, this becomes mandatory.

Confirmed violations still open:
- `website/buy.html:333-334` — hardcoded `tokenPrices={SLH:122,...}` + `|| 122` fallback. Needs to pull from `/api/prices` (SLH not there — API needs `/api/wallet/price?token=SLH` first).

Confirmed violations already fixed this pass:
- `website/community.html:1728` — `|| { total_posts:7, active_today:47, ... }` replaced with `|| { ...: '—' }` (fix predates this session; verified present).

---

## 6. Deployment procedures

### API (Railway auto-deploy)
1. Edit `D:\SLH_ECOSYSTEM\main.py` (and `api/main.py` — keep identical).
2. Test locally: `uvicorn main:app --reload`.
3. Commit + push:
   ```powershell
   cd D:\SLH_ECOSYSTEM
   git add main.py api\main.py
   git commit -m "API: <change>"
   git push
   ```
4. Watch Railway dashboard — deploy takes ~2 min.
5. Verify: `curl https://slh-api-production.up.railway.app/api/health`.

### Website (GitHub Pages auto-deploy)
1. Edit `D:\SLH_ECOSYSTEM\website\<file>.html`.
2. Commit + push from the website directory (it is a **separate git repo**):
   ```powershell
   cd D:\SLH_ECOSYSTEM\website
   git add <files>
   git commit -m "website: <change>"
   git push
   ```
3. Pages publishes within ~60 seconds.
4. Verify: `curl -I https://slh-nft.com/<page>.html`.

### Docker bots
Rebuild and restart a single service:
```powershell
cd D:\SLH_ECOSYSTEM
docker compose up -d --build <service-name>
```

All services:
```powershell
docker compose up -d --build
```

### ESP32 firmware
```powershell
cd D:\SLH_ECOSYSTEM\device-registry\esp32-cyd-work\firmware\slh-device-v3
pio run
pio run -t upload --upload-port COM5
pio device monitor -p COM5 -b 115200
```

If COM5 is busy, close any open `pio device monitor` windows and retry. `slh-start.ps1 -Stop` also kills stuck `pio.exe` processes.

---

## 7. Security model

| Entry point | Identity proof | Where enforced |
|-------------|---------------|----------------|
| Public web page | None | n/a (no mutations allowed) |
| Mini App (`/miniapp/*`) | Telegram `initData` (HMAC-SHA256) | `api/telegram_gateway.verify_miniapp_request` (pending wire-in) |
| Bot update (aiogram) | Bot token trust + Telegram ID whitelist | Each bot's handler + `api/telegram_gateway.verify_bot_request` |
| ESP device | `X-Device-Token` header | Existing `main.py` device auth |
| Legacy admin | `X-Admin-Key: <ADMIN_API_KEYS>` header | `_require_admin()` in main.py |

### Admin keys (2026-04-21 state, rotate any visible value)
- `ADMIN_API_KEYS` on Railway: `slh_admin_2026_rotated_04_20, slh_ops_2026_rotated_04_20`
- `ADMIN_BROADCAST_KEY` on Railway: `slh-broadcast-2026-change-me` (default; rotate)
- Admin Telegram IDs: `224223270` (Osif; default in `api/telegram_gateway.ADMIN_TELEGRAM_IDS`)

### SMS (OTP) provider

Real SMS for device-pair OTPs is shipped via `api/sms_provider.py`. Pick **one** provider and set the env vars on Railway:

| Provider | Set `SMS_PROVIDER=` | Plus env vars |
|----------|---------------------|---------------|
| Twilio (global) | `twilio` | `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_FROM` |
| Inforu (Israel) | `inforu` | `INFORU_USERNAME`, `INFORU_API_TOKEN`, `INFORU_SENDER` (default `SLH`) |
| 019 Mobile (Israel) | `sms019` | `SMS019_USERNAME`, `SMS019_PASSWORD`, `SMS019_SENDER` (default `SLH`) |
| Dev (no-send) | `stub` | — |
| Refuse all | `disabled` | — |

Default if unset: `stub` locally, `disabled` on Railway. When `disabled` is active, `/api/device/register` returns `delivery: pending` and exposes `_dev_code` only when `DEV_EXPOSE_OTP=1`.

Check status without sending:
```python
from api.sms_provider import provider_status
print(provider_status())
```

### Swarm — independent device mesh API

Phase-1 endpoints from `ops/SWARM_V1_BLUEPRINT_20260424.md`. All under `/api/swarm/`.
Module: `api/swarm.py`. Wired into `main.py` via `app.include_router(_swarm.router)`,
gated behind `_SWARM_AVAILABLE` so a missing module can't block API boot.

| Verb + Path | Auth | Purpose |
|---|---|---|
| `POST /api/swarm/devices/register` | none (POC) | First-boot register: device_id + public_key + type. Idempotent. |
| `POST /api/swarm/devices/heartbeat` | none | Every 30s from device — updates last_heartbeat, RSSI, battery, peers_seen. |
| `POST /api/swarm/events` | none | Mesh events (button press, sensor reading, signed-tx). Mirrored to `/api/events/public`. |
| `GET  /api/swarm/devices/{id}/commands` | none | Device polls — returns queued commands, atomically marks delivered. |
| `POST /api/swarm/commands/queue` | **X-Admin-Key** | Admin queues a command for a device. TTL configurable. |
| `POST /api/swarm/commands/{id}/ack` | none | Device acks executing the command + optional result payload. |
| `GET  /api/swarm/devices` | none | List devices (no PII; just IDs + types + heartbeat + online flag). |
| `GET  /api/swarm/stats` | none | Snapshot for `/my.html` and `/miniapp/swarm.html` dashboards. |

**Tables auto-created on first hit** (ensure_schema): `swarm_devices`, `swarm_events`,
`swarm_commands`. Schema in `api/swarm.py`.

**Live verify after deploy:**
```powershell
curl.exe -s "https://slh-api-production.up.railway.app/api/swarm/stats"
# expected: {"total_devices":0,"online":0,"events_24h":0,"pending_commands":0}
```

**Mini App:** `/miniapp/swarm.html` — 4-tile stats + per-device list + command-broadcast input.

### Known security debt
- 3 admin endpoints in `main.py` still use `admin_secret` body field instead of `_require_admin()` header (registration approve @957, beta coupon @2344, marketplace approve @4782). P0 fix.
- JWT_SECRET + ADMIN_API_KEYS default to empty on startup with only a warning (should fail-fast in prod).
- CORS permits all methods — tighten to `GET, POST, OPTIONS` for public; stricter on admin.

---

## 8. Broadcast system

Two paths:

### Telegram broadcast (DM users)
```powershell
curl.exe -X POST https://slh-api-production.up.railway.app/api/broadcast/send `
  -H "X-Admin-Key: <ADMIN_BROADCAST_KEY>" `
  -H "Content-Type: application/json" `
  -d '{"message":"...","segment":"all"}'
```
Segments: `all`, `approved`, `premium`, `admins`.

### On-chain broadcast (event_log)
When `event_log` table is populated, events flow to `/api/events/public` → `/live.html` + Mini App dashboards. Currently returning `event_log_unavailable` — P0 fix pending (table creation).

---

## 9. Troubleshooting (common issues)

### "COM5 busy" when flashing ESP32
Cause: a stuck `pio device monitor` from a previous session.
Fix:
```powershell
powershell -File D:\SLH_ECOSYSTEM\ops\slh-start.ps1 -Stop
```
Or manually Task Manager → kill `pio.exe`. If "Access Denied", close the owning terminal.

### Mini App opens blank / login loop
Cause: Telegram `initData` validation failed (bad token or stale `auth_date` > 1h).
Check:
1. `BOT_TOKEN_<BOT_UPPER>` env var is set on Railway matching the bot that opened the Mini App.
2. Clock skew between client and server.
3. User's Telegram version (old clients send different `initData` formats).

### `event_log_unavailable`
Cause: `event_log` table not created, or column mismatch with `api/telegram_gateway._audit` schema.
Fix: run migration to create `event_log(event_type TEXT, telegram_id BIGINT, slh_user_id INTEGER, payload JSONB, created_at TIMESTAMPTZ DEFAULT NOW())`.

### `/api/performance` returns `available: false`
Cause: `backtest_full.py` scheduled task has not run on Railway; CSV missing from container.
Fix: either enable scheduled task or run `python daily_backtest.py` on Railway shell.

### ledger-bot crash loop
Cause: `docker-compose.yml` maps `TOKEN=${BOT_TOKEN}` but the service expects `LEDGER_BOT_TOKEN`.
Fix: edit compose to pass correct variable, `docker compose up -d ledger-bot`.

### Admin endpoint returns 403 when key was set
Cause: env var on Railway not loaded (container restarted with stale copy) or key has whitespace.
Check:
```powershell
curl.exe -H "X-Admin-Key: <key>" https://slh-api-production.up.railway.app/api/admin/devices/list
```
Should return JSON, not `{"detail":"Forbidden"}`.

---

## 10. Escalation / support

- **Primary support:** `@osifeu_prog` (Telegram) — same as owner.
- **Bug reports:** `/bug <text>` via main bot (creates ticket), or `website/bug-report.html` (web form).
- **Railway issues:** dashboard → project → deployments → inspect logs.
- **GitHub issues:** [osifeu-prog/slh-api/issues](https://github.com/osifeu-prog/slh-api/issues) (private repo).

Do NOT use `@SLHSupport` — that handle does not exist (common copy-paste error).

---

## 11. File map for the operator

Essential reads when dropping in cold:
- This file — how to run things
- [SESSION_HANDOFF_20260421_TELEGRAM_FIRST.md](SESSION_HANDOFF_20260421_TELEGRAM_FIRST.md) — what just shipped
- [TELEGRAM_FIRST_MIGRATION_PLAN.md](TELEGRAM_FIRST_MIGRATION_PLAN.md) — strategic direction
- [KNOWN_ISSUES.md](KNOWN_ISSUES.md) — verified backlog
- [AUDIT_FULL_20260421_COMPREHENSIVE.md](AUDIT_FULL_20260421_COMPREHENSIVE.md) — night-of audit (95 items)
- `D:\SLH_ECOSYSTEM\CLAUDE.md` — project instructions at repo root
- `C:\Users\Giga Store\.claude\projects\D--\memory\MEMORY.md` — auto-memory index (Claude-only, read by every session)
