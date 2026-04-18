# SLH · Session Handoff · 17 April 2026

> Closed state of a long multi-agent session. Use this as the starting prompt for the next Claude/agent picking up.

---

## 🟢 What shipped this session (commits live)

### API (Railway, commit `4c9d8a8`)
| File | Purpose |
|------|---------|
| `routes/payments_auto.py` | +0.00002 BNB tolerance (Binance withdrawal fee) |
| `routes/payments_monitor.py` | **NEW** — BSC Genesis poller, auto-match incoming TX → grant premium + issue receipt |
| `main.py` / `api/main.py` | Wire monitor into startup (set_pool + start_monitor) |
| 2 new tables | `pending_payment_intents`, `unmatched_deposits` (auto-created on first startup) |
| New endpoints | `GET /api/payment/monitor/status`, `POST /api/payment/monitor/intent` |

### Website (GitHub Pages, already live)
| File | Purpose |
|------|---------|
| `tour.html` | 8-station onboarding with progress bar + localStorage |
| `agent-tracker.html` | Live dashboard of 6 agents (status, blockers, deliverables) |
| `blog/neurology-meets-meditation.html` | Post #1 (from Content Writer agent) |
| `blog/crypto-yoga-attention.html` | Post #2 |
| `blog/verified-experts-not-influencers.html` | Post #3 |
| `blog/slh-ecosystem-map.html` | Post #4 |
| `blog/anti-facebook-manifesto.html` | Post #5 |
| `css/slh-design-system.css` | Tokens · 5 themes · components · nav · a11y (sr-only-focusable, prefers-reduced-motion) |
| `js/slh-nav.js` | Unified nav · role-based · theme/lang dropdowns · RTL · mobile hamburger |
| `js/slh-skeleton.js` | Skeleton loaders · `SLHSkeleton.show/hide/withSkeleton/fetchJson` + `data-skeleton` auto |
| `pay.html` | QR switched to **EIP-681** (`ethereum:0xd06...@56?value=<wei>`) — auto-BSC + amount pre-fill |
| `pay.html` (TON) | QR switched to `ton://transfer/...?amount=` deeplink |
| `scripts/e2e-smoke-test.ps1` | Tracks 1-6 smoke test with pass/fail counts |

---

## 🟡 Blocked — waiting on Osif

### 1. Osif's pending test TX — 0.000490 BNB
- **TX hash:** `0x2a9d5da99172b7e6c758ea07457d419be891df68b539b9966f092ec0f17a262a`
- **On-chain:** confirmed via BSC RPC ✅ (from Binance hot wallet → Genesis)
- **Previous status:** rejected (wanted ≥ 0.0005, got 0.000490 after Binance fee)
- **After this deploy (~90s):** retry `/api/payment/bsc/auto-verify` with the same hash — should pass with new tolerance.
- **Alternative:** wait 30s for payment-monitor to auto-match (requires pending_payment_intent row; see Next Steps).

### 2. Agent #3 · Social Automation (S.1 n8n setup)
Two requirements:
```
N8N_PASSWORD=<...>
מאשר docker compose
```
Once both received:
```powershell
cd D:\SLH_ECOSYSTEM
docker compose config
docker compose up -d n8n
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
start http://localhost:5678
```

### 3. Agent #4 · ESP Firmware (CYD black screen)
- Build succeeds on `C:\Users\USER\Desktop\SLH\ESP32-2432S028` (not `D:\SLH_ECOSYSTEM\esp-firmware`).
- Screen stayed black — files/config went to D: but `pio run` ran in C:.
- Delivered fix: overwrite src/ + platformio.ini in **C:\ folder** with `colorTest()` (RED→GREEN→BLUE) + dual backlight pins (GPIO 21 **and** 27).
- **Waiting for:** Osif to run the block + report what the screen shows after reboot.
- If colors cycle → pins OK → WiFiManager AP next; if black → swap MOSI/MISO or try `-DTFT_BL=27`.

### 4. Agent #6 · @G4meb0t_bot
- Skeleton ready (aiogram 3.x).
- **Waiting for:** Telegram BotFather token.

---

## 🔵 Agent Status Map (live at `/agent-tracker.html`)

| # | Agent | Status | Next task |
|---|-------|--------|-----------|
| 1 | Content Writer | ⏸ ממתין לאישור | W.2 (30 social posts), W.3 (emails) |
| 2 | UI/UX Designer | 🟢 פעיל | U.3 typography audit (after U.5) |
| 3 | Social Automation | 🔴 חסום | S.1 n8n install (waiting on N8N_PASSWORD) |
| 4 | ESP Firmware | 🔴 חסום | E.2 device register (waiting on screen test) |
| 5 | Master Executor | 🟢 פעיל שוטף | E2E test suite run, final 100% report |
| 6 | @G4meb0t | ⏸ ממתין ל-token | Deploy + sudoku mini-app |

---

## 🔧 Test & verify

**Quick health (should be 200 OK):**
```bash
curl -s https://slh-api-production.up.railway.app/api/health
# → {"status":"ok","db":"connected","version":"1.0.0"}
```

**Monitor status (after deploy):**
```bash
curl -s https://slh-api-production.up.railway.app/api/payment/monitor/status
# Expect: running:true, genesis:0xd061..., last_run_iso:<recent>
```

**Full E2E smoke:**
```powershell
cd D:\SLH_ECOSYSTEM
.\scripts\e2e-smoke-test.ps1 -AdminKey "slh2026admin"
```

**Osif's TX retry (after ~90s deploy wait):**
```bash
curl -sX POST https://slh-api-production.up.railway.app/api/payment/bsc/auto-verify \
  -H "Content-Type: application/json" \
  -d '{"user_id":224223270,"tx_hash":"0x2a9d5da99172b7e6c758ea07457d419be891df68b539b9966f092ec0f17a262a","expected_min_bnb":0.0005,"plan_key":"test_min"}'
```

---

## 📍 Key URLs

| Purpose | URL |
|---------|-----|
| Live API | https://slh-api-production.up.railway.app |
| Live website | https://slh-nft.com |
| Agent Tracker | https://slh-nft.com/agent-tracker.html |
| Tour | https://slh-nft.com/tour.html |
| Payment | https://slh-nft.com/pay.html |
| Mission Control | https://slh-nft.com/mission-control.html |
| Prompts index | https://slh-nft.com/prompts/ |
| Genesis wallet (BSC) | `0xd061de73B06d5E91bfA46b35EfB7B08b16903da4` |
| Public BSC RPC | `https://bsc-dataseed.binance.org` |

---

## 🛠 Next Claude — do these first

1. **Verify Osif's TX is accepted** (once Railway deploy lands):
   ```bash
   curl -sX POST .../bsc/auto-verify -d '{...osif tx above...}'
   ```
   If `"verified":true` — send Osif a short confirmation + Telegram receipt link.

2. **Register a frontend pending intent** when user clicks a product on `/pay.html` (before sending). Add a fetch to `POST /api/payment/monitor/intent` with `{user_id, chain:'bsc', expected_amount, plan_key}`. This lets the monitor auto-match without any TX hash paste.

3. **Close the 3 blog post placeholders** in `/blog.html` index (post #1–5 now real HTML files).

4. **Ask Osif for:** N8N_PASSWORD · BotFather token for @G4meb0t_bot_bot · CYD screen test result.

5. **Don't touch** without explicit approval: `docker-compose.yml` (n8n service), Railway env vars, `.env` file, pay.html Genesis address.

---

## ⚠️ Rules re-stated (CLAUDE.md)

- Railway builds from ROOT `main.py` — always sync `api/main.py` → `main.py` after any API edit.
- Hebrew UI, English code/commits.
- Website is a separate git repo at `D:\SLH_ECOSYSTEM\website`.
- Dating group `t.me/+nKgRnWEkHSIxYWM0` is **PRIVATE** (never link publicly, never share with minor nephew ID `6466974138`).
- Public broadcast channel: `t.me/slhniffty`.
- Admin key in Railway env `ADMIN_API_KEYS` (default `slh2026admin`).
- Tolerance for BSC payments: `0.00002 BNB` (absolute, not percentage).

---

## 📝 Archive-ready prompt (copy this to start a fresh session)

```
You're picking up the SLH Spark ecosystem mid-build. Read:
- D:\SLH_ECOSYSTEM\ops\SESSION_HANDOFF_2026-04-17.md  (this file)
- D:\SLH_ECOSYSTEM\CLAUDE.md  (house rules)

Immediate priorities:
1. Verify Osif's TX 0x2a9d5da9...a262a via /api/payment/bsc/auto-verify (should pass after deploy).
2. Wire /pay.html to register pending_payment_intents on product click (~30 lines JS).
3. Poll Osif for the 3 blocker inputs (N8N_PASSWORD, BotFather token, CYD screen result).

House rules (abbreviated):
- Hebrew UI, English code.
- Railway builds from root main.py; api/main.py is a mirror — sync both.
- Never commit .env.
- Dating group is private; broadcast channel is t.me/slhniffty.
- Agent tracker at /agent-tracker.html is source of truth for who's working on what.

When in doubt, ask Osif in Hebrew, one short question at a time.
```

---

*End of handoff · 17 Apr 2026 · evening · API commit `4c9d8a8`*
