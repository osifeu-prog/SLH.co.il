# SLH Spark Ecosystem - Project Brief
> Last updated: 2026-04-08 | Version: 2.0
> Owner: Osif (Telegram ID: 224223270)

## Mission
SLH Spark = decentralized investment + education + community ecosystem.
Each bot = paid economic unit. The website (slh-nft.com) is the central hub.

## Live Infrastructure

### Website (GitHub Pages)
- **URL**: https://slh-nft.com
- **Repo**: github.com/osifeu-prog/osifeu-prog.github.io (branch: main)
- **Pages**: 17 HTML pages (dashboard, wallet, trade, earn, community, etc.)
- **Stack**: Vanilla JS, CSS3, i18n (HE/EN/RU/AR/FR)

### API (Railway)
- **URL**: https://slh-api-production.up.railway.app
- **Repo**: github.com/osifeu-prog/slh-api (branch: master)
- **Stack**: FastAPI + asyncpg + PostgreSQL
- **Endpoints**: 30+ REST endpoints

### Docker Bots (Local)
- **Location**: D:\SLH_ECOSYSTEM\docker-compose.yml
- **Bots**: 25 containerized Telegram bots
- **DB**: PostgreSQL (slh-postgres:5432) + Redis (slh-redis:6379)
- **Password**: slh_secure_2026

### Standalone Bots
- **NFTY Bot** (@NFTY_madness_bot): D:\SLH_BOTS\ (aiogram + SQLite)
- **Guardian**: D:\telegram-guardian-DOCKER-COMPOSE-ENTERPRISE\

## Token & Economy
- **SLH Token (BSC)**: 0xACb0A09414CEA1C879c67bB7A877E4e19480f022
- **TON Wallet**: UQCr743gEr_nqV_0SBkSp3CtYS_15R3LDLBvLmKeEv7XdGvp
- **Registration**: 44.4 ILS = 0.1 SLH token + full access
- **Referral**: 10-generation commission (10%/5%/3%/2%/1%/0.5%...)

## Key Credentials
- **Admin Telegram ID**: 224223270
- **API Admin Key**: osif_slh_admin_2024 (legacy) / slh_admin_2026 (env)
- **Docker PG**: postgres:slh_secure_2026@localhost:5432/slh_main
- **Railway PG**: set via DATABASE_URL env var on Railway

## Auth Flow
1. User clicks Telegram Login Widget on dashboard.html
2. HMAC verified server-side at /api/auth/telegram
3. JWT issued (12h expiry), stored in localStorage as slh_jwt
4. Registration check: is_registered boolean in web_users table
5. Unregistered users see payment panel (44.4 ILS → TON wallet)
6. Admin approves → 0.1 SLH credited + referral commissions distributed
