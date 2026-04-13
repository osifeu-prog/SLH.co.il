# SLH Spark Ecosystem — Claude Code Instructions

## Who is the user
- **Osif Kaufman Ungar** (@osifeu_prog, Telegram ID: 224223270)
- Solo Hebrew-speaking developer building SLH Spark — a crypto investment ecosystem in Israel
- Works in Hebrew, expects Hebrew in UI. Code comments/commits in English
- Prefers direct action over long explanations. "כן לכל ההצעות" is common — means proceed with all suggestions
- Has 10+ institutional investors interested (1M+ ILS each)

## Project Overview
SLH Spark is an institutional-grade digital investment ecosystem with:
- **Website:** 43 HTML pages on GitHub Pages (slh-nft.com)
- **API:** FastAPI on Railway (slh-api-production.up.railway.app), ~7000 lines in main.py
- **Bots:** 25 Telegram bots via Docker Compose (aiogram 3.x)
- **Blockchain:** SLH token on BSC (BEP-20), PancakeSwap V2 pool live
- **Database:** PostgreSQL 15 + Redis 7

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
| github.com/osifeu-prog/slh-api | master | Railway (auto-deploy) |
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
- **API Version:** 1.1.0 (113 endpoints)
- **Pages:** 43 HTML, all with analytics + AI assistant (100%)
- **Theme coverage:** 42% (18/43 pages)
- **i18n coverage:** 37% (16/43 pages)
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
2. `curl slh-api-production.up.railway.app/api/health`
3. Check `git status` in both repos
4. Ask user what's priority today
5. Check if Railway env vars are set (JWT_SECRET, ADMIN_API_KEYS)

## Pending Critical Items
- [ ] Railway env vars: JWT_SECRET (empty), ADMIN_API_KEYS (default)
- [ ] 4 contributors need to log in to website to receive ZVK
- [ ] Rotate .env bot tokens (31 exposed in chat history)
- [ ] Webhook migration (polling → webhooks)
- [ ] wallet.html: show on-chain balances (BSC + TON)
- [ ] i18n on 27 more pages
- [ ] Theme switcher on 25 more pages
