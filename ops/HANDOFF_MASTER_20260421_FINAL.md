# SLH SPARK — HANDOFF MASTER (2026-04-21 FINAL)

**מסמך העברת מקל מלא. סוגר את לילה 21.4.**

מבוסס על: זיכרון ארוך טווח (CLAUDE.md + MEMORY.md 39 entries), git logs ב-slh-api + website, endpoint probes על production, mobile audit, scan על דוחות מצורפים.

---

## 1. מצב נוכחי של המערכת (Production)

### API — `slh-api-production.up.railway.app`
- **Version:** 1.1.0
- **Health:** `{"status":"ok","db":"connected"}`
- **Endpoints shipped היום:**
  - `POST /api/admin/link-phone-tg` (commit `ca8f5e3`)
  - `GET /api/admin/events` (commit `192e12e`) — ring buffer + cursor + types filter
  - `POST /api/ops/reality` (commit `f561684`) — single source of truth admin endpoint
  - `GET /api/ops/reality` (via admin broadcast key)
  - 5 endpoints ב-commit `98cb7e4`: `/api/events/public`, `/api/ops/credit`, `/api/ops/approve-payment`, `/api/ops/ban`, `/api/performance`
- **Phase 0 DB Core:** Deployed. `shared_db_core.py` active. `init_db_pool` ב-main.py. Fail-fast 503 על DB down.
- **Phase 0B migration:** 16/16 שירותים (כולל botshop, academia-bot, osif-shop, nfty-bot, admin-bot)

### Website — `slh-nft.com` (GitHub Pages)
- **דפים חיים:** 43+ (ספירה מעודכנת ב-ops-dashboard.html אומרת 79 — לבדוק עדכון)
- **דפים חדשים ב-21.4:**
  - `/chain-status.html` (commit `251195a`) — 6 פאנלים, auto-refresh 15s
  - `/device-pair.html` + `/admin/reality.html` (commit `1d4333a`)
  - `/performance.html` (commit `5a0c078`) — Research Lab + Sharpe/Sortino/MaxDD
- **דפים מעודכנים היום:**
  - `admin.html` — Events tab inline (commit `5c53006`) + Chain Status link
  - `ops-dashboard.html` — Event Stream 24h (commit `da00881`)
  - `dashboard.html` — Hardware Pairing panel (commit `f01a31a`)
  - `wallet.html` — Web3 refresh + BSCScan link (commit `da00881`)
  - `community.html` — mobile flex-wrap fix (commit `0668d9d`)
  - `js/translations.js` + `js/ai-assistant.js` — **i18n "65%" purge** on 5 languages (HE/EN/RU/AR/FR) via parallel agent (commit `7ff9db1`). `grep 65% website/js/ → 0 matches` (down from 25). Handoff: `ops/SESSION_HANDOFF_20260421_I18N_CLOSURE.md`
  - `blockchain.html` + `status.html` + `earn.html` + `invite.html` — Dynamic Yield cleanup + Arkham deep-links (commit `f5c7367`)
  - `shared.js` — footer extended + Research Lab + Reality Dashboard links on all pages (commit `5a0c078`)
  - Nav + Site Map FAB (commit `c25e1fc`)

### Security State (Oct 2026-04-21 Late)
- **COMPROMISED TODAY (required rotation):** OpenAI, Gemini, Groq, JWT_SECRET, ENCRYPTION_KEY, 3 bot tokens (Guardian/ExpertNet/SLH_AIR), ADMIN_API_KEYS, BSCScan, Bitquery — כולם הודבקו לצ'אט והופצו לזיכרון
- **Feedback memory נוסף:** `feedback_never_paste_secrets.md` — בשיחות הבאות אחסום אוטומטית
- **ADMIN_API_KEYS אומת פעיל:** `curl -H "X-Admin-Key: slh_admin_2026_rotated_04_20" /api/admin/devices/list` החזיר 3 devices → הוכיח שה-env כן מוגדר. Reality Reset memory תוקנה בהתאם.

---

## 2. מה בוצע ב-Night 21.4 — רשימה מלאה

### רצף מאוחד (שלושה סבבים של agents אוטונומיים + Osif):

#### Phase A — Core infrastructure
1. `shared_db_core.py` נוצר ומחובר ל-main.py (Phase 0 DB Core)
2. Phase 0B: 16 שירותים עברו migration — (botshop = repo עצמאי, לא submodule)
3. `PHASE_0B_REBUILD_BOTS.ps1` helper
4. Payment bug fix: `/api/payment/status/{user_id}` 500 → תוקן (deposits column mismatch). User 8789977826 received manual remediation + DM broadcast #26.

#### Phase B — Honest admin layer
5. `/api/ops/reality` endpoint + `/admin/reality.html` — Reality Dashboard (Arkham deep-links)
6. `/api/admin/events` + `/api/admin/link-phone-tg` + `/api/admin/devices/*` (chain of custody)
7. Admin key rotation UI (Night 20.4) + `slh2026admin` purge (10 modules)

#### Phase C — Observable chain
8. `/chain-status.html` — 6 פאנלים חיים (Railway API, Devices, Guardian, Ledger, Staking, Events)
9. Event Stream 24h ב-ops-dashboard
10. Hardware Pairing panel ב-dashboard.html
11. Chain Status links ב-admin + ops + footer

#### Phase D — Dynamic Yield pivot
12. API: referral cap 10→2 tiers (commit `cfc98e4`)
13. Course #1 "Dynamic Yield Economics" seeded ב-Railway Postgres (3 tiers Free/Pro/VIP ₪0/₪179/₪549)
14. Telegram broadcast #25 ל-11/11 users
15. Phantom audit pass 1 + pass 2 (earn/invite/status/blockchain cleaned, whitepaper left as legit "Target")

#### Phase E — Closing the loop
16. 5 new endpoints ב-commit `98cb7e4`: events/public, ops/credit, ops/approve-payment, ops/ban, performance
17. `/performance.html` Research Lab + Reality Dashboard footer links
18. `admin.html` Events tab inline (commit `5c53006`)
19. `community.html` mobile flex-wrap fix (commit `0668d9d`)
20. Guardian token rotated LOCALLY (`.env` ב-`D:/SLH_ECOSYSTEM/` ו-`D:/telegram-guardian-DOCKER-COMPOSE-ENTERPRISE/`). Bot alive: `@Grdian_bot` (id 8521882513)

**סה"כ commits היום:** ~20 ב-slh-api + ~15 ב-website + 1 ב-slh-guardian + 1 ב-GATE_BOTSHOP

---

## 3. מה פתוח עכשיו (סדר עדיפויות)

### 🔴 Blockers שלך (דורש גישה ידנית, 15-30 דק')

| # | פעולה | איפה | זמן |
|---|-------|------|-----|
| B1 | **Railway env:** הוסף `LEDGER_WORKERS_CHAT_ID` (מ-`getUpdates` של Guardian bot), `SLH_ADMIN_KEY` ל-Guardian service | Railway dashboard → slh-api → Variables | 5 |
| B2 | **Guardian restart:** `docker compose restart guardian-bot` (ב-`D:/telegram-guardian-DOCKER-COMPOSE-ENTERPRISE`) | Terminal | 2 |
| B3 | **localStorage paste:** `localStorage.setItem('slh_admin_password', '<NEW_ROTATED_KEY>')` ב-console של slh-nft.com/chain-status.html | F12 Console | 1 |
| B4 | **ledger-bot TOKEN=None crash loop:** env mismatch — container יש `BOT_TOKEN`, קוד קורא `TOKEN`. יישר ב-docker-compose `TOKEN=${BOT_TOKEN}` | Compose file | 5 |
| B5 | **Post-secret-exposure rotation:** אם עוד לא סיימת — רוטט OPENAI/GEMINI/GROQ/3 bots/JWT/ENCRYPTION/ADMIN/BSCScan/Bitquery | Per provider | 20 |

### 🟡 Manual ops (צריך גישה שלך)

| # | פעולה | הקשר |
|---|-------|------|
| M1 | `docker compose up -d --build` על 9 קונטיינרים דרך `ops/PHASE_0B_REBUILD_BOTS.ps1` (DryRun נתמך) | Phase 0B deploy |
| M2 | `curl -X POST /api/admin/link-phone-tg` לחיבור `972584203384` → TG `224223270` (device esp32-A1B2C3D4E5F6 ממתין) | אימות אישי |
| M3 | SQL review: user `8789977826` — refund ₪147 OR upgrade VIP +₪353 (payment bug 21.4 cleanup) | Railway DB |
| M4 | Flash firmware v3 via PlatformIO (USB) — `cd D:/SLH_ECOSYSTEM/ops/firmware/slh-device-v3 && pio run -t upload` | ESP32 hardware |
| M5 | `git push` ב-website repo (**5 commits local**: `7ff9db1` i18n purge + `0668d9d` mobile fix + `5c53006` events tab + `c25e1fc` nav + `5a0c078` performance page) | GitHub Pages deploy |
| M6 | רוטציית GUARDIAN_BOT_TOKEN ב-@BotFather (local .env כבר עודכן אבל ה-token עלול להיות compromised — vefify) | @BotFather |

### 🟢 אוטונומי מוכן לביצוע בסשן הבא

| # | משימה | תלות |
|---|-------|------|
| A1 | **Backend proxy `/api/bsc/*`** שמשתמש ב-Railway BSCSCAN_API_KEY → הפוך את 10/12 KPIs ב-blockchain.html לחיים | BSCScan key ב-Railway |
| A2 | **`/performance` command ב-@Grdian_bot** — קוד ב-`D:/telegram-guardian-DOCKER-COMPOSE-ENTERPRISE/app/` | Bot code access |
| ~~A3~~ | ~~i18n cleanup "65%"~~ | ✅ **DONE** by parallel agent (commit `7ff9db1`, 25→0 matches) |
| A3b | **Cache-bust version bump** — `?v=20260411i → ?v=20260421a` ב-43 HTML files (אחרת משתמשים עם טאב פתוח ימשיכו לראות "65% APY") | Post-i18n cleanup |
| A4 | **Events tab UX enhancement** — filter by time range, export CSV | Events tab shipped |
| A5 | **Task Scheduler** (Windows) ל-`daily_backtest.py` כל 6 שעות | Backtest script |
| A6 | **Telegram push alerts** לאותות trading חדשים | /api/performance populated |
| A7 | **Mobile responsive pass 2** — dashboard's flex grids, wallet tx-table scroll container, admin.html כ-desktop-only (משבירה מובייל) | community.html fix בסיס |
| A8 | **blockchain.html **Single Source of Truth** חיבור ל-`/api/tokenomics/stats` בלבד (להיפטר מ-BSCScan פרונטאלי) | Backend endpoint ready |

### 🔵 אסטרטגי (דורש החלטה שלך)

| # | נושא | בלוקר |
|---|------|-------|
| S1 | **Phase 2 Identity Proxy** | ארכיטקטורה |
| S2 | **Phase 3 Ledger unification** | איחוד ledgers |
| S3 | **Webhook migration** (22 בוטים ב-polling) | Topology change |
| S4 | **BSC DEX integration** (PancakeSwap Web3) | Paper trading קודם |
| S5 | **Mobile app MVP** (React Native / Flutter) | 2-3 שבועות |
| S6 | **GUARDIAN_AUDIT_AGENT_PROMPT run** ב-session נפרד (`ops/GUARDIAN_AUDIT_AGENT_PROMPT_20260421.md`) | Agent context |
| S7 | **Legal entity** (Roadmap 13+) | **הבלוקר הגדול ביותר למסחר אמיתי** |
| S8 | **BSCScan/DEX audit חיצוני** ל-SLH Token | Contract audit firm |

---

## 4. מפת ארכיטקטורה (Current)

```
┌───────────────────────────────────────────────────────────────────┐
│                         slh-nft.com (GitHub Pages)                │
│  43+ HTML pages │ shared.js footer │ admin.html (Events tab inline)│
└─────────────────────────────┬─────────────────────────────────────┘
                              │ fetch X-Admin-Key / public
                              ▼
┌───────────────────────────────────────────────────────────────────┐
│           slh-api-production.up.railway.app (FastAPI)             │
│  /api/health │ /api/admin/* │ /api/ops/* │ /api/events/public     │
│  /api/performance │ /api/tokenomics/* │ /api/academia/*           │
│                                                                    │
│  Phase 0 DB Core: shared_db_core.py → init_db_pool → Fail-fast 503│
└─────────────┬──────────────────────────┬──────────────────────────┘
              │                          │
              ▼                          ▼
      ┌──────────────┐          ┌──────────────────┐
      │  PostgreSQL  │          │     Redis        │
      │  (Railway)   │          │   (Railway)      │
      └──────────────┘          └──────────────────┘

                                     ┌──────────────────────┐
                                     │ Docker Compose (9+)  │
                                     │  - guardian-bot ⚠    │
                                     │  - academia-bot ✓    │
                                     │  - expertnet-bot ✓   │
                                     │  - nfty-bot ✓        │
                                     │  - tonmnh-bot ✓      │
                                     │  - match-bot ✓       │
                                     │  - admin-bot ✓       │
                                     │  - userinfo-bot ✓    │
                                     │  - campaign-bot ✓    │
                                     │  - wellness-bot ✓    │
                                     │  - slh-ledger 🔴     │
                                     │  - slh-claude-bot 🔵 │
                                     └──────────────────────┘

              ┌─────────────────────────┐
              │  BSC (BEP-20)           │
              │  - SLH token            │
              │  - PancakeSwap V2 pool  │
              │  - Genesis wallet       │
              └─────────────────────────┘

              ┌─────────────────────────┐
              │  TON network            │
              │  - Deposit address      │
              │  - (Ethereum future)    │
              └─────────────────────────┘

              ┌─────────────────────────┐
              │  ESP32-CYD firmware v3  │
              │  - Device pair API      │
              │  - Heartbeat events     │
              └─────────────────────────┘
```

**Legend:**
- ✓ healthy / migrated
- ⚠ needs restart for new env
- 🔴 crash loop (TOKEN=None mismatch, needs fix M6)
- 🔵 dormant (needs ANTHROPIC_API_KEY before launch)

---

## 5. Outstanding items mapped to roadmap

**Roadmap 13+ status (from `ops/ROADMAP_13_PLUS_20260421.md`):**

| # | Item | Status |
|---|------|--------|
| 13 | Mining infrastructure | 🔵 Q3-Q4 |
| 14 | User revenue system | 🔵 Q3-Q4 |
| 15 | ARCM = Arkham Intelligence | ✅ Clarified |
| 16-20 | UI/UX overhaul (slh-calm theme + toolbar) | 🟡 Partial (admin-reality + performance + events tab done) |
| 21 | PWA | 🔵 Q3 |
| 22 | Play Store + App Store | 🔵 Q3-Q4 |
| 23 | Support loop | 🔵 May |
| 24 | Payment rebuild | 🟡 Partial (payment bug fix 21.4) |
| 25 | Data consolidation | 🟡 Partial (shared_db_core Phase 0/0B done) |

**Pivot checklist (from DYNAMIC_YIELD_SPEC_20260420):**
- ✅ Fixed APY 48-65% → Revenue-Share (code)
- ✅ Referral 10 tiers → 2 tiers
- ✅ Course #1 built + priced + broadcasted
- ✅ Website pages cleaned (earn/invite/status/blockchain)
- 🟡 i18n cleanup (translations.js + ai-assistant.js) — spawn task queued
- 🔵 Course #2+ planning

---

## 6. Verified snapshots (empirical, 2026-04-21 late)

**Production probes:**
| URL | Status | Notes |
|-----|--------|-------|
| `/api/health` | 200 | `{"status":"ok","db":"connected","version":"1.1.0"}` |
| `/api/ops/reality` (no auth) | 403 | Properly gated |
| `/api/admin/events` (no auth) | 403 | Properly gated |
| `/api/admin/link-phone-tg` (no auth) | 403 | Properly gated |
| `/api/admin/devices/list` (with valid key) | 200 | Returns 3 devices, includes target user 972584203384 |
| `/api/academia/license/status` | 200 graceful | |
| `/api/academia/courses` | 200 | 3 courses: VIP ₪549 / Pro ₪179 / Free ₪0 |
| `/api/esp/heartbeat` (no auth) | 401 | Proper |
| `/api/device/claim/<any>` | 200 | Graceful |
| `/api/performance` | 200 | `available:false` — CSV missing, Run daily_backtest.py |
| `/api/events/public` | 200 | `error:"event_log_unavailable"` — table not populated yet |
| `/chain-status.html` | 200 | Live, auto-refresh 15s |
| `/device-pair.html` | 200 | Live |
| `/admin.html` Events tab | ✅ Verified in local preview | |
| `/community.html` mobile | ✅ Fixed + verified at 375px | |

**Known limitations:**
- `/api/performance` needs `daily_backtest.py` to generate CSV
- `/api/events/public` needs event_log table populated (probably DB migration pending or events not yet flowing)
- `blockchain.html` shows 2/12 KPIs live — other 10 rate-limited by frontend BSCScan calls (needs backend proxy)
- `admin.html` not mobile-responsive (by design — desktop backoffice)

---

## 7. Master doc cross-references

| Document | Purpose |
|----------|---------|
| `ops/SESSION_FULL_CLOSURE_20260421.md` | Afternoon closure (Round 1+2) |
| `ops/SESSION_HANDOFF_20260421_LATE.md` | Evening closure (Round 3) |
| `ops/OPEN_TASKS_MASTER_20260421.md` | 26-item consolidated task list (my earlier extract) |
| `ops/SESSION_HANDOFF_20260421_I18N_CLOSURE.md` | i18n "65%" purge parallel-agent handoff (10 sections) |
| `ops/SLH_PHASE0_HANDOFF_2026-04-21.md` | Operational handoff draft (test commands + checklist + commit templates) — per Osif's note |
| `ops/REALITY_RESET_20260421.md` | No-real-customers truth reset |
| `ops/ROADMAP_13_PLUS_20260421.md` | Strategic roadmap |
| `ops/DYNAMIC_YIELD_SPEC_20260420.md` | Pivot spec |
| `ops/ACADEMIA_PAYMENT_OVERHAUL_20260420.md` | Payment methods (6 options) |
| `ops/GUARDIAN_AUDIT_AGENT_PROMPT_20260421.md` | Audit agent briefing (reserved) |
| `ops/TASK_BOARD.md` | Active task tracker |
| `ops/ENDPOINTS_TEST_GUIDE.md` | API test reference |
| `CLAUDE.md` | System operating instructions (auth, conventions, rules) |
| `C:/Users/Giga Store/.claude/projects/D--/memory/MEMORY.md` | Claude's persistent memory index (39 entries) |
| **THIS FILE** | **Master handoff — read first for resumption** |

---

## 8. Recommended resumption order

**When you return:**

1. **5 דק' — verify production health:**
   ```bash
   curl https://slh-api-production.up.railway.app/api/health
   curl https://slh-api-production.up.railway.app/api/ops/reality -H "X-Broadcast-Key: <key>"
   ```

2. **10 דק' — close B1/B2/B3:** Railway env → Guardian restart → localStorage paste

3. **5 דק' — verify B4 (ledger):** `docker compose logs slh-ledger --tail 50`. If still crash loop, pick TOKEN fix:
   - Option A: `environment: TOKEN=${BOT_TOKEN}` ב-compose
   - Option B: Patch ledger code to read `BOT_TOKEN`

4. **1 דק' — git push website** (`git push origin main` ב-`D:/SLH_ECOSYSTEM/website`) — 4 local commits ready

5. **Then pick one:**
   - **Quick win:** Flash firmware v3 (M4, 20 דק')
   - **Data close:** SQL review user 8789977826 (M3)
   - **Autonomous code:** A1 (backend BSC proxy), A3 (i18n 65% purge), or A7 (mobile pass 2)

---

## 9. What I (Claude) verified vs inferred

**Verified empirically this session:**
- API endpoint statuses (via WebFetch)
- Admin key works (via Osif's curl test)
- Events tab renders + graceful 403 (via local preview)
- Community mobile fix (via preview at 375px)
- Git commits landed (via `git log`)

**Inferred from memory (may need fresh check):**
- Exact env vars in Railway
- Current state of Telegram broadcasts
- Bot container health (Docker ps not accessible from this session)

**Unknown / not tested:**
- Performance of backtest scripts (not run)
- Guardian bot /start /admin /whoami (local-only test)
- Firmware v3 behavior (hardware access needed)

---

*Generated by Claude Opus 4.7 (1M context) — 2026-04-21 late.*
*For Osif Kaufman Ungar · @osifeu_prog · 224223270.*
*Next session: start by reading this file + running verification in section 8.*
