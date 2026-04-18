# SLH Spark · Executor Agent Prompt · 2026-04-18
**Purpose:** Paste this entire prompt into a new Claude Code session to spawn a full-context executing agent.
**Request origin:** User wanted comprehensive system audit + fix everything broken.

---

## WHO I AM
- **Osif Kaufman Ungar** (@osifeu_prog, Telegram ID: 224223270)
- Solo Hebrew-speaking developer building SLH Spark — crypto investment ecosystem in Israel
- GitHub: osifeu-prog
- Windows 10 Pro, drives: C: (system), D: (projects)
- Working directory: D:\SLH_ECOSYSTEM\

## COMMUNICATION RULES
- Hebrew in UI, English in code/commits
- Direct action, no long explanations
- Never fake/mock data in production — use [DEMO] or test_ prefix
- Never minimize scope — all 25 bots matter
- "כן לכל ההצעות" = proceed with all suggestions

---

## PROJECT OVERVIEW

SLH Spark = institutional-grade digital investment ecosystem:
- **Website:** 43 HTML pages on GitHub Pages (slh-nft.com)
- **API:** FastAPI on Railway (slh-api-production.up.railway.app), ~7000 lines in main.py, 113 endpoints
- **Bots:** 25 Telegram bots via Docker Compose (aiogram 3.x)
- **Blockchain:** SLH token on BSC (BEP-20), PancakeSwap V2 pool live
- **DB:** PostgreSQL 15 + Redis 7, 30+ tables, SHA-256 audit chain

### 5-Token Economy
| Token | Purpose | Price Target |
|-------|---------|-------------|
| SLH | Premium/governance | 444 ILS |
| MNH | Stablecoin | 1 ILS |
| ZVK | Activity rewards | ~4.4 ILS |
| REP | Reputation score | 0-1000+ |
| ZUZ | Anti-fraud "Mark of Cain" | Auto-ban at 100 |

### Key Addresses
- SLH Contract: 0xACb0A09414CEA1C879c67bB7A877E4e19480f022 (BSC BEP-20, 15 decimals)
- PancakeSwap Pool: 0xacea26b6e132cd45f2b8a4754170d4d0d3b8bbee
- Genesis Wallet: 0xd061de73B06d5E91bfA46b35EfB7B08b16903da4
- Main MetaMask: 0xD0617B54FB4b6b66307846f217b4D685800E3dA4 (holds 199K SLH)

---

## REPOSITORY STRUCTURE
```
D:\SLH_ECOSYSTEM\
├── api/main.py                # FastAPI backend (ALSO synced to root main.py!)
├── main.py                    # ROOT COPY — Railway builds from HERE!
├── website/                   # GitHub Pages (separate git repo)
│   ├── js/shared.js           # Nav, auth, i18n, theme (1157 lines)
│   ├── js/translations.js     # 1000+ keys, 5 languages (2207 lines)
│   ├── js/analytics.js        # Visitor tracking
│   ├── js/ai-assistant.js     # Floating chat widget, 4 LLM providers
│   ├── js/web3.js             # MetaMask/Trust Wallet
│   ├── css/shared.css         # 7 themes, RTL, glassmorphism (2320 lines)
│   ├── admin.html             # Admin panel (19 sidebar pages)
│   ├── ops-dashboard.html     # Live system monitoring
│   └── ...43 HTML files total
├── ops/                       # SESSION_HANDOFF files, upgrade plans
├── docker-compose.yml         # 25 bot services + postgres + redis
├── .env                       # Bot tokens + API keys (DO NOT COMMIT)
└── *-bot/ directories         # Individual bot codebases
```

## GIT REPOS & DEPLOYMENT
| Repo | Branch | Deploys To |
|------|--------|------------|
| github.com/osifeu-prog/slh-api | master | Railway (auto-deploy) |
| github.com/osifeu-prog/osifeu-prog.github.io | main | GitHub Pages (slh-nft.com) |

**CRITICAL:** Railway builds from ROOT main.py, NOT api/main.py. Always:
```bash
cp api/main.py main.py
git add main.py api/main.py
```

---

## WORK RULES (FROM REAL PRODUCTION BUGS)

### Always Do
- Read latest ops/SESSION_HANDOFF_*.md at start
- Check API health: curl slh-api-production.up.railway.app/api/health
- Use real data from API — never mock/fake in production
- Hebrew UI text, English code/commits
- Update SESSION_HANDOFF at end of session

### Never Do
- Never put passwords/tokens in HTML (use localStorage from admin login)
- Never use `_ensure_tables` — tables created at startup, use specific ensure functions
- Never assume display_name column exists (use try/except)
- Never push .env to git
- Never give 50 SLH as reward (= ₪22,200!) — use 500 ZVK max
- Never show mock data as real

### Admin Auth
- Admin panel stores password in localStorage.slh_admin_password
- API uses X-Admin-Key header
- Default key: slh2026admin (needs rotation)

---

## CRITICAL SECURITY ISSUES (P0)

### SEC-1: Admin Passwords in Public HTML
- Files: broadcast-composer.html, ecosystem-guide.html
- Exposed passwords: slh2026admin, slh_admin_2026, slh-spark-admin, slh-institutional
- Agent worked on removal — VERIFY IF COMPLETE

### SEC-2: Unprotected API Endpoints
- POST /api/tokenomics/burn — NO AUTH
- POST /api/tokenomics/reserves/add — NO AUTH
- POST /api/tokenomics/internal-transfer — NO AUTH

### SEC-3: Railway Secrets Missing
- JWT_SECRET: ❌ EMPTY (auth broken)
- ADMIN_API_KEYS: ❌ using defaults
- ADMIN_BROADCAST_KEY: ❌ using default
- BOT_SYNC_SECRET: ❌ using default
- BITQUERY_API_KEY: ❌ dummy "1123123"

### SEC-4: Wallet Address Mismatch
- Code has: 0xd061de73B06d5E91bfA46b35EfB7B08b16903da4
- Chat had: 0xD0617B54FB4b6b66307846f217b4D685800E3dA4
- Found in 5 HTML files + API — need to confirm which is correct

### SEC-5: 31 Bot Tokens Exposed
- Need rotation via rotate.html tool
- Guardian remote repo broken (404): https://github.com/osifeu-prog/gardient2.git

---

## SPECIAL PROJECTS

### ExpertNet (Zvika's Franchise Bot)
- Bot: @SLH_AIR_bot (token: 8530795944)
- Zvika's Telegram: 7757102350 (@Osif83)
- TON wallet: UQDhfyUPSJ8x9xnoeccTl55PEny7zUvDW8UabZ7PdDo52noF
- BNB wallet: 0x82815fA224Dd57FC009754cD55438f6a1C020252
- Payment gate ACTIVE, activation fee 22.221 ILS

### Ambassador SaaS Model
- Each ambassador gets a bot as entry to full SLH ecosystem
- Target: factory workers (600 at Zvika's factory) + families

### Academia Bot (@SLH_Academia_bot)
- Revenue engine: VIP flow → approve → referrals → multi-language
- Priority: payment→approve→unlock flow first

---

## KEY URLs
- Website: https://slh-nft.com
- Ops Dashboard: https://slh-nft.com/ops-dashboard.html
- Admin Panel: https://slh-nft.com/admin.html
- API Docs: https://slh-api-production.up.railway.app/docs
- API Health: https://slh-api-production.up.railway.app/api/health

---

## TASK FOR YOU

אני צריך בדיקות מקיפות לכל המערכת — אתר, API, בוטים. תעשה:

1. **בדוק את ה-API** — curl לכל endpoint קריטי, תבדוק מה עובד מה לא
2. **בדוק את האתר** — כל 43 דפים, נאב, i18n, theme, לינקים שבורים
3. **בדוק אבטחה** — תאמת שה-SEC issues עדיין קיימים או תוקנו
4. **בדוק את ה-Git** — status בשני repos, שינויים לא מפושים
5. **בדוק Docker** — מצב הקונטיינרים, לוגים של שגיאות
6. **תקן את כל הבלאגנים** — סדר, תקן, נקה, ודא שהכל עובד
7. **תן דוח מצב מלא** — מה עובד, מה שבור, מה דחוף

קרא קודם:
- D:\SLH_ECOSYSTEM\CLAUDE.md
- D:\SLH_ECOSYSTEM\ops\SESSION_HANDOFF_20260418_FINAL.md
- D:\SLH_ECOSYSTEM\ops\MASTER_WORKPLAN_20260418.md
- C:\Users\Giga Store\.claude\projects\D--\memory\MEMORY.md

תתחיל מיד בביצוע — אל תשאל אותי שאלות מיותרות. תבצע. אני רוצה דוח סופי מסודר בסוף.
