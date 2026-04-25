# SLH Spark · CONTROL
**Your single source of truth. Open this daily. Everything else links from here.**

🔗 Web-viewable: https://slh-nft.com/ops-viewer.html?file=CONTROL.md
📅 Last updated: 2026-04-25

---

## 🎯 STATE RIGHT NOW (verified 2026-04-25)

| | |
|---|---|
| **Revenue (₪)** | **0** — no paying customer yet |
| **API** | 🟢 live · v1.1.0 · db connected |
| **Website** | 🟢 live · https://slh-nft.com (127 pages, GitHub Pages) |
| **Bots (25)** | 🟢 running · ledger-bot rebuilt + fixed |
| **CRM (Ambassador)** | 🟢 live · 5 endpoints + 2 test records |
| **Tzvika → founder** | 🟢 deployed (`b48a1b1`) |
| **Data integrity** | 🟢 clean · 1 HIGH remaining (legit library default) |
| **event_log** | 🟢 **active · 17 events captured** (device.registered, device.heartbeat) |
| **ESP32 fleet** | 🟢 **6 devices registered · `esp32-14335C6C32C0` heartbeating live since 2026-04-23** |
| **Telegram Gateway** | 🟡 gateway_loaded=true · `primary_bot_token_set=false` (env var pending) |
| **Mini Apps** | 🟡 code live · will 500 until TELEGRAM_BOT_TOKEN env set |
| **Public events feed** | 🟢 endpoint live · 0 visible items (filter mismatch — see Note A) |

---

## 👉 TODAY — 3 actions only you can do

1. **Railway env vars** (THE blocker) — Variables tab on Railway:
   - `TELEGRAM_BOT_TOKEN` = `<from @BotFather for @WEWORK_teamviwer_bot>`
   - `SMS_PROVIDER` = `stub`
   - `DEV_EXPOSE_OTP` = `true`
   - Verify: `curl https://slh-api-production.up.railway.app/api/miniapp/health` → expect `primary_bot_token_set: true`. ⏱ 3 min
2. **BotFather** `/setdomain` for `@WEWORK_teamviwer_bot` → `https://slh-nft.com/miniapp/dashboard.html`. ⏱ 30 s
3. **Global git config** — `git config --global user.name "Osif Kaufman Ungar" ; git config --global user.email "osif.erez.ungar@gmail.com"`. ⏱ 10 s

> Note A: `/api/events/public` returns `{events:[],total:0}` because event_log only has `device.*` events; PUBLIC_EVENT_TYPES filter expects `payment.cleared`, `stake.opened`, `broadcast.send`, etc. First broadcast/payment will populate it.

## 🕰 PENDING OTHERS (not your move)

- Yaara's reply to WhatsApp (sent 2026-04-24)
- Eliezer's Excel of 130 investors (CRM ready to import)
- Yahav `/start @SLH_AIR_bot` (bot DM bounced 2026-04-22)
- ESP32 firmware flash (physical, requires USB)

---

## 📜 LAST 48 HOURS — what happened

| When | Who | What |
|---|---|---|
| 2026-04-25 | Funnel+Control session (me) | Registered in alignment doc (late). Deleted 3 unused pages. Built CONTROL.md + CUSTOMER_PROSPECTUS_DEMO.md. Closed session. |
| 2026-04-25 | External agent | "mass update" `a799300` — 30k line commit, ugly but not broken |
| 2026-04-24 | Voice/Swarm session | Voice POC page + Swarm POC page + network.html expanded to 61 nodes |
| 2026-04-24 | Telegram-first session | SMS provider + Mini Apps + telegram_gateway wired |
| 2026-04-23 → 24 | Funnel+Control session (me) | Creator funnel (`pay-creator-package`, `creator-intake`), pay-test.html, audit script, pre-commit guards, CRM Phase 0 live, Tzvika promoted |

Full session log: `ops/SYSTEM_ALIGNMENT_20260424.md` § Active Agents

---

## 🗺 PROJECT MAP — what each piece is

| Project | What | Status | Doc |
|---|---|---|---|
| **API (Railway)** | FastAPI backend, 113+ endpoints | 🟢 live | `ops/SYSTEM_ARCHITECTURE.md` |
| **Website** | 127 pages on GitHub Pages | 🟢 live | `ops/project-map.html` |
| **Bots (25)** | Telegram bots via Docker | 🟢 running | `docker-compose.yml` |
| **CRM Phase 0** | `routes/ambassador_crm.py` — 5 endpoints | 🟢 live | code inline |
| **Payments** | TON + BNB auto-verify · card not wired | 🟡 partial | `ops/TEST_PAYMENT_GUIDE.md` |
| **ESP32 firmware** | slh-device-v3 · ILI9341 + WiFiManager | 🟡 code ready, flash pending | `ops/firmware/slh-device-v3/` |
| **Voice Vision** | POC page only · NO endpoint yet | 🔵 vision | `ops/VOICE_STACK_COMPETITIVE_20260424.md` |
| **Swarm Vision** | POC page + waitlist · NO endpoint yet | 🔵 vision | `ops/SWARM_V1_BLUEPRINT_20260424.md` |
| **Kosher Wallet** | Waitlist on swarm.html | 🔵 vision | (same) |

---

## 📚 KEY DOCS — when you need deeper detail

| Need to see... | Open... |
|---|---|
| Who's working on what | `ops/SYSTEM_ALIGNMENT_20260424.md` |
| "How do I run the system?" | `ops/OPS_RUNBOOK.md` + `slh-start.ps1` |
| **Customer-facing prospectus (demo)** | `ops/CUSTOMER_PROSPECTUS_DEMO.md` ← fill [DEMO] markers + PDF |
| Customer replied — what next? | `ops/CUSTOMER_ONE_PLAYBOOK.md` |
| Customer didn't reply, it's been 24h | `ops/FOLLOWUP_TEMPLATES.md` |
| Test the payment flow end-to-end | `ops/TEST_PAYMENT_GUIDE.md` + `pay-test.html` |
| All API endpoints | `ops/API_REFERENCE.md` |
| Something broke | `ops/OPS_RUNBOOK.md` → `ops/INCIDENTS.md` |
| What I am thinking long-term | `ops/ROADMAP_Q2_2026.md` (planned) |
| PowerShell commands for admin tasks | `ops/OPERATOR_QUICK_COMMANDS.md` |

---

## 🧭 AGENTS ACTIVE NOW

Register in `ops/SYSTEM_ALIGNMENT_20260424.md` Active Agents Board BEFORE working. No parallel sessions without coordination.

- Claude Opus 4.7 (Main Session · this one) — **paused at end of this turn**
- [Slot Open] — Infrastructure/DevOps
- [Slot Open] — Community/Telegram
- [Slot Open] — QA/Testing

---

## 📊 REAL METRICS (not vanity)

Update when numbers change. Don't pad.

| Metric | Value | Source |
|---|---|---|
| Real paying customers | **0** | reality.users |
| Revenue this month (₪) | **0** | reality.payments |
| Tokens (types live) | 5 (SLH, MNH, ZVK, REP, ZUZ) + AIC | — |
| Users registered | 21 | /api/ops/reality |
| ESP32 devices registered | **6** (1 actively heartbeating) | /api/admin/devices/list |
| event_log entries (total) | **17** | /api/admin/events |
| events in last 24h by type | device.registered=2, device.heartbeat=2 | /api/admin/events |
| DMs sent (last 48h) | 6 (5 delivered · 0 engagement via bot) · 1 WhatsApp personal | broadcast_history |
| On-chain tx processed | Osif's own Genesis deposits (test only) | bscscan |
| Railway deploys (last 48h) | 10+ | git log |

---

## ⚡ RULES THAT KEEP THIS FILE CONCISE

1. **Under 200 lines.** If you hit 200 — move sections to separate docs, link here.
2. **Truth only.** No aspirational lines. If unclear → "(unknown)".
3. **Update, don't append.** Rewrite the section, don't add to it.
4. **Every agent updates this before closing their session.** One screen, your dashboard.

---

## 🔜 NEXT SCHEDULED REVIEW

- **Tomorrow 2026-04-26 morning:** Osif opens this, confirms 3 TODAY actions status.
- **End of week (2026-04-30):** full review — did any of the waiting items happen? If not, escalate or archive.
