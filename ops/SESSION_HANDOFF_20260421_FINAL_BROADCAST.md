# SESSION HANDOFF — 21.4.2026 (FINAL)
# SLH Spark — Admin Bot Upgrade + Broadcast System

**Session end:** 2026-04-21 ~21:00
**Commits pending:** admin-bot/main.py + docker-compose.yml
**Lead Agent:** Claude Sonnet 4.6

---

## ✅ COMPLETED THIS SESSION

### 1. Scheduled Airdrop (19:45)
- Script: `broadcast_airdrop.py` — ran via scheduled task
- Result: 24 users, 120 token txns, 20/24 TG sent (4 fake IDs skipped)
- Logged: `broadcast_log` row

### 2. Independence Day Broadcast
- Script: `broadcast_independence_day.py` (new, committed)
- Gift: ZVK+78, REP+78 per user (78 = year 78 of Israel)
- Result: 19/19 ✅ — zero failures
- Logged: `broadcast_log`

### 3. ESP32 Firmware (slh-device-v3)
- Path: `D:\SLH_ECOSYSTEM\ops\firmware\slh-device-v3\`
- Board confirmed: ESP32 DevKit (CH340, COM5)
- ILI9341 driver + backlight (pin 21) + RST (pin 4) confirmed working
- Full firmware written: WiFiManager captive portal + QR pairing + balance display + heartbeat
- **BUILD: ✅ SUCCESS** (34% Flash, 14.6% RAM)
- **UPLOAD: ❌ BLOCKED** — COM5 busy (Serial Monitor open)
- Action needed: close Serial Monitor, run `pio run -t upload --upload-port COM5`

### 4. Admin Bot — Full Upgrade
- File: `admin-bot/main.py` (517 → 390 lines, fully refactored)
- docker-compose.yml: added `RAILWAY_DATABASE_URL` + `AIRDROP_BOT_TOKEN` to admin-bot

#### New Commands Added:
| Command | Description |
|---------|-------------|
| `/broadcast` | FSM: target → gift preset → message → preview → confirm → send + credit |
| `/airdrop`   | FSM: target → gift preset → confirm → credit tokens (no message) |
| `/gift <id> <amount> <TOKEN>` | Single-user instant gift |
| `/users`     | List all web_users with registration status |

#### Gift Presets (Inline Keyboard):
- `daily` — 0.12 SLH + 8 ZVK + 32 MNH + 12 REP + 100 ZUZ
- `independence` — 78 ZVK + 78 REP
- `rep50` — 50 REP
- `none` — no gift

#### Architecture:
- FSM via `aiogram.fsm` (MemoryStorage)
- asyncpg direct connection to Railway DB (`RAILWAY_DATABASE_URL`)
- Confirmation step before any bulk action
- Full audit log to `broadcast_log` table
- Sends via `AIRDROP_BOT_TOKEN` (separate bot, rate-safe)

---

## ⚠️ OPEN TASKS FOR NEXT SESSION

### BLOCKERS (requires Osif action)
| # | Task | Action |
|---|------|--------|
| B1 | Upload ESP32 firmware | Close Serial Monitor → `pio run -t upload --upload-port COM5` |
| B2 | Docker rebuild admin-bot | `docker-compose build admin-bot && docker-compose up -d admin-bot` |
| B3 | Railway env var: `RAILWAY_DATABASE_URL` | Add to Railway dashboard (admin-bot service) |

### CODE-READY (agent can execute)
| # | Task | File | Priority |
|---|------|------|----------|
| C1 | Fix `/api/admin/link-phone-tg` bug (returns 500) | `main.py:10770` — `_require_admin()` returns int not tuple | High |
| C2 | Wallet page: show on-chain BSC balances | `website/wallet.html` — endpoints ready, 0 blockchain calls wired | High |
| C3 | `broadcast_log` — add `broadcast_id` + `broadcast_deliveries` per-user tracking | `main.py` + `broadcast_airdrop.py` | Medium |
| C4 | i18n on 27 remaining pages | `website/js/translations.js` already has 5 langs | Medium |
| C5 | device-pair.html — build the QR scan pairing page | `website/device-pair.html` (doesn't exist yet) | High |
| C6 | Admin bot: add `/broadcastlog` command to show last 10 sends | `admin-bot/main.py` | Low |
| C7 | Fix `active_today \|\| 47` fake data in HTML | Grep: `47` in website HTML files | High |

---

## 🔧 STRUCTURED TASK LIST (Lead Agent Format)

---

**TASK:** Fix link-phone-tg 500 error
**CURRENT ISSUE:** `POST /api/admin/link-phone-tg` returns 500. Root: `main.py:10770` calls `_require_admin()` expecting tuple `(admin_id, role)` but function returns `int` only.
**EXPECTED BEHAVIOR:** Returns 200 with `{ok: true, user_id, phone, telegram_id}` after linking.
**LOCATION:** `main.py:10770` — `admin_id, _role = _require_admin()`
**DATA SOURCE:** `web_users` table (phone + telegram_id columns)
**PRIORITY:** High

---

**TASK:** Wire on-chain BSC balances to wallet.html
**CURRENT ISSUE:** `website/wallet.html` shows internal token balances only. BSC on-chain SLH balance (0xACb0A09414CEA1c879c67bB7A877E4e19480f022) never fetched.
**EXPECTED BEHAVIOR:** Show real on-chain balance via BSCScan API or web3 call. Endpoint `GET /api/wallet/{user_id}/balances` returns `on_chain_slh` field — wire it to the UI.
**LOCATION:** `website/wallet.html` — balance display section
**DATA SOURCE:** `GET /api/wallet/{user_id}/balances` → `on_chain_slh`
**PRIORITY:** High

---

**TASK:** Build device-pair.html pairing page
**CURRENT ISSUE:** Page doesn't exist. ESP32 firmware (slh-device-v3) shows QR pointing to `https://slh-nft.com/device-pair.html?mac=<MAC>&device_id=<device_id>` but page 404s.
**EXPECTED BEHAVIOR:** Page loads → user enters phone → receives Telegram OTP → enters code → device paired. Calls: `POST /api/device/register` then `POST /api/device/verify`.
**LOCATION:** `website/device-pair.html` (create new)
**DATA SOURCE:** `POST /api/device/register`, `POST /api/device/verify` → returns `{signing_token, user_id}`
**PRIORITY:** High

---

**TASK:** Fix fake active_today data in HTML
**CURRENT ISSUE:** HTML contains hardcoded `<span>47</span>` or `active_today || 47` fallback — shows fake data when real value is 0.
**EXPECTED BEHAVIOR:** Show `--` or `0` when no data. No fake fallback numbers.
**LOCATION:** Grep `47` and `active_today` in `website/` HTML files
**DATA SOURCE:** `GET /api/performance` or `GET /api/health`
**PRIORITY:** High

---

**TASK:** Add broadcast_deliveries per-user tracking
**CURRENT ISSUE:** `broadcast_log` logs totals only. No per-user delivery record (who got it, who failed).
**EXPECTED BEHAVIOR:** Each send writes a row to `broadcast_deliveries(broadcast_id, user_id, status, error, delivered_at)`. Table exists, 186 rows but nothing linking to recent broadcasts.
**LOCATION:** `broadcast_airdrop.py` + `broadcast_independence_day.py` + `admin-bot/main.py`
**DATA SOURCE:** `broadcast_log.id` → FK in `broadcast_deliveries.broadcast_id`
**PRIORITY:** Medium

---

## 📁 FILES CHANGED THIS SESSION

```
admin-bot/main.py                          UPGRADED (full rewrite with FSM)
docker-compose.yml                         UPDATED (RAILWAY_DATABASE_URL + AIRDROP_BOT_TOKEN)
broadcast_independence_day.py              NEW
ops/firmware/slh-device-v3/src/main.cpp   UPGRADED (full firmware)
ops/firmware/slh-device-v3/platformio.ini UPDATED (WiFiManager git + TFT_RST=4)
```

## 🚀 GIT PUSH COMMANDS

```bash
# API repo (root)
cd D:\SLH_ECOSYSTEM
git add admin-bot/main.py docker-compose.yml broadcast_independence_day.py
git add ops/firmware/slh-device-v3/src/main.cpp ops/firmware/slh-device-v3/platformio.ini
git commit -m "feat: admin-bot FSM broadcast+airdrop+gift, ESP32 full firmware, independence day broadcast"
git push origin master

# Website repo (if device-pair.html built this session)
cd D:\SLH_ECOSYSTEM\website
git add device-pair.html
git commit -m "feat: device-pair.html QR pairing page for ESP32"
git push origin main
```

---

## 🤖 MANAGER AGENT PROMPT (copy-paste ready)

```
You are the Lead Agent for SLH Spark — an Israeli crypto investment ecosystem.
Repo: github.com/osifeu-prog/slh-api (master) + github.com/osifeu-prog/osifeu-prog.github.io (main)
API: https://slh-api-production.up.railway.app
DB: Railway Postgres (asyncpg, RAILWAY_DATABASE_URL in .env)

CONTEXT:
- 24 users in web_users (19 real, 4 fake test IDs)
- 113 API endpoints in main.py (~10,800 lines)
- 43 HTML pages on GitHub Pages
- 25 Telegram bots via Docker Compose

SESSION WORK DONE (21.4.2026):
1. admin-bot upgraded: FSM /broadcast + /airdrop + /gift + /users (admin-bot/main.py)
2. ESP32 firmware written: WiFiManager + QR pairing + balance display (ops/firmware/slh-device-v3/)
3. Independence Day broadcast sent: 78 ZVK + 78 REP to 19 users ✅
4. Daily airdrop ran: 24 users, 120 txns ✅

NEXT TASKS (priority order):
1. [HIGH] Fix main.py:10770 — _require_admin() returns int not tuple → 500 on /api/admin/link-phone-tg
2. [HIGH] Build website/device-pair.html — ESP32 pairing page (calls /api/device/register + /api/device/verify)
3. [HIGH] Wire on-chain BSC balance in website/wallet.html
4. [HIGH] Grep "47" + "active_today" in website/ — remove fake fallback data
5. [MEDIUM] Add broadcast_deliveries per-user rows in broadcast_airdrop.py + admin-bot

RULES:
- Never fake data — use `--` when empty
- Never hardcode passwords in HTML
- Hebrew UI, English code/commits
- Always sync api/main.py → main.py (root) before push
- Railway builds from ROOT main.py only

START: Read ops/SESSION_HANDOFF_20260421_FINAL_BROADCAST.md then check API health.
```

---

## 📊 SYSTEM STATUS (end of session)

| Component | Status |
|-----------|--------|
| Railway API | ✅ Live |
| Website (43 pages) | ✅ Live |
| admin-bot (upgraded) | ⚠️ Needs docker rebuild |
| ESP32 firmware | ⚠️ Needs upload (COM5 busy) |
| Daily airdrop (scheduled) | ✅ Running 19:45 |
| DB (Railway Postgres) | ✅ Healthy |
| Independence Day broadcast | ✅ Sent 19/19 |
