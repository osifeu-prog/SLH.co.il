# SLH System Alignment Report — 2026-04-24
**Owner:** Osif Kaufman Ungar (@osifeu_prog, Telegram 224223270)
**Purpose:** קו יישור בין כל הסוכנים הפעילים — מה כל אחד עושה, מה כבר נעשה, מה חוסם, מה לא לעשות.
**Usage:** כל סוכן חדש שנכנס לפרויקט **חייב לקרוא את המסמך הזה**, להוסיף את השם שלו בסעיף "Active Agents" ולעדכן את סעיף "Status" שלו בסוף כל סשן.

**🔗 Paired document:** [`ops/AGENT_COORDINATION_20260424.md`](AGENT_COORDINATION_20260424.md) — shared protocol rules
(written by another agent in parallel). Both are complementary: this doc = **active status board**,
the other = **protocol rules**. Read both.

---

## 🛑 STOP — Read This First

### Core Rules (non-negotiable)
1. **לא מציגים שירותים LIVE שלא קיימים.** אם אין hardware / license / stack — תסמן "Phase 2 Vision" / "POC" / "Planned". אין "Coming soon without date".
2. **לא לוקחים כסף על vaporware.** לא pre-orders, לא checkout, לא deposits — לפני POC עובד.
3. **לא עובדים כפול.** לפני שמתחיל משימה — `grep` ל-ops docs + scan ל-website/*.html לוודא שאין חפיפה.
4. **שומרים על מדיניות Hebrew UI / English code.** UI בעברית, code + commits באנגלית.
5. **לא hardcoding של secrets/passwords** ב-HTML. רק localStorage + API auth.
6. **לא פוגעים ב-main.py בלי סנכרון לי-root.** Railway בונה מ-ROOT main.py, לא מ-api/main.py.
7. **בלוקר מיידי = עדכון כאן.** אם אתה תקוע — כתוב בסעיף "Blockers" למטה.

---

## 📊 System State — Verified 2026-04-24

### LIVE (verified via curl)
| רכיב | URL / מיקום | סטטוס |
|---|---|---|
| Website | `https://slh-nft.com` | ✅ GitHub Pages, 127 HTML pages |
| API | `https://slh-api-production.up.railway.app/api/health` | ✅ v1.1.0, 113+ endpoints |
| SLH Token | BSC `0xACb0A09414CEA1C879c67bB7A877E4e19480f022` | ✅ PancakeSwap V2 pool active |
| Voice Vision | `https://slh-nft.com/voice.html` | ✅ commit ccd8281 (shipped 24.4) |
| Swarm Vision | `https://slh-nft.com/swarm.html` | ✅ commit ccd8281 (shipped 24.4) |
| Neural Network Map | `https://slh-nft.com/network.html` | ✅ 61 nodes (+10 Voice/Swarm) |
| Roadmap | `https://slh-nft.com/roadmap.html` | ✅ 39 items (+5 Voice/Swarm) |

### WIP (code ready, not deployed / not fully wired)
| רכיב | מצב | בעל משימה |
|---|---|---|
| Ambassador CRM | 5 endpoints אבל 404 חי | Infra (Railway redeploy) |
| Mini Apps (`/miniapp/*`) | קיימים מקומית, 404 חי | Infra |
| `marketplace.html` + `team.html` | מקומיים, 404 חי | Infra |
| API repo ops commit `c89f4a3` | מקומי בלבד | Osif (push ידני) |

### Blocked (waiting on external)
| בלוקר | Owner | פעולה נדרשת |
|---|---|---|
| Railway auto-deploy תקוע מ-097eafe | Osif | לחיצת Redeploy ב-dashboard |
| 31 bot tokens דולפים | Osif | BotFather `/revoke` + rotate |
| Guardian repo 404 | Osif | new remote או gh auth fix |

---

## 👥 Active Agents — Claims Board

### Agent: Claude Opus 4.7 (1M context) — Main Session
**Reporting window:** 2026-04-24 (today)
**Current status:** ✅ Session closed
**What I did this session:**
1. ניתוח תחרותי של ימות המשיח → `ops/VOICE_STACK_COMPETITIVE_20260424.md` (280 lines, 9 sections)
2. Blueprint טכני ל-SLH Swarm → `ops/SWARM_V1_BLUEPRINT_20260424.md` (310 lines, ESP32+FastAPI code stubs + DB schema)
3. 2 דפי vision חדשים: `voice.html` (548 lines) + `swarm.html` (640 lines)
4. עדכנתי `network.html` — 10 צמתים חדשים + 14 connections + canvas renderers
5. עדכנתי `roadmap.html` — 5 items חדשים + 2 categories
6. עדכנתי `project-map.html` — 52 דפים
7. עדכנתי `js/shared.js` — site-map FAB section "Phase 2 Vision"
8. Cache-bust bump: `shared.js?v=20260424a` ב-37 דפי HTML
9. Handoff doc → `ops/SESSION_HANDOFF_20260424_VOICE_SWARM.md`
10. Team addendum → `ops/TEAM_HANDOFF_20260424/ADDENDUM_VOICE_SWARM_PHASE2.md`
11. Command Center launcher → `website/command-center.html` (new)
12. Setup PowerShell doc → `ops/COMMAND_CENTER_SETUP_20260424.md`
13. **This alignment report**

**What I did NOT do (deliberate):**
- לא נגעתי ב-`api/main.py` / `main.py` / database migrations — Phase 2 הוא vision בלבד
- לא דחפתי את API repo (`c89f4a3`) — יש שם uncommitted work אחר שלא שלי
- לא יצרתי endpoints `/api/voice/*` או `/api/swarm/*` — Phase 1 POC decision לא התקבלה עדיין

**Git state at session close:**
- `osifeu-prog/osifeu-prog.github.io` (website): pushed to `origin/main` → commit `ccd8281`
- `osifeu-prog/slh-api` (API): local commit `c89f4a3` on `master`, NOT pushed

**My next session trigger:** אוסיף מחליט Phase 1 POC (Voice Twilio trial / Swarm ESP32 order).

---

### Agent: Guardian ESP Preorder Bot (Parallel Session — NOT ME)
**As reported in user message @ 2026-04-24:**
The other agent announced it would build:
- `CREATE TABLE orders` in Railway Postgres
- `POST /api/preorder` + `GET /api/preorder/status/{id}` + `POST /api/admin/orders/confirm`
- Telegram `/preorder` wizard in `@SLH_macro_bot` (different project: `D:\SLH.co.il`)
- `/guardian.html` landing page
- Mission Control "Orders" tab

**⚠️ OVERLAP WARNING (flagged by Claude Opus 4.7):**
- `/swarm.html` already has Kosher Wallet waitlist — building `/guardian.html` = duplicate
- `/kosher-wallet.html` already exists
- `@SLH_macro_bot` ≠ main SLH stack (different project)
- Taking payment before POC = vaporware risk

**REQUESTED ACTION (for that agent):**
**Please pause your current work and re-read this alignment doc.** Coordinate with the flow below:
1. Use **waitlist only** (already implemented in `/swarm.html` + `/voice.html`) — no money flow
2. Do NOT build `/guardian.html` — use existing `/swarm.html` + `/kosher-wallet.html`
3. If you MUST build a bot command — add it to `@SLH_AIR_bot` (D:\SLH_ECOSYSTEM) not `@SLH_macro_bot` (D:\SLH.co.il)
4. Check `ops/SWARM_V1_BLUEPRINT_20260424.md` for the tech spec
5. Update this file in "Active Agents" section with your claim + status

---

### Agent: [Slot Open] — Infrastructure/DevOps Agent
**Claim this slot if you're working on:**
- Railway deploy unblock
- Docker compose restart
- Database migrations
- Bot fleet operations

---

### Agent: [Slot Open] — Community/Telegram Agent
**Claim this slot if you're working on:**
- Broadcasts (broadcast_ids 35+)
- Group moderation
- New bot creation

---

### Agent: [Slot Open] — QA/Testing Agent
**Claim this slot if you're working on:**
- Cross-browser tests
- Mobile layout
- i18n verification
- Endpoint fuzzing

---

## 🗺️ Project Overview (for new agents / human operators)

### Stack
- **Website:** 127 HTML pages on GitHub Pages (`slh-nft.com`)
- **API:** FastAPI on Railway (`slh-api-production.up.railway.app`), 113+ endpoints, ~7000 lines in `main.py`
- **Bots:** 25 Telegram bots via Docker Compose (aiogram 3.x)
- **Blockchain:** SLH token on BSC (BEP-20), PancakeSwap V2 pool
- **Database:** PostgreSQL 15 + Redis 7

### Repos
| Repo | Branch | Deploys To |
|---|---|---|
| `github.com/osifeu-prog/slh-api` | master | Railway |
| `github.com/osifeu-prog/osifeu-prog.github.io` | main | GitHub Pages (slh-nft.com) |

### 5-Token Economy
| Token | Purpose | Status |
|---|---|---|
| SLH | Premium/governance | LIVE on BSC, PancakeSwap pool active |
| MNH | ILS-pegged stablecoin | Internal only |
| ZVK | Activity rewards (~4.4 ILS) | Internal |
| REP | Personal reputation | Internal, 0-1000+ |
| ZUZ | Anti-fraud Mark of Cain | Guardian, auto-ban at 100 |

### Bot Fleet (25 bots in docker-compose.yml)
core-bot, guardian-bot, botshop, wallet, factory, fun, admin, airdrop, campaign, game, ton-mnh, ton, ledger, osif-shop, nifti, chance, nfty, academia-bot, claude-bot (@SLH_Claude_bot — executor), + more.

### Active Users (as of 24.4)
Tzvika, Elazar, Idan, Yaara, Yahav, Orit + Osif = 7 core.

---

## 🚦 Phase Status

### Phase 0 (Q3-Q4 2025) — FOUNDATION ✅
Website launched, SLH token on BSC, 7 initial bots, Docker+Postgres infra, staking system.

### Phase 1 (Q1 2026) — GROWTH ✅ 80%
Community+referral, BSC+TON wallet, AI multi-provider, MNH stablecoin, ZUZ anti-fraud, Neural Network Map, Audit Hash Chain, CEX integration, Genesis 49, Genesis Launch on PancakeSwap. **Missing:** Institutional Admin, Strategy Engine, Sumsub+Fireblocks.

### Phase 2 (Q2 2026 — NOW) — EXPANSION 🟡 30%
In-flight: P2P Marketplace, GemPad round 2, Webhook migration (all 25 bots), Multi-exchange listing, Mobile app, PWA. **New:** Voice POC + Swarm POC (added today, upcoming).

### Phase 3 (Q3-Q4 2026) — SCALE ⏸️ 0%
19 ecosystem tokens, Premium groups, Ambassador SaaS, 20+ specialized bots.

### Phase 4 (2027+) — VISION ⏸️ 0%
Digital banking, AI portfolio manager, Web3 social, Multi-chain DEX, **Voice commercial launch**, **Swarm DePIN economy**, **Kosher Wallet mass production**.

---

## 📬 Communication Protocol (for agents)

### When claiming a task
1. Open this file (`ops/SYSTEM_ALIGNMENT_20260424.md`)
2. Go to your slot in "Active Agents" (or claim an open slot)
3. Write your name + the task you're taking
4. Write expected completion window
5. Commit this file

### During work
- Log blockers immediately to "Blocked" section
- Don't push commits to `master` without checking if other agents are mid-flight
- For API changes: always `cp api/main.py main.py` before committing (Railway builds from ROOT)

### At session close
1. Update your slot with "Status: closed" + deliverables list
2. Move your agent block to archival section if work is fully done
3. Commit this file

---

## 🔐 Critical Secrets (NEVER paste in chat)
Per memory `feedback_never_paste_secrets`, the following must NOT appear in any agent output, code, commit message, or chat:
- `ANTHROPIC_API_KEY`
- Any `*_BOT_TOKEN`
- `DB_PASSWORD` / Postgres connection strings
- BSC private keys / seed phrases
- `slh_admin_password` localStorage values
- Railway env values

If leaked: flag immediately to Osif + list every exposed secret with rotation URLs.

---

## 🧭 Quick Links — For Navigation

**Control Center:** `https://slh-nft.com/command-center.html` *(new, from this session)*
**Neural Network:** `https://slh-nft.com/network.html`
**Roadmap:** `https://slh-nft.com/roadmap.html`
**Project Map:** `https://slh-nft.com/project-map.html`
**Admin:** `https://slh-nft.com/admin.html`
**Mission Control:** `https://slh-nft.com/mission-control.html`
**Ops Dashboard:** `https://slh-nft.com/ops-dashboard.html`
**Bot Tokens:** `https://slh-nft.com/admin-tokens.html`

**Internal docs:**
- `ops/SESSION_HANDOFF_20260424_VOICE_SWARM.md`
- `ops/VOICE_STACK_COMPETITIVE_20260424.md`
- `ops/SWARM_V1_BLUEPRINT_20260424.md`
- `ops/COMMAND_CENTER_SETUP_20260424.md`
- `ops/TEAM_HANDOFF_20260424/` (6 files)

---

**Last updated:** 2026-04-24 @ session close by Claude Opus 4.7 (1M context)
**Next update:** any agent on claim/close.
