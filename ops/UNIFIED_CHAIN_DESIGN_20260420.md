# 🔗 SLH Unified Chain Design — ESP ↔ TG ↔ Guardian ↔ Ledger ↔ API

> **Date:** 2026-04-20
> **Author:** Claude (diagnosis session with Osif)
> **Goal:** Close the loop between devices, Telegram bots, Guardian, Ledger, staking, and the Railway API — with zero data loss and full audit trail.
> **Status:** PROPOSAL — awaiting Osif approval before implementation.

---

## 1. Executive Summary

The SLH ecosystem already has **every building block** live:

| Subsystem | Status | Location |
|-----------|--------|----------|
| Railway FastAPI (`slh-api`) | ✅ live, 113+ endpoints, synced `main.py`↔`api/main.py` | `osifeu-prog/slh-api` master |
| Device endpoints (`/api/device/*`) | ✅ live, PostgreSQL-backed (`users_by_phone`, `devices`, `device_verify_codes`) | `main.py:10210+` |
| Guardian endpoints (`/api/guardian/*`) | ✅ live, 5 public + 3 admin | `main.py:5912–6144` |
| Wallet/Ledger endpoints (`/api/wallet/*`, `/api/tokenomics/*`) | ✅ live, 6 wallet + tokenomics | `main.py:3777–5113` |
| Staking endpoints (`/api/staking/*`) | ✅ live | `main.py:2683+` |
| Admin key rotation | ✅ live 20.4 | `routes/admin_rotate.py` |
| Ledger bot (`@SLH_Ledger_bot`) | ✅ running in docker-compose | `shared/bot_template.py` |
| Factory/Staking bot (`@Osifs_Factory_bot`) | ✅ running, isolated `slh_factory` DB | `factory/app/` |
| Wallet bot (`@SLH_Wallet_bot`) | ✅ reads BSC on-chain via aiohttp | `wallet/app/blockchain_service.py` |
| Academia bot + 6 payment methods | ✅ live 20.4 | `academia-bot/bot.py` |
| Guardian bot | ✅ container builds | `D:\telegram-guardian-DOCKER-COMPOSE-ENTERPRISE\` |
| ESP active firmware | ✅ posting heartbeats | `D:\AISITE\esp32-heartbeat\esp32-heartbeat.ino` |
| ESP PlatformIO firmware | 🟡 code present, not uploaded to device | `D:\SLH_ECOSYSTEM\device-registry\esp32-cyd-work\firmware\` |
| CYD+Ledger demo firmware | 🟡 archived only | `D:\ARCHIVE_SLH_OLD\SLH_PROJECT_V2_20260416\ESP\CYD_LEDGER_DEMO\` |

**Bottom line:** the problem is **not missing code**. It's that the pieces don't **talk to each other** end-to-end.

---

## 2. Gap Analysis — The 7 Disconnects

### Gap A — Guardian bot is an island
- **Evidence:** `grep -r "slh-api\|slh_api\|api/guardian\|api/wallet\|api/ledger" /d/telegram-guardian-DOCKER-COMPOSE-ENTERPRISE/bot/` → **zero matches**
- **Impact:** Fraud reports filed inside the Guardian bot stay in `guardian_local.db` / `slh_guardian` PG. They never touch `/api/guardian/report` on Railway, so other bots that consult `/api/guardian/check/{user_id}` see an empty blacklist.
- **Fix:** Add an outbound client module `guardian_api_client.py` in the Guardian bot that mirrors every local report to `POST /api/guardian/report` with `X-Admin-Key` header.

### Gap B — ESP firmware is localhost-only
- **Evidence:** `D:\AISITE\esp32-heartbeat\esp32-heartbeat.ino:6` — `const char* serverUrl = "http://10.0.0.7:5002/api/esp/heartbeat";`
- **Impact:** Device only works when `D:\AISITE\esp_bridge.py` runs on 10.0.0.7. No production deployment, no per-user binding, no signing token, no TG notification on events.
- **Fix:** New firmware `slh-device-v3`:
  1. First boot → WiFiManager portal → user scans QR with `https://slh-nft.com/device-pair.html?device_id=<MAC>`
  2. Page posts to `/api/device/register` with phone → code → `/api/device/verify`
  3. `signing_token` returned to the device (via Bluetooth LE or web-serial on first pair; subsequent heartbeats carry it)
  4. Heartbeats go directly to `https://slh-api-production.up.railway.app/api/esp/heartbeat` (new endpoint) with `Authorization: Bearer <signing_token>`
  5. Local `esp_bridge.py` keeps working as a **dev/offline cache**, not the sole path

### Gap C — No bridge between local esp_bridge and Railway
- **Evidence:** `D:\AISITE\esp_bridge.py` writes `secure\esp_status.json` but never POSTs to Railway.
- **Fix:** Add forwarder thread in `esp_bridge.py` — every received heartbeat is also sent to Railway's `/api/esp/heartbeat` with the device's signing token. Gracefully degrade to local-only if offline.

### Gap D — Local device-registry is a toy stub
- **Evidence:** `D:\SLH_ECOSYSTEM\device-registry\main.py` — in-memory `devices = {}` and `codes = {}`, 60 lines, prints code to stdout instead of sending.
- **Impact:** ESP_QUICKSTART directs contributors to hit port 8090, but that path has no DB, no persistence, no Twilio.
- **Fix:** Either (a) delete the micro-service and update docs to point at Railway's `/api/device/register`, or (b) turn it into a thin proxy to Railway. **Recommended: delete + redirect.**

### Gap E — Other bots don't consult Guardian before processing
- **Evidence:** None of wallet/academia/factory bots call `/api/guardian/check/{user_id}` before honoring a payment or stake.
- **Impact:** A user flagged with ZUZ ≥ 100 can still buy, stake, or withdraw.
- **Fix:** Add a `shared/guardian_gate.py` decorator used by `@require_clean_zuz` on all financial handlers. Default behavior: reject with a Hebrew explanation + mention `@osifeu_prog` for appeal.

### Gap F — Ledger-bot is passive — no outbound notifications
- **Evidence:** Ledger-bot responds to `/mybalance` etc. but doesn't react to `/api/payment/*/auto-verify` events.
- **Impact:** Osif doesn't get a TG ping when payments clear. Audit trail exists in DB but is silent.
- **Fix:** Add `/api/webhooks/ledger` endpoint + a `ledger_event_fanout` helper in `main.py`. Ledger-bot subscribes via Redis stream `slh:payments` and posts to Workers group.

### Gap G — ESP cannot display wallet balance on-device
- **Evidence:** `CYD_LEDGER_DEMO.ino` (archived) has the display logic. Active `esp32-heartbeat.ino` does **not**.
- **Impact:** The "kosher wallet" vision — device shows SLH/MNH/ZVK balance without needing phone — is not live.
- **Fix:** Restore CYD_LEDGER_DEMO logic into `slh-device-v3`, add `GET /api/wallet/{user_id}/balances` call every 60s using signing_token. Display top 3 token balances + last TX.

---

## 3. Proposed Unified Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         RAILWAY (slh-api)                           │
│                                                                     │
│  ┌─ Public surface ─────────────────────────────────────────────┐   │
│  │  /api/device/*   /api/esp/*    /api/guardian/*               │   │
│  │  /api/wallet/*   /api/staking/* /api/tokenomics/*            │   │
│  │  /api/payment/*  /api/academy/* /api/admin/*                 │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                            │                                        │
│  ┌─ Shared tables (slh_main PG) ────────────────────────────────┐   │
│  │  users_by_phone · devices · device_verify_codes              │   │
│  │  token_balances · token_transfers · staking_positions        │   │
│  │  guardian_reports · guardian_blacklist · admin_secrets       │   │
│  │  academy_licenses · wallet_idempotency                       │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  ┌─ Event bus (new — Redis stream slh:events) ────────────────┐     │
│  │  device.registered · payment.cleared · guardian.alert      │     │
│  │  stake.opened · stake.unlocked · zuz.spike                 │     │
│  └────────────────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────────────┘
           ▲              ▲                ▲               ▲
           │ HTTPS        │ HTTPS          │ HTTPS         │ Redis sub
           │              │                │               │
    ┌──────┴─────┐  ┌─────┴──────┐  ┌──────┴──────┐  ┌─────┴──────┐
    │ ESP32-CYD  │  │  Browser   │  │  TG Bots    │  │  Workers   │
    │  (kosher   │  │  website   │  │  (25 via    │  │   group    │
    │  wallet)   │  │ slh-nft.com│  │  compose)   │  │  feed      │
    └──────┬─────┘  └────────────┘  └──────┬──────┘  └────────────┘
           │                                │
           │ Local-cache fallback            │ pre-action gate
           ▼                                 ▼
    ┌─────────────┐                  ┌────────────────┐
    │ esp_bridge  │                  │ guardian_gate  │
    │  (AISITE    │                  │  (shared lib)  │
    │  port 5002) │                  │                │
    └─────────────┘                  └────────────────┘
```

**Three promises of this design:**
1. **Single source of truth** = Railway PostgreSQL. Local DBs become caches, not authorities.
2. **Every action flows through Guardian gate** before touching balances.
3. **One event bus** (Redis stream on the same Railway Redis) fans out to bots + workers group + on-chain watchers.

---

## 4. Implementation Plan — 6 Phases

Phased so we never break running production. Each phase is independently shippable and testable.

### Phase 1 — Foundation (day 1, ~4h)
- **1.1** Delete `D:\SLH_ECOSYSTEM\device-registry\main.py` toy stub. Update `ESP_QUICKSTART.md` to point only at Railway `/api/device/register`.
- **1.2** Create `D:\SLH_ECOSYSTEM\shared\guardian_gate.py` — single `await check_zuz(user_id)` helper that reads `/api/guardian/check/{user_id}`. Cache 60s in Redis.
- **1.3** Add event-bus module `D:\SLH_ECOSYSTEM\shared\events.py` — thin wrapper around Redis XADD/XREAD for stream `slh:events`.
- **1.4** Write Railway endpoint `POST /api/esp/heartbeat` (auth: `Authorization: Bearer <signing_token>`) — upserts `devices.last_seen`, `devices.last_ip`, logs event `device.heartbeat`.
- **1.5** Smoke test all four with curl + unit tests.

### Phase 2 — Guardian bot → API integration (day 1, ~3h)
- **2.1** Add `D:\telegram-guardian-DOCKER-COMPOSE-ENTERPRISE\bot\slh_api_client.py` — methods `report_fraud()`, `check_user()`, `fetch_blacklist()`, `post_alert()`. Uses `X-Admin-Key`.
- **2.2** On every Guardian local action (report, ban, scan), also call `slh_api_client.report_fraud()`. Idempotency via `external_report_id` column.
- **2.3** Daily cron in Guardian container: pull `/api/guardian/blacklist` → sync to local DB. Local only → Railway (push), Railway only → local (pull).
- **2.4** Add `/api/guardian/alert` POST — Guardian bot calls it when ZUZ spikes → Railway fans to Redis stream → Ledger-bot picks up → posts to Workers group.
- **2.5** Rotate `GUARDIAN_BOT_TOKEN` (currently `8521882513:...` hardcoded in `.env.secrets.local` — also seen in memory) via BotFather + update Railway/.env.

### Phase 3 — Bot-wide Guardian enforcement (day 2, ~4h)
- **3.1** Wrap `/api/wallet/send` + `/api/wallet/deposit` + `/api/staking/stake` + Academia payment callbacks with `guardian_gate.check_zuz(user_id)` call. ZUZ ≥ 100 → 403 with Hebrew message.
- **3.2** Same in wallet-bot, factory-bot, academia-bot Python handlers.
- **3.3** Smoke test: temporarily flag self (user 224223270) with ZUZ 150 → verify all 4 paths reject. Unflag. Verify they clear.

### Phase 4 — Ledger-bot event listener (day 2, ~3h)
- **4.1** Ledger-bot subscribes to Redis stream `slh:events` consumer group `ledger-bot`.
- **4.2** Handlers:
  - `payment.cleared` → DM the user + post anonymized summary to Workers group.
  - `stake.opened` / `stake.unlocked` → post to Workers group + DM.
  - `device.registered` → DM user "מכשיר חדש נקשר. אם לא אתה — /revoke".
- **4.3** Message idempotency: store last 200 event IDs in Redis set, dedupe on restart.

### Phase 5 — ESP firmware v3 + dashboard (day 3–4, ~8h)
- **5.1** Branch off `slh-device-cyd-clean` PlatformIO project → new variant `slh-device-v3`.
- **5.2** Add modules:
  - `auth.cpp` — read/write `signing_token` to NVS Preferences.
  - `heartbeat.cpp` — POST to Railway every 30s, fallback to local bridge if offline.
  - `wallet.cpp` — GET `/api/wallet/{user_id}/balances` every 60s, display top 3.
  - `pair.cpp` — first-boot WiFiManager + QR code on TFT showing `https://slh-nft.com/device-pair.html?mac=<MAC>`.
- **5.3** New website page `website/device-pair.html`:
  - Reads MAC from URL, asks for phone number, calls `/api/device/register`.
  - User pastes the TG/SMS code → `/api/device/verify` → receives `signing_token`.
  - Page displays token as QR → user scans with device (ESP32 camera OR short BLE transfer).
- **5.4** Flash test unit (device at 10.0.0.4) with v3 firmware. Verify:
  - Old behavior preserved (heartbeat to local 10.0.0.7:5002 still works as fallback).
  - New behavior: device heartbeats reach Railway, balance shows on screen.
- **5.5** Restore CYD_LEDGER_DEMO display logic (balance + last TX) from archive into v3.

### Phase 6 — Staking visibility + unified dashboard (day 5, ~4h)
- **6.1** New page `website/chain-status.html` — live view of every link:
  - Device registry count · last heartbeat per device
  - Guardian alerts last 24h · top-3 ZUZ users
  - Ledger volume last 24h · by token
  - Active stakes · total locked per currency
  - Payment methods success rate · last 7 days
  - All from existing admin endpoints — no new backend needed.
- **6.2** Link `chain-status.html` from `admin.html` sidebar + `agent-hub.html`.
- **6.3** Write `ops/UNIFIED_CHAIN_LAUNCH_20260420.md` after verification — what was live before, what changed, verification evidence (curl outputs + screenshots).

---

## 5. Decisions Osif Must Make Before I Start

1. **Rotate GUARDIAN_BOT_TOKEN now or in Phase 2?**
   Current token is in plaintext `.env.secrets.local` and was mentioned earlier. Safest: rotate via BotFather today, send me the new one via secure channel (Telegram), I update `.env` + Railway.

2. **Device-pair.html QR-to-device transfer channel — which?**
   - **Option A:** Display token as big QR code → user physically shows phone to ESP32 camera (requires ESP32 camera module — our CYD has one via extra header).
   - **Option B:** BLE pairing (requires BLE code in firmware, ~150 more lines).
   - **Option C:** User types 32-char token via rotary encoder on device (ugly but zero hardware deps).
   - **Recommended:** Start with Option C (works with current hardware), roadmap to Option A.

3. **Local esp_bridge — keep or retire?**
   - **Keep as offline cache:** Firmware falls back to local when Railway unreachable. Requires `D:\AISITE` to run the forwarder.
   - **Retire:** Firmware goes direct-to-Railway only. Simpler but no offline continuity.
   - **Recommended:** Keep, repurpose `esp_bridge.py` as one-way forwarder to Railway.

4. **Guardian sync direction — push-only or bidirectional?**
   - **Push-only** (local→Railway): Guardian bot keeps writing to its own DB, mirrors to Railway. Railway is the union.
   - **Bidirectional**: Both sides canonical, last-writer-wins with event IDs.
   - **Recommended:** Bidirectional for blacklist (so other bots enforce bans from Guardian). Push-only for message scans (too high volume).

5. **Academia 70/30 split (instructor/platform) — wire now or defer?**
   - Currently "Phase 3" per the Academia doc. If we wire it inside this chain design, it belongs in Phase 3 of this plan (bot-wide enforcement step).
   - **Recommended:** Wire it. Marketplace instructors are paid via `payout_phone` → `/api/wallet/send` 70% to instructor user_id, 30% to treasury user_id. Idempotency via `license_id`.

6. **ESP firmware upload — who flashes the device?**
   - Osif has the device at 10.0.0.4. Flashing requires physical USB.
   - **Recommended:** I prepare the v3 firmware + flash instructions. Osif runs `platformio run -t upload` on his laptop with the CYD connected.

---

## 6. Risks + Mitigations

| Risk | Mitigation |
|------|------------|
| Guardian bidirectional sync causes ban loop (user banned → unbanned → banned) | Add `last_modified_source` column + 60s debounce |
| Firmware v3 bricks the device | Keep old firmware .bin as rollback, flash only after v3 verified on bench unit |
| Event bus adds Redis load | Use existing `redis` service; cap stream length at 10k via MAXLEN |
| ZUZ gate blocks legitimate users (false positive) | Admin bypass header `X-Admin-Override-ZUZ` for manual override, logged to audit |
| Railway env vars drift between local .env and cloud | Add `ops/env-diff` cron that weekly diffs + alerts |
| Data migration breaks live users/payments | Every schema change additive only. No renames, no drops, only `ADD COLUMN ... DEFAULT ...` |

---

## 7. What I'll Touch (Files & Repos)

**`osifeu-prog/slh-api` (Railway) — additive only:**
- `main.py` / `api/main.py` — add `/api/esp/heartbeat`, `/api/guardian/alert`, event bus init
- `shared/guardian_gate.py` — new
- `shared/events.py` — new
- `shared/bot_template.py` — wire guardian_gate before payments
- `routes/admin_rotate.py` — no change
- New SQL migration `910_esp_heartbeats_audit.sql`

**`osifeu-prog/osifeu-prog.github.io` (Pages) — new files only:**
- `website/device-pair.html` — new
- `website/chain-status.html` — new
- `website/admin.html` sidebar — one new `<a>` tag

**`osifeu-prog/slh-guardian` (separate repo at `D:\telegram-guardian-DOCKER-COMPOSE-ENTERPRISE`):**
- `bot/slh_api_client.py` — new
- `bot/main.py` — add mirror-to-API on every local action
- Rotate token

**`D:\AISITE\` (local Mission Control, not a repo):**
- `esp_bridge.py` — add Railway forwarder thread
- `control_panel.html` — link to Railway chain-status.html

**`D:\SLH_ECOSYSTEM\device-registry\`:**
- Delete `main.py` (toy)
- Keep `esp32-cyd-work/firmware/` as the PlatformIO canonical source
- New folder `esp32-cyd-work/firmware/slh-device-v3/`

---

## 8. Verification Criteria (Definition of Done)

Every phase verified with curl + DB query + screenshot before moving to next:

- **P1:** `curl -H "Authorization: Bearer <token>" slh-api.../api/esp/heartbeat` → 200, DB row updated.
- **P2:** Flag a test user via Guardian bot → within 60s, `curl slh-api.../api/guardian/check/<uid>` returns the flag.
- **P3:** Attempt `/api/wallet/send` from a flagged user → 403 with ZUZ reason.
- **P4:** TON auto-verify a test payment → DM arrives in Ledger-bot within 5s.
- **P5:** Device at 10.0.0.4 boots with v3 firmware → its heartbeats show up in Railway DB + the TFT shows current SLH balance.
- **P6:** `chain-status.html` renders all 5 panels with non-zero data.

After P6: commit `ops/UNIFIED_CHAIN_LAUNCH_20260420.md` with the full before/after evidence bundle.

---

## 9. Approval

Please mark each decision (1–6 in §5) with your choice or "recommended" and I'll proceed top-to-bottom. I will NOT touch any production code, DB, or firmware until you approve this plan.

**Signed:** Claude — awaiting Osif's go-ahead
