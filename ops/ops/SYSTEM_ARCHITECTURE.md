# SLH Spark · System Architecture
**Status:** Living doc. Last updated: 2026-04-21.
**Purpose:** Single source of truth on what exists, where it runs, and how pieces connect. Read this first when picking up the project cold.

---

## 1. System at a glance

```
                                    ┌──────────────────────────┐
                                    │  End user (Telegram)      │
                                    └────────────┬──────────────┘
                                                 │
                                                 ▼
    ┌────────────────────┐           ┌──────────────────────────┐
    │ Website (GH Pages) │◄──fetch──►│  @SLH_AIR_bot + 24 others│
    │ slh-nft.com        │   REST    │  (aiogram 3.x, polling)  │
    │ 43 HTML pages      │           └────────────┬─────────────┘
    └──────────┬─────────┘                        │
               │                                  │
               └──────────────┐                   │
                              ▼                   ▼
                    ┌──────────────────────────────────┐
                    │  FastAPI  (Railway)              │
                    │  slh-api-production.up.railway   │
                    │  ~11,000 lines main.py           │
                    │  113+ endpoints                  │
                    │  routes/*.py modular plugins     │
                    └──────────────┬───────────────────┘
                                   │ asyncpg
                                   ▼
                    ┌──────────────────────────────────┐
                    │  Postgres 15 + Redis 7           │
                    │  (Railway-managed)               │
                    │  + local docker compose mirror   │
                    └──────────────────────────────────┘
                                   │
              ┌────────────────────┼────────────────────┐
              ▼                    ▼                    ▼
    ┌─────────────────┐  ┌──────────────────┐  ┌────────────────┐
    │ BSC (PancakeSwap│  │ TON Network       │  │ Payment rails  │
    │ SLH token)      │  │ (TonViewer)       │  │ TON/BNB/fiat  │
    └─────────────────┘  └──────────────────┘  └────────────────┘
```

---

## 2. Components

### Frontend — `website/` (separate git repo)
- Repo: `github.com/osifeu-prog/osifeu-prog.github.io`
- Host: GitHub Pages (slh-nft.com, custom domain)
- 43 HTML files, vanilla JS (no framework)
- Shared: `js/shared.js` (1157 lines — nav, auth, i18n, theme, FAB)
- Shared: `js/translations.js` (5 langs: he/en/ru/ar/fr)
- Admin: `admin.html` (19 sidebar pages)
- Auth: `localStorage.slh_admin_password` → `X-Admin-Key` header

### Backend — `api/` + root `main.py`
- Repo: `github.com/osifeu-prog/slh-api` (master)
- Host: Railway (auto-deploy on push to master)
- **CRITICAL:** Railway builds from root `main.py`, NOT `api/main.py`. Keep both in sync.
- Stack: FastAPI + asyncpg + aiogram 3.x
- 113+ endpoints declared in `api/main.py` + `routes/*.py` modules
- Routes modules: ai_chat, payments_auto, payments_monitor, community_plus, aic_tokens, pancakeswap_tracker, sudoku, dating, broadcast, love_tokens, treasury, creator_economy, wellness, threat, whatsapp, system_audit, agent_hub, campaign_admin, academia_ugc, bot_registry, admin_rotate, **ambassador_crm** (new 2026-04-21)

### Bots — `*-bot/` directories, orchestrated by `docker-compose.yml`
- 25 Telegram bots via Docker Compose
- Image template: `dockerfiles/Dockerfile.template`
- Shared code: `shared/bot_template.py` (reads `BOT_TOKEN` from env)
- Key bots: admin-bot, airdrop, botshop, campaign-bot, expertnet-bot, factory, fun, guardian, ledger-bot, match-bot, nfty-bot, osif-shop, promo, school, tonmnh-bot, userinfo-bot, wallet, wellness-bot
- Status: polling (not webhook) — 22/22 bots

### Database
- Postgres 15 (Railway-managed for prod; local docker for dev)
- Redis 7 (Railway-managed)
- Schema: 30+ tables, SHA-256 audit chain on broadcasts/payments
- Key tables: `users`, `web_users`, `deposits`, `broadcast_history`, `broadcast_log`, `ambassador_contacts` (new), `community_posts`, `audit_log`, payment/token tables

### Blockchain
- **SLH Token**: BSC BEP-20, `0xACb0A09414CEA1C879c67bB7A877E4e19480f022` (15 decimals)
- **PancakeSwap Pool**: `0xacea26b6e132cd45f2b8a4754170d4d0d3b8bbee`
- **Genesis Wallet**: `0xd061de73B06d5E91bfA46b35EfB7B08b16903da4`
- **Main MetaMask**: `0xD0617B54FB4b6b66307846f217b4D685800E3dA4` (holds 199K SLH)
- TON Network: side integration for TON-denominated products

---

## 3. 5-token economy

| Token | Purpose | Status |
|-------|---------|--------|
| SLH | Premium/governance, target 444 ILS | Live on BSC, PancakeSwap pool active |
| MNH | Stablecoin pegged to 1 ILS | Internal ledger only |
| ZVK | Activity rewards (~4.4 ILS) | Internal, earned via contributions |
| REP | Reputation score (0–1000+) | Internal, tiered |
| ZUZ | Anti-fraud "Mark of Cain" | Guardian system, auto-ban at 100 |
| AIC | AI credits (~$0.001) | Added late — `routes/aic_tokens.py` |

---

## 4. Repository layout

```
D:\SLH_ECOSYSTEM\                  # root (main git repo: slh-api)
├── api/main.py                    # backend (mirror — source of truth for review)
├── main.py                        # ROOT COPY — Railway deploys from here
├── routes/                        # modular plugins (APIRouter + set_pool pattern)
│   ├── ambassador_crm.py          # NEW 2026-04-21 — CRM Phase 0
│   ├── broadcast.py
│   ├── payments_auto.py
│   ├── sudoku.py
│   ├── treasury.py
│   └── ... ~20 modules
├── shared/                        # cross-bot libs
│   ├── bot_template.py            # minimal bot shell
│   ├── shared_db_core.py          # asyncpg pool init
│   └── slh_payments/              # payment engine
├── docker-compose.yml             # 25 bot services + postgres + redis
├── website/                       # separate git — GitHub Pages
│   ├── js/shared.js
│   ├── js/translations.js
│   ├── admin/                     # admin-only pages (reality.html, etc.)
│   └── ... 43 HTML files
├── ops/                           # operational docs + handoffs (this file lives here)
├── scripts/                       # one-off automation (onboarding DMs, data-integrity audit)
├── .githooks/pre-commit           # drift guard (active via core.hooksPath)
├── slh-start.ps1                  # one-command orchestrator (run this first!)
└── CLAUDE.md                      # human-facing project rules
```

---

## 5. Runtime operations

### Start everything
```powershell
.\slh-start.ps1                    # full start + health check
.\slh-start.ps1 -StatusOnly        # just check state
.\slh-start.ps1 -SkipBuild         # if no Dockerfile changes
```

### Deploy to production
- **API:** `git push origin master` on repo root → Railway auto-deploys from `main.py`
- **Website:** `git push origin main` in `website/` → GitHub Pages rebuilds (~60s)

### Data integrity check
```powershell
python scripts\audit_data_integrity.py
```
Exits non-zero on HIGH findings. Run before every release.

### Pre-commit safety
`.githooks/pre-commit` active (drift guard). Blocks commits with >300 lines or >100 net deletions without `feat/refactor/docs/ops/chore/test(<scope>):` message prefix, or `GUARD_CONFIRMED=1` bypass.

---

## 6. Authentication layers

| Layer | Used by | Secret source |
|-------|---------|---------------|
| `X-Admin-Key` header | admin API endpoints | `ADMIN_API_KEYS` env (comma-sep) |
| `X-Broadcast-Key` header | `/api/ops/*`, `/api/broadcast/*` | `ADMIN_BROADCAST_KEY` env (default `slh-broadcast-2026-change-me`) |
| JWT Bearer | user-facing routes | `JWT_SECRET` env |
| `localStorage.slh_admin_password` | admin.html panel | set per-session via browser F12 Console |
| `localStorage.slh_broadcast_key` | admin/reality.html | same |
| Device HMAC | `/api/esp/*` (ESP32 devices) | per-device signing_token in NVS |

---

## 7. Known issues snapshot (live as of 2026-04-21)

| ID | Issue | Severity | Note |
|----|-------|----------|------|
| — | Railway deploy pipeline stuck | **HIGH** | Commits `b48a1b1`, `7c06bbc`, `b60cec2` queued. User-action required: Railway dashboard. |
| — | Yahav (`7940057720`) not reachable via bot DM | MED | Bot can't initiate — needs user to `/start @SLH_AIR_bot` first |
| — | `Your Name <your.email@example.com>` in recent git commits | LOW | Osif's global git config unset — see CLAUDE.md |
| — | 414 curly quotes remain in string content of `api/main.py` | LOW | Non-blocking (inside string literals, not code) |
| — | `docker-compose.yml` dirty from parallel session | MED | Avoid `git add -A`; stage surgically |
| — | Tzvika classification | LOW | `b48a1b1` promoted to founder, pending deploy |
| — | p2p escrow feature (097eafe) | — | Reverted with b60cec2 (was non-functional). To be re-added with proper ASCII quotes. |

---

## 8. Incident log references

- [INCIDENT_20260421_GIT_DRIFT](INCIDENT_20260421_GIT_DRIFT.md) — 694-line near-miss; guard shipped in response
- [HOOKS_IMPROVEMENT_PLAN_20260421](HOOKS_IMPROVEMENT_PLAN_20260421.md) — pre-commit roadmap
- [TECH_SUMMARY_20260421_NIGHT_LATE](TECH_SUMMARY_20260421_NIGHT_LATE.md) — same-day technical closure
- [SESSION_HANDOFF_20260422_NEXT](SESSION_HANDOFF_20260422_NEXT.md) — pickup procedure

---

## 9. Rules of the road (pinned)

1. **Never fake data.** No `|| 47` fallbacks, no hardcoded counts. Display `--` when unknown.
2. **Never commit `.env`.** `.env.template` only.
3. **Verify before commit:** `git diff --stat` is mandatory. Drift > 50 lines relative to expected = halt.
4. **Railway builds from root `main.py`.** Sync both `main.py` and `api/main.py` on every API change.
5. **Money flows need a legal entity first.** CRM-style features (ambassador_crm) are fine; investment-mediating features are not (yet).
6. **PowerShell ≠ Browser Console.** `curl.exe` / `docker` / `git` go to PowerShell; `localStorage.*` / `location.*` / `fetch(...)` go to F12 Console.
7. **Messages to users are user-visible actions.** Always preview before sending; log recipients + broadcast_id.

---

## 10. What this doc is NOT

- Not an API reference — see `ops/API_REFERENCE.md` (planned, auto-gen from `/openapi.json`).
- Not a runbook — see `ops/OPS_RUNBOOK.md` (planned).
- Not a sales pitch — see `whitepaper.html`.

_Next writeup: auto-generate `API_REFERENCE.md` from `/openapi.json`; add architecture diff vs. last month when relevant._
