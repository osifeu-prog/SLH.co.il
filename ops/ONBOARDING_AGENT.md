# Agent / Developer Onboarding Guide
> Read this first before working on SLH Ecosystem

## Quick Start (5 minutes)

### 1. Understand the System
Read these files in order:
1. `ops/PROJECT_BRIEF.md` - What is SLH, key URLs, credentials
2. `ops/ARCHITECTURE.md` - System diagram, DB schema, bot map
3. `ops/TASK_BOARD.md` - Current sprint tasks, what's done/pending

### 2. Key File Locations
```
D:\SLH_ECOSYSTEM\
  |- api\main.py              # API backend (FastAPI) - THE most critical file
  |- website\                  # GitHub Pages site (slh-nft.com)
  |   |- dashboard.html        # Main user dashboard (largest file)
  |   |- community.html        # Community forum + marketplace
  |   |- js\shared.js          # Core JS utilities, auth, i18n
  |   |- js\translations.js    # i18n strings (5 languages)
  |- docker-compose.yml        # All 25 bot definitions
  |- ops\                      # THIS folder - project documentation

D:\SLH_BOTS\
  |- handlers\tamagotchi.py    # NFTY bot main logic
  |- run_tamagotchi_advanced.py # NFTY bot runner

D:\telegram-guardian-DOCKER-COMPOSE-ENTERPRISE\
  |- bot\app_factory.py        # Guardian bot
```

### 3. How to Deploy
```bash
# Website (GitHub Pages):
cd D:\SLH_ECOSYSTEM\website
git add . && git commit -m "message" && git push origin main
# Live in ~2 minutes at slh-nft.com

# API (Railway):
cd D:\SLH_ECOSYSTEM\api
git add . && git commit -m "message" && git push origin master
# Auto-deploys to Railway in ~3 minutes

# Docker Bots:
cd D:\SLH_ECOSYSTEM
docker compose restart slh-expertnet  # restart specific bot
docker compose up -d                   # start all
docker compose logs -f slh-guardian-bot # watch logs
```

### 4. Testing
See `ops/ENDPOINTS_TEST_GUIDE.md` for complete API testing guide.
Use `curl.exe` in PowerShell (not `curl` which is an alias).

### 5. Rules
- **Language**: Hebrew for UI text, English for code/comments
- **i18n**: All user-facing text uses data-i18n attributes (5 langs: HE, EN, RU, AR, FR)
- **Auth**: Telegram Login Widget + JWT (12h expiry)
- **DB**: PostgreSQL for API, SQLite for NFTY bot
- **Admin ID**: 224223270 (hardcoded in multiple places)
- **Never** push secrets to public repos
- **Always** add `Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>` to commits

## Current Priorities
1. NFTY Bot stabilization (aiosqlite migration done, needs testing)
2. Web3 wallet integration (MetaMask/TrustWallet)
3. Marketplace/ecommerce on community page
4. CBT/mindfulness system in NFTY bot

## Contact
- Telegram: @osifeu (Admin ID: 224223270)
- Website: https://slh-nft.com
- API: https://slh-api-production.up.railway.app
