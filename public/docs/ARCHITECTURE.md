# SLH Ecosystem Architecture / ארכיטקטורת מערכת SLH

> **Version:** 1.0.0
> **Last Updated:** 2026-04-08
> **Maintainer:** SPARK IND
> **Domain:** [slh-nft.com](https://slh-nft.com)

---

## Table of Contents / תוכן עניינים

1. [System Overview / סקירת מערכת](#1-system-overview--סקירת-מערכת)
2. [Infrastructure / תשתיות](#2-infrastructure--תשתיות)
3. [Data Flow / זרימת נתונים](#3-data-flow--זרימת-נתונים)
4. [Security Architecture / ארכיטקטורת אבטחה](#4-security-architecture--ארכיטקטורת-אבטחה)
5. [Bot Ecosystem / מערכת הבוטים](#5-bot-ecosystem--מערכת-הבוטים)
6. [Website Architecture / ארכיטקטורת האתר](#6-website-architecture--ארכיטקטורת-האתר)
7. [API Endpoints / נקודות קצה](#7-api-endpoints--נקודות-קצה)
8. [Database Schema / סכימת בסיס נתונים](#8-database-schema--סכימת-בסיס-נתונים)
9. [Revenue Model / מודל הכנסות](#9-revenue-model--מודל-הכנסות)
10. [Future Roadmap / תוכנית עתידית](#10-future-roadmap--תוכנית-עתידית)

---

## 1. System Overview / סקירת מערכת

### What is SLH Ecosystem?

SLH (Spark Ledger Hub) is a decentralized digital investment ecosystem built on Telegram, combining a multi-bot platform with a web portal, blockchain token economy (BSC + TON), staking, referrals, and community features. The entire system is managed by a solo developer and deployed across Docker containers, Railway cloud, and GitHub Pages.

### High-Level Architecture Diagram

```
                    Users (Telegram + Web)
                           |
              +------------+------------+
              |                         |
              v                         v
    +-------------------+     +---------------------+
    | slh-nft.com       |     | Telegram Bots       |
    | (GitHub Pages)    |     | (25 containers)     |
    | 15 HTML pages     |     | Docker Compose      |
    +--------+----------+     +--------+------------+
             |                         |
             | HTTPS                   | PostgreSQL + Redis
             v                         v
    +--------------------------------------------+
    | Railway FastAPI API                        |
    | slh-api-production.up.railway.app          |
    | 30+ RESTful endpoints                      |
    +--------+------------------+----------------+
             |                  |
             v                  v
    +----------------+    +-----------+
    | Railway PG     |    | Railway   |
    | PostgreSQL 15  |    | Redis 7   |
    +----------------+    +-----------+
             |
    +--------+--------+
    | Local Docker PG  |
    | (Development)    |
    | 5 databases      |
    +-----------------+
```

### Technology Stack / סטאק טכנולוגי

| Layer              | Technology                                         |
|--------------------|----------------------------------------------------|
| **Language**       | Python 3.11+                                       |
| **Bot Framework**  | aiogram 3.x, python-telegram-bot (legacy bots)     |
| **Web API**        | FastAPI + asyncpg + aiohttp + httpx                |
| **Database**       | PostgreSQL 15 (Docker local + Railway cloud)       |
| **Cache/Streams**  | Redis 7 (Docker local + Railway cloud)             |
| **Blockchain**     | web3.py (BSC/BEP-20), TON Center API (TON)        |
| **Website**        | Static HTML5/CSS3/JS (vanilla, no framework)       |
| **Containers**     | Docker Compose (25 service definitions)            |
| **API Hosting**    | Railway (production FastAPI, auto-deploy)          |
| **Site Hosting**   | GitHub Pages (slh-nft.com, custom domain)          |
| **Dev OS**         | Windows 10 Pro + Docker Desktop                   |
| **Wallet Connect** | TonConnect SDK (TON), MetaMask/Trust Wallet (BSC) |
| **Price Feeds**    | CoinGecko API, CryptoCompare, alternative.me      |
| **i18n**           | Custom JS engine (HE, EN, RU, AR, FR)             |

### Component Count

| Component            | Count |
|----------------------|-------|
| Telegram Bots        | 25    |
| Docker Containers    | 25 services + 2 infra (PG + Redis) |
| PostgreSQL Databases | 5 local + 1 Railway cloud           |
| Redis Databases      | 3 (DB 0, 1, 2)                      |
| Website Pages        | 15 HTML pages                        |
| API Endpoints        | 30+                                  |
| Bot Tokens           | 25 (19 unique + shared)              |
| Supported Languages  | 5 (HE, EN, RU, AR, FR)              |
| UI Themes            | 4 (dark, terminal, crypto, light)    |

---

## 2. Infrastructure / תשתיות

### 2.1 Docker Compose Architecture

All services are defined in a single `docker-compose.yml` at the ecosystem root. The system runs on Docker Desktop for Windows.

#### Shared Infrastructure Services

| Container        | Image              | Port  | Purpose                          |
|------------------|--------------------|-------|----------------------------------|
| `slh-postgres`   | postgres:15-alpine | 5432  | Primary PostgreSQL database      |
| `slh-redis`      | redis:7-alpine     | 6379  | Caching, sessions, event streams |

Both infrastructure services include health checks (5s interval, 5 retries) and are dependencies for all bot services.

#### Container Orchestration

```
docker-compose.yml
  |
  +-- Infrastructure (2)
  |     +-- slh-postgres (PostgreSQL 15)
  |     +-- slh-redis (Redis 7)
  |
  +-- Core Bots (9)
  |     +-- slh-core-bot (Academia)
  |     +-- slh-guardian-bot (Security)
  |     +-- slh-botshop (Store)
  |     +-- slh-wallet (TON/BNB)
  |     +-- slh-factory (Staking)
  |     +-- slh-fun (Promo)
  |     +-- slh-admin (Mission Control)
  |     +-- slh-expertnet (Zvika/AIR)
  |     +-- slh-airdrop (HUB)
  |
  +-- Special Bots (7)
  |     +-- slh-campaign (Google Sheets)
  |     +-- slh-game (Match)
  |     +-- slh-ton-mnh (TON Mainnet)
  |     +-- slh-osif-shop (WebApp)
  |     +-- slh-nifti (Wellness)
  |     +-- slh-nfty (NFT Marketplace)
  |     +-- slh-userinfo (User Info)
  |
  +-- Template Bots (9)
        +-- slh-ton, slh-ledger, slh-chance,
        +-- slh-selha, slh-ts-set, slh-crazy-panel,
        +-- slh-nft-shop, slh-beynonibank, slh-test-bot
```

#### Exposed Ports

| Port | Service                   |
|------|---------------------------|
| 5432 | PostgreSQL                |
| 6379 | Redis                     |
| 8001 | Guardian Bot (HTTP)       |
| 8002 | FUN Bot (HTTP)            |
| 8080 | OSIF Shop (WebApp)        |

### 2.2 Railway Cloud (Production)

The production API and databases run on Railway with automatic deployment from GitHub.

| Resource   | Connection                                            |
|------------|-------------------------------------------------------|
| API        | `https://slh-api-production.up.railway.app`           |
| PostgreSQL | `junction.proxy.rlwy.net:17913/railway`               |
| Redis      | `junction.proxy.rlwy.net:12921`                       |

Railway auto-deploys from the `main` branch of the API repository.

### 2.3 GitHub Pages (Website)

| Property   | Value                    |
|------------|--------------------------|
| Domain     | `slh-nft.com`            |
| CNAME      | Configured               |
| Deployment | Push to `main` branch    |
| PWA        | `manifest.json` present  |

### 2.4 PostgreSQL Database Layout

Created via `init-db.sql` on first startup:

| Database        | Used By                                                          |
|-----------------|------------------------------------------------------------------|
| `slh_main`      | Core bot, Admin, ExpertNet, Airdrop, all template bots, API     |
| `slh_guardian`  | Guardian bot (isolated security data)                            |
| `slh_botshop`  | BotShop bot (product catalog, orders)                            |
| `slh_wallet`   | Wallet bot (wallet keys, transactions)                           |
| `slh_factory`  | Factory bot (investment positions)                               |
| `railway`       | Railway cloud production (API + website data)                    |

### 2.5 Redis Database Allocation

| DB Index | Used By               |
|----------|-----------------------|
| 0        | Core bot, NFTY bot    |
| 1        | Guardian bot          |
| 2        | Airdrop bot           |

### 2.6 Startup & Operations Scripts

| Script        | Purpose                                          |
|---------------|--------------------------------------------------|
| `start.ps1`   | Start services (params: all, core, infra, etc.)  |
| `stop.ps1`    | Stop all services                                |
| `build.ps1`   | Build all Docker images                          |
| `logs.ps1`    | View container logs                              |

---

## 3. Data Flow / זרימת נתונים

### 3.1 User Registration Flow

```
[User opens Telegram bot]
        |
        v
[/start command with optional ?start=ref_XXXXX deep link]
        |
        v
[Bot checks if user exists in DB]
        |
   +----+----+
   | New User |
   +----+----+
        |
        v
[Insert into users table (user_id, username, xp_total=0, balance=0, level=1)]
        |
        v
[If referral code present: register in referrals table (user_id, referrer_id, depth)]
        |
        v
[Send welcome message with bot menu]
```

### 3.2 Web Authentication Flow

```
[User visits slh-nft.com/dashboard.html]
        |
        v
[Telegram Login Widget renders]
        |
        v
[User clicks "Log in with Telegram"]
        |
        v
[Telegram OAuth -> returns id, first_name, username, photo_url, auth_date, hash]
        |
        v
[Frontend POSTs to /api/auth/telegram]
        |
        v
[Backend verifies HMAC-SHA256 signature using BOT_TOKEN]
        |
        v
[Upsert into web_users table]
        |
        v
[Return user profile + token balances + premium status]
        |
        v
[Frontend stores in localStorage as slh_user]
        |
        v
[User redirected to authenticated dashboard]
```

### 3.3 Token Economy Flow

```
                  +-------------------+
                  |  SLH Token (BSC)  |
                  |  BEP-20 Contract  |
                  +--------+----------+
                           |
              +------------+------------+
              |                         |
   +----------v----------+   +---------v---------+
   | On-Chain (BSC)      |   | Off-Chain Ledger  |
   | web3.py reads       |   | token_balances    |
   | Balance queries     |   | token_transfers   |
   | Contract events     |   | Internal P2P      |
   +---------------------+   +-------------------+
              |                         |
              v                         v
   +---------------------+   +-------------------+
   | TON Wallet           |   | Staking Engine    |
   | TON Center API       |   | 4 plans           |
   | Deposit verification |   | Auto-compound     |
   +---------------------+   +-------------------+
              |                         |
              +------------+------------+
                           |
                           v
                  +-------------------+
                  | Portfolio View    |
                  | Dashboard + API   |
                  +-------------------+
```

### 3.4 Wallet Connection Flow

#### BSC (MetaMask / Trust Wallet)

```
[User clicks "Connect BSC Wallet"]
        |
        v
[Check window.ethereum availability]
        |
   +----+----+
   |         |
   | Yes     | No
   |         +-> Open MetaMask download / Trust Wallet deep link
   v
[Request accounts: ethereum.request({method: 'eth_requestAccounts'})]
        |
        v
[Switch to BSC chain (chainId: 0x38) if not on BSC]
        |
        v
[Store wallet address in localStorage (slh_user.wallets.bsc)]
        |
        v
[POST to /api/user/{id}/wallets to sync backend]
        |
        v
[Dispatch 'wallet-changed' CustomEvent for UI updates]
```

#### TON (TonConnect)

```
[User clicks "Connect TON Wallet"]
        |
        v
[Initialize TonConnectUI with tonconnect-manifest.json]
        |
        v
[TonConnect modal opens -> User selects wallet (Tonkeeper, etc.)]
        |
        v
[Wallet connected -> address received]
        |
        v
[Store in localStorage + sync to backend]
```

### 3.5 Payment & Premium Access Flow

```
[User sends /premium command to any bot]
        |
        v
[Bot displays pricing (ILS + TON equivalent)]
        |
        v
[User sends TON to ecosystem wallet:
 UQCr743gEr_nqV_0SBkSp3CtYS_15R3LDLBvLmKeEv7XdGvp]
        |
        v
[User sends screenshot proof (photo) to bot]
        |
        v
[Bot forwards proof to admin (ADMIN_USER_ID: 224223270)]
        |
        v
[Admin approves (/approve) or rejects (/reject)]
        |
        v
[On approve: insert into premium_users (user_id, bot_name, status='approved')]
        |
        v
[User receives premium group invite link]
```

### 3.6 Referral Commission Distribution

```
[New user stakes TON or makes qualifying transaction]
        |
        v
[ReferralEngine.distribute_commissions() triggered]
        |
        v
[Walk referral tree up to 10 generations]
        |
        +-- Gen 1 (direct referrer):  10% commission
        +-- Gen 2:                     5% commission
        +-- Gen 3:                     3% commission
        +-- Gen 4:                     2% commission
        +-- Gen 5:                     1% commission
        +-- Gen 6-10:                  0.5% each
        |
        v
[Insert into referral_earnings table per generation]
        |
        v
[Credit earner's token_balances]
```

---

## 4. Security Architecture / ארכיטקטורת אבטחה

### 4.1 API Authentication

| Layer              | Mechanism                                              |
|--------------------|---------------------------------------------------------|
| Web Auth           | Telegram Login Widget (HMAC-SHA256 verification)       |
| Auth Expiry        | 24-hour window from `auth_date`                        |
| CORS               | Restricted to `slh-nft.com`, `localhost:8899`, `localhost:3000` |
| Rate Limiting      | In-memory rate limiter on community endpoints          |
| Admin Verification | `ADMIN_USER_ID` env var checked for privileged actions |

### 4.2 Telegram Auth Verification

The backend verifies Telegram Login Widget data using HMAC-SHA256:

1. Extract `hash` from auth data
2. Sort remaining fields alphabetically
3. Create `data_check_string` as `key=value\n` pairs
4. Compute `secret_key = SHA256(BOT_TOKEN)`
5. Compute `HMAC-SHA256(secret_key, data_check_string)`
6. Compare with provided `hash`
7. Verify `auth_date` is within 86400 seconds (24 hours)

### 4.3 Wallet Security

| Aspect               | Implementation                                  |
|------------------------|-------------------------------------------------|
| BSC Wallet Connect     | MetaMask/Trust Wallet browser injection         |
| TON Wallet Connect     | TonConnect protocol with manifest verification  |
| Admin BSC Wallet       | `0xD0617B54FB4b6b66307846f217b4D685800E3dA4`   |
| Admin TON Wallet       | `UQCr743gEr_nqV_0SBkSp3CtYS_15R3LDLBvLmKeEv7XdGvp` |
| Wallet Backup on Logout| Wallet addresses preserved in localStorage     |
| Backend Sync           | Wallet addresses synced to server-side DB       |

### 4.4 Admin Access Control

- Single admin user controlled by `ADMIN_USER_ID` (Telegram ID: 224223270)
- All bots route admin commands to this user ID
- Admin bot (`slh-admin`) serves as mission control
- Admin panel on website (`admin.html`) requires authenticated session
- Payment approvals require admin Telegram confirmation

### 4.5 Environment Variable Security

- All secrets stored in `.env` file (not committed to git)
- Docker Compose injects env vars into containers
- Railway environment variables configured via dashboard
- Bot tokens (25 total) are the primary authentication secrets
- Database credentials passed via `DATABASE_URL` connection strings

### 4.6 Known Security Concerns

- Token sharing: `SLH_SELHA_TOKEN` used by both selha-bot and userinfo-bot (polling conflict risk)
- `AIRDROP_BOT_TOKEN` may share with `EXPERTNET_BOT_TOKEN`
- All bots run in polling mode (no webhook TLS verification)
- No API key rotation policy in place
- Community rate limiter is in-memory (resets on restart)

---

## 5. Bot Ecosystem / מערכת הבוטים

### 5.1 Core Bots (Custom Codebases)

#### Bot 1: SLH Academia (`slh-core-bot`)
- **Purpose:** Main ecosystem bot -- store, tasks, XP system, token economy
- **Source:** `D:\SLH_PROJECT_V2\` (external repository)
- **Database:** `slh_main`
- **Framework:** aiogram 3.x
- **Features:** XP progression, level system, daily tasks, store purchases, referral deep links

#### Bot 2: Guardian (`slh-guardian-bot`)
- **Purpose:** Security monitoring, admin alerts, group protection
- **Source:** `D:\telegram-guardian-DOCKER-COMPOSE-ENTERPRISE\` (external)
- **Database:** `slh_guardian` (isolated)
- **Port:** 8001 (HTTP health endpoint)
- **Features:** Real-time monitoring, intrusion detection, admin notifications

#### Bot 3: GATE BotShop (`slh-botshop`)
- **Purpose:** Product store, AI-powered shop experience
- **Source:** `D:\SLH_ECOSYSTEM\botshop\`
- **Database:** `slh_botshop`
- **Features:** Product catalog, cart, payment integration, admin dashboard

#### Bot 4: SLH Wallet (`slh-wallet`)
- **Purpose:** Multi-chain wallet management (TON + BNB/BSC)
- **Source:** `D:\SLH_ECOSYSTEM\wallet\`
- **Database:** `slh_wallet`
- **Features:** Balance queries, deposit verification, transfer initiation, portfolio view

#### Bot 5: BOT Factory (`slh-factory`)
- **Purpose:** Investment and staking interface
- **Source:** `D:\SLH_ECOSYSTEM\factory\`
- **Database:** `slh_factory`
- **Features:** Staking plans, investment tracking, yield calculations

#### Bot 6: FUN Bot (`slh-fun`)
- **Purpose:** Promotional content, premium community management
- **Source:** `D:\SLH_ECOSYSTEM\fun\`
- **Database:** Stateless (no database dependency)
- **Port:** 8002
- **Features:** Promo campaigns, premium group management, community engagement

#### Bot 7: Super Admin (`slh-admin`)
- **Purpose:** Mission control for the entire ecosystem
- **Source:** `D:\SLH_ECOSYSTEM\` (root context, `Dockerfile.admin`)
- **Database:** `slh_main`
- **Features:** Cross-bot monitoring, user management, system commands

#### Bot 8: ExpertNet/AIR (`slh-expertnet`)
- **Purpose:** Zvika Kaufman's ambassador bot with arcade and ZVIKUSH tokens
- **Source:** `D:\SLH_ECOSYSTEM\expertnet-bot\`
- **Database:** `slh_main`
- **Features:** Arcade games, ZVIKUSH token economy, staking vaults, premium tiers

#### Bot 9: SLH HUB/Airdrop (`slh-airdrop`)
- **Purpose:** Central economic engine -- airdrop distribution, token swaps
- **Source:** `D:\SLH_ECOSYSTEM\airdrop\`
- **Database:** `slh_main` + Redis (DB 2)
- **Features:** Airdrop campaigns, LetsExchange integration, BSC/TON operations, Railway DB sync

### 5.2 Special Bots

| Bot             | Container        | Dockerfile              | Key Feature                           |
|-----------------|------------------|--------------------------|---------------------------------------|
| Campaign        | `slh-campaign`   | `Dockerfile.campaign`    | Google Sheets integration, group routing |
| Game Bot        | `slh-game`       | `Dockerfile.match`       | Gaming/match mechanics                |
| TON MNH         | `slh-ton-mnh`    | `Dockerfile.tonmnh`      | TON mainnet operations                |
| OSIF Shop       | `slh-osif-shop`  | `Dockerfile.osifshop`    | WebApp-enabled shop (port 8080)       |
| Nifti           | `slh-nifti`      | `Dockerfile.wellness`    | NFT/wellness content publishing       |
| NFTY Madness    | `slh-nfty`       | `Dockerfile.nfty`        | NFT marketplace, CoinGecko price feeds|
| UserInfo        | `slh-userinfo`   | Built in context         | Enhanced @userinfobot with ecosystem links |

### 5.3 Template Bots (Shared Codebase)

All template bots use `shared/bot_template.py` via `Dockerfile.template`. They share identical logic configured entirely through environment variables:

**Shared Features:**
- `/start` with referral deep link parsing
- `/premium` with pricing display
- Payment proof (photo upload)
- Admin approve/reject workflow
- Automatic premium group invite on approval

| Bot          | BOT_KEY        | Price ILS | Price TON | Description                    |
|--------------|----------------|-----------|-----------|--------------------------------|
| SLH TON      | `slh_ton`      | 79        | 4.0       | TON wallet & transfers         |
| SLH Ledger   | `ledger`       | 49        | 2.5       | Finance & expense tracking     |
| Chance Pais  | `chance`        | 19        | 1.0       | Lottery & luck games           |
| SLH Selha    | `selha`         | 49        | 2.5       | Community & trading            |
| TS Set        | `ts_set`       | 29        | 1.5       | Configuration & automation     |
| CrazyPanel   | `crazy_panel`   | 49        | 2.5       | Advanced admin panel           |
| NFT Shop     | `nft_shop`      | 49        | 2.5       | NFT e-commerce                 |
| BeynoniBank  | `beynonibank`   | 39        | 2.0       | Banking & financial services   |
| TestBot      | `test_bot`      | 0         | 0         | Development & testing          |

### 5.4 Cross-Bot Communication

- **Shared Database:** Most bots connect to `slh_main`, enabling cross-bot data access
- **Redis Streams:** Core bot publishes to `slh:updates` stream (Redis DB 0)
- **Event Bus (WIP):** `shared/slh_bus/` directory exists for future inter-bot messaging
- **Shared Payment Gate:** `shared/slh_payments/` provides universal payment handling
- **Referral Engine:** Cross-bot referral tracking via `shared/slh_payments/referrals.py`

### 5.5 Token Integration Per Bot

| Bot              | Tokens Supported | Integration Type        |
|------------------|------------------|-------------------------|
| Core (Academia)  | SLH, XP          | Internal ledger + XP    |
| Wallet           | TON, BNB, SLH    | On-chain + ledger       |
| Factory          | TON, SLH         | Staking positions       |
| ExpertNet        | ZVIKUSH (ZVK)    | Internal ledger         |
| Airdrop/HUB      | SLH, TON, BNB   | Airdrop + swap          |
| NFTY Madness     | SLH              | CoinGecko price feeds   |
| Template Bots    | TON              | Premium payments only   |

---

## 6. Website Architecture / ארכיטקטורת האתר

### 6.1 Page Structure

The website is a static single-page application collection hosted on GitHub Pages at `slh-nft.com`.

| Page               | File                 | Auth Required | Purpose                           |
|--------------------|----------------------|---------------|-----------------------------------|
| Homepage           | `index.html`         | No            | Landing, hero, ecosystem overview |
| Trade              | `trade.html`         | No            | Trading interface, charts         |
| Earn               | `earn.html`          | No            | Earning opportunities overview    |
| Wallet             | `wallet.html`        | Yes           | Wallet balances, connect, send    |
| Bots               | `bots.html`          | No            | Bot catalog with pricing          |
| Referral           | `referral.html`      | Yes           | Referral tree, link generation    |
| Referral Card      | `referral-card.html` | No            | Shareable referral card           |
| Community          | `community.html`     | No            | Community feed, posts, likes      |
| Blockchain         | `blockchain.html`    | No            | Blockchain explorer / info        |
| Dashboard          | `dashboard.html`     | Yes           | User dashboard after login        |
| Staking            | `staking.html`       | No            | Staking plans, deposit/withdraw   |
| Analytics          | `analytics.html`     | No            | Analytics dashboard               |
| Admin              | `admin.html`         | Yes           | Admin panel                       |
| Guides             | `guides.html`        | No            | User guides and tutorials         |
| Whitepaper         | `whitepaper.html`    | No            | Project whitepaper                |

### 6.2 Navigation Architecture

**Top Navigation (Desktop):**
- Logo (SLH Spark) -> Home
- First 5 nav items visible
- Remaining items in "More" dropdown
- Language selector (5 flags)
- User avatar with profile dropdown (when logged in)
- Login button (when logged out)

**Bottom Navigation (Mobile):**
Home | Wallet | Earn | Bots | Referral

**Mobile Drawer:**
Full navigation list accessible via hamburger menu.

### 6.3 Shared JavaScript Modules

| Module              | File                  | Responsibilities                                    |
|---------------------|-----------------------|-----------------------------------------------------|
| **Shared Core**     | `js/shared.js`        | API client, auth, i18n, theme, nav, ticker, utils   |
| **Web3 Wallet**     | `js/web3-wallet.js`   | MetaMask/Trust Wallet (BSC), TonConnect (TON)       |
| **Translations**    | `js/translations.js`  | 5-language translation dictionary                   |
| **Analytics**       | `js/analytics.js`     | Client-side analytics tracking, heartbeat, events   |

### 6.4 Internationalization (i18n) System

**Supported Languages:**

| Code | Language | Direction |
|------|----------|-----------|
| `he` | Hebrew   | RTL       |
| `en` | English  | LTR       |
| `ru` | Russian  | LTR       |
| `ar` | Arabic   | RTL       |
| `fr` | French   | LTR       |

**Implementation:**
- Translation keys stored in `T` object in `translations.js`
- HTML elements use `data-i18n` attribute for text, `data-i18n-html` for HTML content
- `setLang()` updates `dir` and `lang` attributes on `<html>`
- RTL languages (`he`, `ar`) automatically set `dir="rtl"`
- Language preference persisted in `localStorage` as `slh_lang`
- Default language: Hebrew (`he`)

### 6.5 Theme System

| Theme      | Description                |
|------------|----------------------------|
| `dark`     | Default dark theme          |
| `terminal` | Hacker/terminal green style |
| `crypto`   | Crypto-inspired palette     |
| `light`    | Light mode                  |

**Features:**
- Theme stored in `localStorage` as `slh_theme`
- Applied via `data-theme` attribute on `<html>`
- Auto-cycle mode: rotates themes every 8 seconds
- Theme buttons with active state indicators

### 6.6 Real-Time Data Sources

| Source              | URL                                                | Data                               | Refresh    |
|---------------------|----------------------------------------------------|-------------------------------------|------------|
| CoinGecko           | `api.coingecko.com/api/v3/simple/price`            | BTC, ETH, TON, BNB prices (USD+ILS)| 60 seconds |
| SLH API             | `slh-api-production.up.railway.app/api/prices`     | Cached proxy for 7 coins            | 60 seconds |
| SLH API             | `slh-api-production.up.railway.app/api/stats`      | Ecosystem statistics                | On demand  |

**Ticker Bar:**
A scrolling marquee showing live prices for SLH, BTC, ETH, TON, and BNB with 24h percentage change. Updates every 60 seconds via CoinGecko API.

### 6.7 Client-Side Analytics

The analytics module (`analytics.js`) tracks:
- Page views with visitor ID (generated, stored in localStorage)
- Session duration via 30-second heartbeat
- Scroll depth (25%, 50%, 75%, 100% marks)
- Click tracking
- Device/language/referrer statistics
- Events queued locally, flushed to `/api/analytics/event`

### 6.8 PWA Support

- `manifest.json` configured with app name, icons (192px, 512px), theme colors
- Apple touch icon configured
- Favicons (32px, standard)

---

## 7. API Endpoints / נקודות קצה

**Base URL:** `https://slh-api-production.up.railway.app`
**Source:** `D:\SLH_ECOSYSTEM\api\main.py` + `D:\SLH_ECOSYSTEM\shared\wallet_api.py` + `D:\SLH_ECOSYSTEM\shared\community_api.py`

### 7.1 Authentication

| Method | Endpoint               | Description                                  |
|--------|------------------------|----------------------------------------------|
| POST   | `/api/auth/telegram`   | Verify Telegram Login Widget HMAC + upsert user |

### 7.2 User Management

| Method | Endpoint                       | Description                              |
|--------|--------------------------------|------------------------------------------|
| GET    | `/api/user/{telegram_id}`      | Full user profile, balances, staking, deposits |
| POST   | `/api/user/{id}/wallets`       | Sync wallet address (chain + address)    |

### 7.3 Staking

| Method | Endpoint                            | Description                        |
|--------|-------------------------------------|------------------------------------|
| GET    | `/api/staking/plans`                | List 4 staking plans with APY      |
| POST   | `/api/staking/stake`                | Create new staking position        |
| GET    | `/api/staking/positions/{user_id}`  | Get user's active staking positions|

### 7.4 Token Operations

| Method | Endpoint            | Description                                   |
|--------|---------------------|-----------------------------------------------|
| POST   | `/api/transfer`     | Internal token transfer (SLH, ZVK) between users |

### 7.5 Referral System (10 Generations)

| Method | Endpoint                          | Description                      |
|--------|-----------------------------------|----------------------------------|
| POST   | `/api/referral/register`          | Register user with referral code |
| GET    | `/api/referral/tree/{user_id}`    | Get full referral tree           |
| GET    | `/api/referral/link/{user_id}`    | Generate shareable referral link |
| GET    | `/api/referral/leaderboard`       | Top referrers ranking            |
| GET    | `/api/referral/stats/{user_id}`   | Detailed referral statistics     |

### 7.6 Prices & Market Data

| Method | Endpoint         | Description                                               |
|--------|------------------|-----------------------------------------------------------|
| GET    | `/api/prices`    | CoinGecko proxy: BTC, ETH, TON, BNB, SOL, XRP, DOGE (60s cache) |

### 7.7 Statistics & Leaderboard

| Method | Endpoint            | Description                                |
|--------|---------------------|--------------------------------------------|
| GET    | `/api/stats`        | Ecosystem stats (users, premium, staked)   |
| GET    | `/api/leaderboard`  | Global user leaderboard                    |

### 7.8 Activity & Transactions

| Method | Endpoint                      | Description                    |
|--------|-------------------------------|--------------------------------|
| GET    | `/api/activity/{user_id}`     | User activity feed             |
| GET    | `/api/transactions/{user_id}` | User transaction history       |

### 7.9 Community

| Method | Endpoint                                  | Description              |
|--------|-------------------------------------------|--------------------------|
| GET    | `/api/community/posts`                    | Get community post feed  |
| POST   | `/api/community/posts`                    | Create a new post        |
| POST   | `/api/community/posts/{post_id}/like`     | Like a post              |
| POST   | `/api/community/posts/{post_id}/comments` | Comment on a post        |
| GET    | `/api/community/stats`                    | Community statistics     |
| GET    | `/api/community/health`                   | Community API health     |

### 7.10 Analytics

| Method | Endpoint                  | Description              |
|--------|---------------------------|--------------------------|
| POST   | `/api/analytics/event`    | Track analytics event    |
| GET    | `/api/analytics/stats`    | Get analytics data       |

### 7.11 Wallet Engine (via shared/wallet_api.py)

| Method | Endpoint                              | Description                          |
|--------|---------------------------------------|--------------------------------------|
| GET    | `/api/wallet/balance/{chain}/{addr}`  | On-chain balance query (BSC/TON)     |
| POST   | `/api/wallet/transfer`                | Initiate internal ledger transfer    |
| GET    | `/api/wallet/portfolio/{user_id}`     | Full portfolio (on-chain + ledger)   |
| POST   | `/api/wallet/verify-deposit`          | Verify on-chain deposit transaction  |

### 7.12 Health

| Method | Endpoint       | Description                    |
|--------|----------------|--------------------------------|
| GET    | `/api/health`  | Health check + DB connectivity |

---

## 8. Database Schema / סכימת בסיס נתונים

### 8.1 Railway Production Database (slh_main)

#### `web_users` -- Website authenticated users
```sql
telegram_id   BIGINT PRIMARY KEY
username      TEXT
first_name    TEXT
photo_url     TEXT
auth_date     BIGINT
last_login    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
```

#### `users` -- Bot users (XP/economy)
```sql
user_id       BIGINT PRIMARY KEY
username      TEXT
xp_total      NUMERIC(18,2) DEFAULT 0
balance       NUMERIC(18,8) DEFAULT 0
level         INT DEFAULT 1
created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
```

#### `token_balances` -- Multi-token ledger
```sql
id            BIGSERIAL PRIMARY KEY
user_id       BIGINT NOT NULL
token         TEXT NOT NULL DEFAULT 'SLH'
balance       NUMERIC(18,8) NOT NULL DEFAULT 0
updated_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
UNIQUE(user_id, token)
```

#### `token_transfers` -- Transfer history
```sql
id            BIGSERIAL PRIMARY KEY
from_user_id  BIGINT
to_user_id    BIGINT
token         TEXT NOT NULL DEFAULT 'SLH'
amount        NUMERIC(18,8) NOT NULL
memo          TEXT
tx_type       TEXT DEFAULT 'transfer'
created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
```

#### `staking_positions` -- Active staking positions
```sql
id            BIGSERIAL PRIMARY KEY
user_id       BIGINT NOT NULL (FK -> web_users.telegram_id)
plan          TEXT NOT NULL
amount        NUMERIC(18,8) NOT NULL
currency      TEXT DEFAULT 'TON'
apy_monthly   NUMERIC(5,2) NOT NULL
lock_days     INT NOT NULL
start_date    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
end_date      TIMESTAMP NOT NULL
status        TEXT DEFAULT 'active'
earned        NUMERIC(18,8) DEFAULT 0
```

#### `referrals` -- Referral relationships
```sql
id            BIGSERIAL PRIMARY KEY
user_id       BIGINT NOT NULL UNIQUE (FK -> web_users.telegram_id)
referrer_id   BIGINT
depth         INT DEFAULT 1
created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
INDEX idx_referrals_referrer (referrer_id)
```

#### `referral_earnings` -- Commission payouts
```sql
id                BIGSERIAL PRIMARY KEY
earner_id         BIGINT NOT NULL
from_user_id      BIGINT NOT NULL
generation        INT NOT NULL
source_type       TEXT NOT NULL
source_amount     NUMERIC(18,8) NOT NULL
commission_rate   NUMERIC(5,4) NOT NULL
commission_amount NUMERIC(18,8) NOT NULL
token             TEXT DEFAULT 'TON'
created_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP
INDEX idx_referral_earnings_earner (earner_id)
```

#### `deposits` -- Deposit records
```sql
id            BIGSERIAL PRIMARY KEY
user_id       BIGINT NOT NULL
amount        NUMERIC(18,8) NOT NULL
currency      TEXT DEFAULT 'SLH'
tx_hash       TEXT
status        TEXT DEFAULT 'pending'
plan_key      TEXT
created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
```

#### `premium_users` -- Premium access tracking
```sql
id              BIGSERIAL PRIMARY KEY
user_id         BIGINT NOT NULL
bot_name        TEXT NOT NULL
payment_status  TEXT DEFAULT 'pending'
created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
UNIQUE(user_id, bot_name)
```

#### `daily_claims` -- Daily reward claims
```sql
id            BIGSERIAL PRIMARY KEY
user_id       BIGINT NOT NULL
amount        NUMERIC(18,8) NOT NULL DEFAULT 0
streak        INT NOT NULL DEFAULT 1
claimed_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
```

### 8.2 Entity Relationship Overview

```
web_users (telegram_id)
    |
    +-- 1:N --> staking_positions (user_id)
    +-- 1:1 --> referrals (user_id)
    +-- 1:N --> token_balances (user_id, token) UNIQUE
    +-- 1:N --> deposits (user_id)
    +-- 1:N --> premium_users (user_id, bot_name) UNIQUE
    +-- 1:N --> daily_claims (user_id)

referrals (referrer_id) --> web_users (telegram_id)

referral_earnings (earner_id) --> implicit user reference
token_transfers (from_user_id, to_user_id) --> implicit user references
```

### 8.3 Isolated Bot Databases

| Database       | Tables (bot-specific, not centrally documented) |
|----------------|-------------------------------------------------|
| `slh_guardian` | Security events, monitoring logs, alert rules   |
| `slh_botshop`  | Products, orders, cart items, categories        |
| `slh_wallet`   | Wallet addresses, key material, tx history      |
| `slh_factory`  | Investment positions, yield records              |

---

## 9. Revenue Model / מודל הכנסות

### 9.1 Premium Bot Access

Each bot offers premium access via TON payment:

| Tier          | Price Range (ILS) | Price Range (TON) | Included                           |
|---------------|-------------------|--------------------|-------------------------------------|
| Basic Bots    | 19-29             | 1.0-1.5            | Single bot premium features         |
| Standard Bots | 39-49             | 2.0-2.5            | Full bot access + premium group     |
| Advanced Bots | 79-99             | 4.0-5.0            | Wallet, BotShop advanced features   |
| Pro Bots      | 149               | 7.5                | Factory investment tools            |

**Payment Flow:** User sends TON -> screenshot proof -> admin approval -> premium group invite.

### 9.2 SLH Token Economy

| Property           | Value                                          |
|--------------------|------------------------------------------------|
| Token              | SLH (BEP-20 on BSC)                           |
| Contract           | `0xACb0A09414CEA1C879c67bB7A877E4e19480f022`  |
| Fixed Price        | 444 ILS per SLH                                |
| Decimals           | 15                                             |
| Use Cases          | Premium access, staking, P2P transfers, rewards|

### 9.3 Staking Revenue

Users stake TON in the ecosystem, generating yield:

| Plan         | Monthly APY | Annual APY | Minimum | Lock Period |
|--------------|-------------|------------|---------|-------------|
| Monthly      | 4.0%        | 48%        | 1 TON   | 30 days     |
| Quarterly    | 4.5%        | 55%        | 5 TON   | 90 days     |
| Semi-Annual  | 5.0%        | 60%        | 10 TON  | 180 days    |
| Annual       | 5.4%        | 65%        | 25 TON  | 365 days    |

### 9.4 Referral System (10-Generation MLM)

Revenue from referral commissions on qualifying transactions:

| Generation | Commission Rate | Description       |
|------------|-----------------|-------------------|
| 1          | 10%             | Direct referral   |
| 2          | 5%              | Second level      |
| 3          | 3%              | Third level       |
| 4          | 2%              | Fourth level      |
| 5          | 1%              | Fifth level       |
| 6-10       | 0.5% each       | Deep network      |

**Total maximum distribution per transaction:** ~24.5% across 10 levels.

### 9.5 Additional Revenue Streams

| Stream              | Status       | Description                                           |
|---------------------|-------------|-------------------------------------------------------|
| Token Sales (SLH)   | Active      | Direct SLH token purchases at 444 ILS                |
| Premium Groups       | Active      | Paid Telegram group access per bot                   |
| LetsExchange Referral| Active      | Affiliate revenue from crypto swaps                  |
| Airdrop Campaigns    | Active      | Token distribution for engagement                    |
| Daily Claims         | Active      | Streak-based rewards driving retention               |
| NFT Sales            | Planned     | Via NFTY Madness bot                                 |
| Bot Factory SaaS     | Planned     | Users create and monetize their own bots             |
| Ambassador Program   | Active      | ExpertNet (Zvika) as first franchise                 |

### 9.6 ExpertNet Franchise Model (Ambassador #1)

Zvika Kaufman's ExpertNet bot operates as the first ambassador franchise:
- Custom token: ZVIKUSH (ZVK)
- Arcade games with token rewards
- Independent staking vaults
- Premium tiers specific to ExpertNet community
- Revenue shared with ecosystem via commission structure

---

## 10. Future Roadmap / תוכנית עתידית

### Phase 2: Stabilize & Connect (In Progress)

- [ ] Fix duplicate bot token assignments (AIRDROP/EXPERTNET, SELHA/USERINFO)
- [ ] Renew Academia bot token via BotFather
- [ ] Set up GitHub repositories for all bots
- [ ] Implement health monitoring dashboard
- [ ] Cross-bot SSO (unified user database across all bots)
- [ ] Unified admin panel (one bot to manage all)

### Phase 3: Production Deployment

- [ ] Cloudflare Tunnel for webhook mode (replace polling)
- [ ] Nginx reverse proxy for all services
- [ ] SSL certificates for local endpoints
- [ ] Centralized log aggregation
- [ ] Automated PostgreSQL backup strategy (scheduled pg_dump)
- [ ] Docker health monitoring and auto-recovery

### Phase 4: Cross-Bot Economy

- [ ] Shared SLH token balance across all bots (unified ledger)
- [ ] Wallet bot as central treasury
- [ ] Cross-bot referral system (single referral tree)
- [ ] Unified leaderboard across ecosystem
- [ ] P2P trading between users
- [ ] BSC <-> TON bridge integration
- [ ] `slh_bus/` event bus implementation for real-time inter-bot messaging

### Phase 5: AI Integration

- [ ] AI-powered investment recommendations
- [ ] Natural language bot interactions (LLM integration)
- [ ] Automated market analysis and alerts
- [ ] AI-driven customer support across bots
- [ ] Smart portfolio rebalancing suggestions

### Phase 6: Investment Intelligence

- [ ] Real-time market data dashboards
- [ ] Technical analysis indicators
- [ ] Portfolio performance tracking
- [ ] Risk assessment tools
- [ ] Automated trading signals (Binance integration exists in env vars)

### Phase 7: Community & Social Features

- [ ] Enhanced community feed with media uploads
- [ ] User-to-user messaging within ecosystem
- [ ] Community governance (voting on proposals)
- [ ] Achievement system with NFT badges
- [ ] Social trading (copy trading)

### Phase 8: Ambassador SaaS Model

- [ ] Bot-per-ambassador framework (following ExpertNet model)
- [ ] Self-service ambassador onboarding portal
- [ ] Custom token creation per ambassador
- [ ] Revenue sharing dashboard
- [ ] Educational content platform for ambassadors
- [ ] Family/team management within ambassador networks

### Phase 9: Mobile & Scale

- [ ] React Native app (`D:\SLH_APP`) connected to all bots
- [ ] Push notifications for price alerts and portfolio updates
- [ ] Offline mode with local data sync
- [ ] Multi-region deployment (currently single-region)
- [ ] Bot Factory: let users create, deploy, and monetize their own bots

---

## Appendix A: Directory Structure

```
D:\SLH_ECOSYSTEM\
  +-- docker-compose.yml        # All 25 service definitions
  +-- .env                      # Environment variables (25+ tokens, DB creds)
  +-- init-db.sql               # Database initialization (5 databases)
  +-- start.ps1 / stop.ps1     # PowerShell launchers
  +-- build.ps1 / logs.ps1     # Build and log scripts
  +-- PROJECT_MAP.md            # Detailed project map
  +-- ROADMAP.md                # Development roadmap
  +-- STATUS_REPORT.md          # Current status
  +--
  +-- dockerfiles/              # 16+ Dockerfiles
  |     +-- Dockerfile.core
  |     +-- Dockerfile.guardian
  |     +-- Dockerfile.botshop
  |     +-- Dockerfile.wallet
  |     +-- Dockerfile.factory
  |     +-- Dockerfile.fun
  |     +-- Dockerfile.admin
  |     +-- Dockerfile.expertnet
  |     +-- Dockerfile.airdrop
  |     +-- Dockerfile.campaign
  |     +-- Dockerfile.match
  |     +-- Dockerfile.tonmnh
  |     +-- Dockerfile.osifshop
  |     +-- Dockerfile.wellness
  |     +-- Dockerfile.nfty
  |     +-- Dockerfile.template   # Shared template for 9 bots
  |
  +-- shared/                   # Shared Python libraries
  |     +-- bot_template.py     # Template bot logic
  |     +-- wallet_engine.py    # BSC/TON wallet engine
  |     +-- wallet_api.py       # FastAPI wallet router
  |     +-- community_api.py    # Community feed API
  |     +-- slh_token_abi.json  # BEP-20 ABI
  |     +-- group_config.json   # Telegram group mappings
  |     +-- slh_payments/       # Payment processing module
  |     |     +-- config.py     # Bot pricing configs
  |     |     +-- db.py         # Payment DB helpers
  |     |     +-- payment_gate.py # Universal payment handler
  |     |     +-- ledger.py     # Internal token ledger
  |     |     +-- referrals.py  # Referral engine (10 gen)
  |     |     +-- promotions.py # Promo & deals engine
  |     +-- slh_bus/            # Event bus (WIP)
  |
  +-- api/                      # Railway FastAPI backend
  |     +-- main.py             # 30+ endpoints
  |     +-- requirements.txt
  |     +-- Dockerfile
  |     +-- railway.json
  |
  +-- website/                  # GitHub Pages (slh-nft.com)
  |     +-- index.html          # Landing page
  |     +-- dashboard.html      # User dashboard
  |     +-- staking.html        # Staking interface
  |     +-- wallet.html         # Wallet management
  |     +-- community.html      # Community feed
  |     +-- ... (15 pages total)
  |     +-- css/shared.css      # Global styles
  |     +-- js/shared.js        # Core module
  |     +-- js/web3-wallet.js   # Blockchain wallet
  |     +-- js/translations.js  # i18n (5 languages)
  |     +-- js/analytics.js     # Analytics tracker
  |     +-- manifest.json       # PWA manifest
  |     +-- CNAME               # Custom domain
  |
  +-- airdrop/                  # Airdrop/HUB bot
  +-- expertnet-bot/            # ExpertNet (Zvika)
  +-- botshop/                  # BotShop bot
  +-- wallet/                   # Wallet bot
  +-- factory/                  # Factory bot
  +-- fun/                      # FUN bot
  +-- nfty-bot/                 # NFTY Madness
  +-- tonmnh-bot/               # TON MNH
  +-- userinfo-bot/             # UserInfo bot
  +-- osif-shop/                # OSIF Shop
  +-- campaign-bot/             # Campaign assets
  +-- guardian/                 # Guardian local files
  +-- core/                     # Core local files
  +-- admin-bot/                # Admin bot files
  +-- match-bot/                # Game/Match bot
  +-- backups/                  # Database backups
  +-- ops/                      # Operations scripts
```

## Appendix B: Key Constants

| Constant              | Value                                              |
|-----------------------|----------------------------------------------------|
| SLH BSC Contract      | `0xACb0A09414CEA1C879c67bB7A877E4e19480f022`      |
| SLH Decimals          | 15                                                 |
| SLH Price             | 444 ILS                                            |
| Admin BSC Wallet      | `0xD0617B54FB4b6b66307846f217b4D685800E3dA4`      |
| Admin TON Wallet      | `UQCr743gEr_nqV_0SBkSp3CtYS_15R3LDLBvLmKeEv7XdGvp` |
| BSC Chain ID          | 56 (0x38)                                          |
| BSC RPC               | `https://bsc-dataseed.binance.org/`                |
| TON API               | `https://toncenter.com/api/v2`                     |
| API Base URL          | `https://slh-api-production.up.railway.app`        |
| CoinGecko API         | `https://api.coingecko.com/api/v3`                 |
| Admin Telegram ID     | 224223270                                          |
| Default Language      | Hebrew (`he`)                                      |
| Default Theme         | `dark`                                             |

## Appendix C: External Dependencies

| Dependency         | Source Path                                           |
|--------------------|-------------------------------------------------------|
| Core Bot (Academia)| `D:\SLH_PROJECT_V2\`                                 |
| Guardian Bot       | `D:\telegram-guardian-DOCKER-COMPOSE-ENTERPRISE\`     |
| Mobile App (future)| `D:\SLH_APP\`                                        |

---

> **Document generated:** 2026-04-08
> **Source of truth:** `D:\SLH_ECOSYSTEM\` codebase analysis
> **For updates:** Modify this file at `D:\SLH_ECOSYSTEM\website\docs\ARCHITECTURE.md`
