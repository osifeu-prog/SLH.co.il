# 🚀 SLH Unified Chain — Launch Notes (2026-04-20)

> Execution of the plan in `ops/UNIFIED_CHAIN_DESIGN_20260420.md`. All 6 phases shipped code-complete.
> Runtime verification (Railway deploy + device flash + Guardian restart) requires Osif — tracked in "Osif actions" below.

---

## What was shipped

### Phase 1 — Foundation ✅
- **`shared/events.py`** (new) — durable PG-backed event bus. `emit()`, `fetch_since()`, `subscribe()`. No Redis dependency.
- **`shared/guardian_gate.py`** (new) — `check_zuz()` / `require_clean_zuz()` with 60s in-process cache, fail-open on DB error, Hebrew + English reason strings.
- **`POST /api/esp/heartbeat`** (new) — device-authenticated heartbeat, `Authorization: Bearer <signing_token>`. Writes to new `device_heartbeats` audit table. Throttled `device.heartbeat` event emission (1st, 100th, 500th, 1000th per day).
- **`GET  /api/esp/commands/{device_id}`** (new) — device polls pending admin commands (REBOOT, REVOKE, LED_*).
- **`POST /api/esp/commands/{device_id}`** (new, admin) — push a command into the device queue.
- **`GET  /api/device/claim/{device_id}`** (new) — device-side companion to web pairing. Single-use, 15-min window, auto-expires after first heartbeat.
- **`POST /api/device/verify`** — now emits `device.registered` event.
- **`device_commands`** + **`device_heartbeats`** + **`event_log`** tables created on first write (idempotent `CREATE TABLE IF NOT EXISTS`).

### Phase 2 — Guardian bot ↔ slh-api bridge ✅
Repo: `osifeu-prog/slh-guardian` (at `D:\telegram-guardian-DOCKER-COMPOSE-ENTERPRISE\`)
- **`bot/slh_api_client.py`** (new) — httpx client covering `/api/guardian/{report,check,blacklist,scan-message,stats}` + `/api/health`. Fail-silent, best-effort.
- **`bot/commands/guardian_ops.py`** (new) — 7 admin commands: `/gr_ping`, `/gr_check <uid>`, `/gr_report <uid> <reason>`, `/gr_report_high ...`, `/gr_blacklist`, `/gr_scan <text>`, `/gr_stats`.
- **`bot/main.py`** — registers the 7 new handlers at startup.

### Phase 3 — ZUZ enforcement + Academia 70/30 payout ✅
- **`/api/wallet/send`** — now calls `require_clean_zuz()` before transfer; `X-Admin-Override-ZUZ` header bypass.
- **`/api/wallet/deposit`** — same.
- **`/api/staking/stake`** — same.
- **`/api/staking/stake`** — emits `stake.opened` event on successful pending_approval insert.
- **`routes/academia_ugc.py`**:
  - `EarningsPayoutIn` model added.
  - **`POST /api/academy/earnings/mark-paid`** (new, admin) — closes the 70/30 loop. Takes `earnings_id` + `payout_tx`, marks `paid_out=TRUE`, records tx. Idempotent. Emits `academy.payout_made`. Ensures `payout_note` column via `ADD COLUMN IF NOT EXISTS`.

### Phase 4 — Ledger-bot event listener ✅
- **`shared/ledger_listener.py`** (new) — asyncio task polling `event_log` every 3s. Cursor persisted to `/app/data/ledger_cursor.json`. Handlers for: `payment.cleared`, `stake.opened`, `stake.unlocked`, `device.registered`, `academy.payout_made`, `guardian.alert`.
- **`shared/bot_template.py`** — conditional `asyncio.create_task(ledger_listener.run(bot))` when `BOT_KEY == "ledger"`. No impact on the other 24 bots.
- Env needed: `LEDGER_WORKERS_CHAT_ID` (TG group id where ops fanout goes). If missing, listener runs silently but still consumes events.

### Phase 5 — Firmware v3 + pairing flow ✅
- **`device-registry/esp32-cyd-work/firmware/slh-device-v3/`** (new PlatformIO project):
  - `platformio.ini` with build_flags for `SLH_API_HOST`, `SLH_LOCAL_BRIDGE`, `SLH_PAIR_URL`, `SLH_FW_TAG`.
  - `src/main.cpp` (~260 lines): QR pairing screen, NVS-persisted `device_id`/`signing_token`/`user_id`, heartbeat to Railway (Bearer auth) with local bridge fallback, balance fetch every 60s (top 3 tokens SLH/MNH/ZVK on TFT), command poll every 15s (REBOOT/REVOKE handled), 3s long-press factory reset.
- **`website/device-pair.html`** (new) — mobile-friendly Hebrew pairing page. Reads MAC from URL, phone → `/api/device/register` → code → `/api/device/verify`. Device polls `/api/device/claim/{device_id}` and self-activates within 5s.
- **`FLASH_INSTRUCTIONS.md`** — step-by-step for Osif to flash the device, pair it, and roll back to v2 if needed.

### Phase 6 — chain-status.html + this launch doc ✅
- **`website/chain-status.html`** (new) — single-page dashboard, 5 summary nodes + 3 detail tables. Pulls from `/api/health`, `/api/admin/devices/list`, `/api/guardian/blacklist`, `/api/tokenomics/stats`, `/api/staking/plans`. Auto-refresh every 15s. Admin key from `localStorage.slh_admin_password` (existing pattern).
- **`ops/UNIFIED_CHAIN_LAUNCH_20260420.md`** — this doc.

---

## What's NOT yet live (Osif actions)

| # | Action | Why blocked |
|---|--------|-------------|
| 1 | `git push` `slh-api` master | I wrote the code; I don't push without explicit confirmation in session. Now that approval is given, push is next. |
| 2 | `git push` `osifeu-prog.github.io` main | Same. |
| 3 | `git push` `slh-guardian` main | Same. |
| 4 | Railway redeploy (automatic on push of slh-api) | Post-push, wait ~90s. Verify with `curl slh-api-production.up.railway.app/api/health`. |
| 5 | Rotate `GUARDIAN_BOT_TOKEN` via @BotFather | Leaked in .env.secrets.local (per memory). Osif updates Railway + local .env. |
| 6 | Set Railway env var `LEDGER_WORKERS_CHAT_ID` | Needed for Phase 4 fanout. Until set, listener runs silently. |
| 7 | Set Railway env var `SLH_ADMIN_KEY` inside Guardian bot container | Needed for Phase 2 mirror calls. |
| 8 | Flash firmware v3 to the device at 10.0.0.4 | Per `FLASH_INSTRUCTIONS.md`. Physical USB required. |
| 9 | Pair the device via `https://slh-nft.com/device-pair.html?mac=<MAC>` | After flash. |
| 10 | Delete toy `D:\SLH_ECOSYSTEM\device-registry\main.py` | Optional cleanup. Doc already redirects to Railway endpoints. |

---

## Verification criteria & current status

| P | What to verify | Status |
|---|----------------|--------|
| 1 | `curl -H "Authorization: Bearer <token>" slh-api.../api/esp/heartbeat` returns 200 and writes to `device_heartbeats` | Awaits Railway redeploy |
| 2 | `/gr_check 224223270` in Guardian bot chat returns valid JSON | Awaits Guardian container rebuild + `SLH_ADMIN_KEY` env |
| 3 | Flagged user (ZUZ≥100) calling `/api/wallet/send` gets `403 {error:"zuz_blocked"}` | Awaits Railway redeploy |
| 4 | TON auto-verify → `payment.cleared` event → DM from Ledger-bot within 5s | Awaits ledger-bot restart + `LEDGER_WORKERS_CHAT_ID` |
| 5 | Device boots with v3 firmware, shows QR, pairs via website, switches to wallet screen | Awaits physical flash |
| 6 | `chain-status.html` renders all 5 node cards with non-zero data | Live on github.io after push |

---

## Architecture after this change

The chain is now closed at the code level:

```
ESP device ──► /api/esp/heartbeat ──► devices + device_heartbeats ──► event_log ──┐
     ▲                                                                             │
     │ QR + /api/device/claim                                                      │
     │                                                                             ▼
Web (device-pair.html) ──► /api/device/{register,verify} ──► event_log ────► ledger-bot
                                                                                    │
User ──► TG bot (wallet/staking/academia)                                           ▼
     ──► /api/wallet/send ──── guardian_gate ─────┐                          Workers group
     ──► /api/staking/stake ── guardian_gate ─────┤                              + DMs
     ──► academy payment ──────────────────┐      │
                                           ▼      ▼
                                    guardian_blacklist ◄──── Guardian bot (/gr_report)
                                                                (HTTPS via slh_api_client)
```

Single source of truth: **Railway PostgreSQL** (`slh_main` DB).
Single gate for money: **guardian_gate** (cached, fail-open on DB errors).
Single fanout channel: **event_log** (polled every 3s by ledger-bot).

---

## Files changed summary

### `osifeu-prog/slh-api` (to push to master)
- `main.py` — edits around lines 2696, 3841, 3936, 10327, 10380. +claim/heartbeat/commands.
- `api/main.py` — mirror (cp sync).
- `routes/academia_ugc.py` — mark-paid endpoint + model.
- `api/routes/academia_ugc.py` — mirror.
- `shared/events.py` (new)
- `shared/guardian_gate.py` (new)
- `shared/ledger_listener.py` (new)
- `shared/bot_template.py` — conditional listener task
- `device-registry/esp32-cyd-work/firmware/slh-device-v3/` — full new project
- `ops/UNIFIED_CHAIN_DESIGN_20260420.md` (design, written earlier this session)
- `ops/UNIFIED_CHAIN_LAUNCH_20260420.md` (this file)

### `osifeu-prog/osifeu-prog.github.io` (to push to main)
- `website/device-pair.html` (new)
- `website/chain-status.html` (new)

### `osifeu-prog/slh-guardian` (to push to main)
- `bot/slh_api_client.py` (new)
- `bot/commands/guardian_ops.py` (new)
- `bot/main.py` — registers handlers

---

## Rollback plan

If anything misbehaves after Railway redeploy:
- Revert `slh-api` to commit before the merge — Guardian gates + ESP endpoints disappear, existing behavior restored. No data loss (we only added tables, never touched existing schema).
- `devices_heartbeats`, `device_commands`, `event_log` are additive tables — safe to leave in DB.
- `guardian_blacklist` and `academy_earnings` untouched structurally (only `payout_note` added via `ADD COLUMN IF NOT EXISTS`).
- Firmware: hold BOOT for 3s on device → factory reset → reflash v2 .ino from `D:\AISITE\esp32-heartbeat\`.

---

**Signed:** Claude, SLH Infrastructure Agent, 2026-04-20 evening session.
