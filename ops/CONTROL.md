# SLH Spark · CONTROL
**Your single source of truth. Open this daily. Everything else links from here.**

🔗 Web-viewable: https://slh-nft.com/ops-viewer.html?file=CONTROL.md
📅 Last updated: 2026-04-25

---

## 🎯 STATE RIGHT NOW

| | |
|---|---|
| **Revenue (₪)** | **0** — no paying customer yet |
| **API** | 🟢 live · https://slh-api-production.up.railway.app/api/health |
| **Website** | 🟢 live · https://slh-nft.com (127 pages) |
| **Bots (25)** | 🟢 running · ledger-bot rebuilt + fixed |
| **CRM (Ambassador)** | 🟢 live · `POST /api/ambassador/contacts` works end-to-end |
| **Tzvika → founder** | 🟢 deployed |
| **Data integrity** | 🟢 clean · 1 HIGH remaining (legit library default) |

---

## 👉 TODAY — 3 actions only you can do

1. **Railway dashboard health check** — one browser visit to https://railway.app/project/slh-api → Deployments. Confirm latest commit deployed. ⏱ 30s
2. **Global git config** (still `Your Name <your.email@example.com>`) — PowerShell: `git config --global user.name "Osif Kaufman Ungar" ; git config --global user.email "osif.erez.ungar@gmail.com"`. ⏱ 10s
3. **Yaara reply** — if she replied to the WhatsApp you sent, open `ops/CUSTOMER_ONE_PLAYBOOK.md` and follow Stage 1-5. If no reply yet, skip.

## 🕰 PENDING OTHERS (not your move)

- Yaara's reply to WhatsApp (sent 2026-04-24)
- Eliezer's Excel of 130 investors (CRM ready to import)
- Yahav `/start @SLH_AIR_bot` (bot DM bounced 2026-04-22)
- ESP32 firmware flash (physical, requires USB)

---

## 📜 LAST 48 HOURS — what happened

| When | Who | What |
|---|---|---|
| 2026-04-25 | Funnel+Control session (me) | Registered in alignment doc (late). Deleted 3 unused pages. Built this CONTROL.md. |
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
| Customer replied — what next? | `ops/CUSTOMER_ONE_PLAYBOOK.md` |
| Customer didn't reply, it's been 24h | `ops/FOLLOWUP_TEMPLATES.md` |
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
| Waitlist signups | (unknown — reality dump doesn't break out) | — |
| Tokens (types live) | 5 (SLH, MNH, ZVK, REP, ZUZ) + AIC | — |
| Users registered | 21 | /api/ops/reality |
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
