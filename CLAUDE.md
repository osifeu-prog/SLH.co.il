# SLH Spark Ecosystem — Claude Code Instructions

## Who is the user
- **Osif Kaufman Ungar** (@osifeu_prog, Telegram ID: 224223270)
- Solo Hebrew-speaking developer building SLH Spark — a crypto investment ecosystem in Israel
- Works in Hebrew, expects Hebrew in UI. Code comments/commits in English
- Prefers direct action over long explanations. "כן לכל ההצעות" is common — means proceed with all suggestions
- Has 10+ institutional investors interested (1M+ ILS each)

## Project Overview
SLH Spark is an institutional-grade digital investment ecosystem with:
- **Website:** 140+ HTML pages on GitHub Pages (slh-nft.com); 60 pages in root + subdirectories (blog/, admin/, miniapp/, academy/, prompts/)
- **API:** FastAPI ~230 endpoints, **11,765 lines** in main.py — **NOT YET DEPLOYED to Railway** (verified 2026-04-27 via HTTP logs returning 404 on /api/*).
  - Code lives in `D:\SLH_ECOSYSTEM` (remote `origin` → `osifeu-prog/slh-api`)
  - Railway service `SLH.co.il` runs a different codebase (Python http.server + Telegram bot from `osifeu-prog/SLH.co.il` repo) at `slhcoil-production.up.railway.app` + `www.slh.co.il`
  - Plan: deploy FastAPI as a new Railway service `slh-fastapi` connected to `osifeu-prog/slh-api`. See `ops/VISION_NEXT_STEPS_2026-04-27.md`.
  - Reality reference: `ops/SYSTEM_REALITY_2026-04-27.md`
- **Bots:** 25 Telegram bots via Docker Compose (aiogram 3.x), all currently on polling
- **Blockchain:** SLH token on BSC (BEP-20), PancakeSwap V2 pool live
- **Database:** PostgreSQL 15 + Redis 7
- **ESP32:** Hardware device-registry + firmware (esp/, device-registry/)
- **Design system:** New `css/slh-neural.css` provides DNA + Neural Network theme via `[data-theme="neural"]`

## 5-Token Economy
| Token | Purpose | Status |
|-------|---------|--------|
| SLH | Premium/governance, target 444 ILS | Live on BSC, PancakeSwap pool active |
| MNH | Stablecoin pegged to 1 ILS | Internal only |
| ZVK | Activity rewards (~4.4 ILS) | Internal, earned via contributions |
| REP | Personal reputation score | Internal, 0-1000+ tiers |
| ZUZ | Anti-fraud "Mark of Cain" | Guardian system, auto-ban at 100 |

## Key Addresses
- **SLH Contract:** 0xACb0A09414CEA1C879c67bB7A877E4e19480f022 (BSC BEP-20, 15 decimals)
- **PancakeSwap Pool:** 0xacea26b6e132cd45f2b8a4754170d4d0d3b8bbee
- **Genesis Wallet:** 0xd061de73B06d5E91bfA46b35EfB7B08b16903da4
- **Main MetaMask:** 0xD0617B54FB4b6b66307846f217b4D685800E3dA4 (holds 199K SLH)

## Repository Structure
```
D:\SLH_ECOSYSTEM\              # Main project root
├── api/main.py                # FastAPI backend (also synced to root main.py)
├── main.py                    # ROOT COPY — Railway builds from here!
├── website/                   # GitHub Pages (separate git repo)
│   ├── js/shared.js           # Shared navigation, themes, i18n
│   ├── js/translations.js     # Multi-language support
│   ├── admin.html             # Admin panel (19 sidebar pages)
│   ├── ops-dashboard.html     # Live system monitoring
│   └── ...43 HTML files
├── ops/                       # Operations docs, handoffs, plans
├── docker-compose.yml         # 25 bot services + postgres + redis
├── .env                       # Bot tokens + API keys (DO NOT COMMIT)
└── *-bot/ directories         # Individual bot codebases
```

## Git Repos & Deployment
| Repo | Branch | Deploys To |
|------|--------|------------|
| github.com/osifeu-prog/slh-api | master | (legacy — verify still in use) |
| github.com/osifeu-prog/SLH.co.il | main | **Railway production** (slhcoil-production.up.railway.app + www.slh.co.il) |
| github.com/osifeu-prog/osifeu-prog.github.io | main | GitHub Pages (slh-nft.com) |

**CRITICAL:** Railway builds from ROOT main.py, not api/main.py. Always sync both:
```bash
cp api/main.py main.py
git add main.py api/main.py
```

## Work Rules

### Always Do
- Start every session by reading `ops/SESSION_HANDOFF_*.md` (latest date)
- Check API health: `curl slh-api-production.up.railway.app/api/health`
- Use real data from API — never mock/fake data in production pages
- Push website changes to `website/` repo (main branch)
- Push API changes to root repo (master branch) — sync both main.py files
- Write Hebrew UI text, English code/commits
- Log overnight work to `ops/overnight-health-log.md`
- Update `ops/SESSION_HANDOFF_*.md` at end of session

### Never Do
- Never put passwords/tokens in HTML files (use localStorage from admin login)
- Never use `_ensure_tables` — tables are created at startup
- Never assume display_name column exists (use try/except fallback)
- Never push .env file to git
- Never give away 50 SLH as reward (too expensive at 444 ILS each)
- Never show mock data as real — use `[DEMO]` tag or `test_` prefix

### Data Conventions
| Marker | Meaning |
|--------|---------|
| `test_` prefix | Test/demo data |
| `[DEMO]` tag | Placeholder content |
| `[SEED]` tag | Initial seed data |
| `--` | No data available |
| `N/A` | Not applicable |

### Admin Authentication
- Admin panel at /admin.html stores password in `localStorage.slh_admin_password`
- API uses `X-Admin-Key` header
- All admin-only pages read from localStorage — no hardcoded passwords
- Default keys: slh2026admin (primary, will be rotated)

## Current State (update each session)
- **API Version:** ~1.1.0 (~230 endpoints in 11,765 lines of main.py)
- **Pages:** 140+ HTML across root + subdirectories
- **Theme coverage:** ~22% (31/140 pages have data-theme attribute)
- **i18n coverage:** ~40% (57/140 pages reference translations.js or data-i18n)
- **Design system:** `slh-neural.css` (new, 2026-04-27) — DNA + Neural theme available via `[data-theme="neural"]`
- **Landing prototype:** `landing-v2.html` — investor-facing, demonstrates new design system
- **Contributors:** 5 verified (Tzvika, Eli, Zohar, Osif, Yakir)
- **Users registered:** 9 (4 contributors not yet logged into website)
- **Genesis raised:** 0.08 BNB

## Key People
- **Osif** — Owner/developer (224223270)
- **Zohar Shefa Dror** — Active contributor, asks good QA questions
- **Tzvika** — Co-founder, crypto trader
- **Eli** — Contributor
- **Yakir Lisha** — Contributor

## Session Start Checklist
1. Read latest `ops/SESSION_HANDOFF_*.md`
2. Read `ops/SYSTEM_REALITY_2026-04-27.md` and `ops/VISION_NEXT_STEPS_2026-04-27.md` for current ground truth
3. `curl https://slhcoil-production.up.railway.app/api/health` — returns 404 today (the simple bot, not FastAPI)
4. Once FastAPI is deployed (per VISION_NEXT_STEPS): `curl https://slh-fastapi-production.up.railway.app/api/health`
5. Check `git status` in both repos
6. Ask user what's priority today
7. Check if Railway env vars are set (JWT_SECRET, ADMIN_API_KEYS, etc.)

## Pending Critical Items (verified 2026-04-27)
- [ ] **🔴 P0 BLOCKED (Osif):** Railway env vars MISSING — only DATABASE_URL/REDIS_URL/OPENAI_API_KEY set. Need: JWT_SECRET, ADMIN_API_KEYS, ENCRYPTION_KEY, ADMIN_BROADCAST_KEY, INITIAL_ADMIN_PASSWORD, INITIAL_TZVIKA_PASSWORD, ADMIN_USER_ID. See `ops/SECURITY_FIX_PLAN_2026-04-27.md` Section A.
- [ ] **🔴 P0:** Rotate Binance EXCHANGE_API_KEY/EXCHANGE_SECRET (live trading creds in .env)
- [ ] **🔴 P0:** Rotate 30 remaining Telegram bot tokens (1/31 done — GAME_BOT_TOKEN on 2026-04-17)
- [ ] **🟠 P1:** Add JWT auth to 3 sensitive endpoints (/api/user/{id}, /api/user/wallet/{id}, /api/user/full/{id}) — requires frontend audit first
- [ ] **🟠 P1:** Remove .env backup files from project root (4 files, may contain old secrets)
- [ ] **🟠 P1:** Remove test/demo code from production HTML (admin/reality.html, encryption.html)
- [ ] 4 contributors need to log in to website to receive ZVK — external action
- [ ] Webhook migration (polling → webhooks) — all 25 bots still polling
- [ ] wallet.html: show on-chain balances (BSC + TON) — endpoints ready
- [ ] Migrate 109 remaining pages to slh-neural.css design system — see `ops/SLH_NEURAL_MIGRATION_2026-04-27.md`

## Recent Session Changes (2026-04-27)
- ✅ `main.py:8471` + `api/main.py:8471`: Replaced hardcoded `slh_ceo_2026` for Tzvika seed with `INITIAL_TZVIKA_PASSWORD` env var pattern (matches Osif at line 8465)
- ✅ `docker-compose.yml:358`: nfty-bot DATABASE_URL now uses `${DB_PASSWORD:-...}` fallback
- ✅ `website/css/slh-neural.css`: New design system — DNA + Neural theme, glassmorphism, token nodes, animated synapses
- ✅ `website/landing-v2.html`: Investor-facing landing page prototype
- ✅ `ops/SECURITY_FIX_PLAN_2026-04-27.md`: Full security audit + Railway env var instructions
- ✅ `ops/SLH_NEURAL_MIGRATION_2026-04-27.md`: Migration plan for remaining 140 pages

## Full task status
See [TASKS_STATUS_2026-04-18.md](TASKS_STATUS_2026-04-18.md) — consolidated status of all 73 tasks across 5 files, with honest verification against live state.

## Onboarding (AI agents + humans)
See [PROJECT_GUIDE.md](PROJECT_GUIDE.md) — complete onboarding including: repo connect, API access, bot deploy, page patterns, common tasks, AI agent prompt template.
