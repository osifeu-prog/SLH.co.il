# SLH ECOSYSTEM - Project Map / מפת פרויקט

> **Last Updated:** 2026-04-07
> **Maintainer:** SPARK IND
> **Path:** `D:\SLH_ECOSYSTEM\`

---

## Table of Contents
1. [Architecture Overview](#architecture-overview)
2. [Infrastructure](#infrastructure)
3. [Telegram Bots](#telegram-bots)
4. [Website (slh-nft.com)](#website-slh-nftcom)
5. [Shared Libraries](#shared-libraries)
6. [API Endpoints](#api-endpoints)
7. [Token Economics](#token-economics)
8. [Environment Variables](#environment-variables)
9. [Development Setup](#development-setup)
10. [Current Status & Known Issues](#current-status--known-issues)

---

## Architecture Overview

### System Diagram / דיאגרמת מערכת

```
                              +---------------------+
                              |   slh-nft.com       |
                              |  (GitHub Pages)     |
                              |  14 HTML pages      |
                              +--------+------------+
                                       |
                                       | HTTPS
                                       v
                      +-----------------------------------+
                      |  Railway API (FastAPI)             |
                      |  slh-api-production.up.railway.app |
                      |  api/main.py - 25+ endpoints       |
                      +--------+-----------+--------------+
                               |           |
                  +------------+     +-----+-------+
                  |                   |             |
                  v                   v             v
         +----------------+   +-----------+   +-----------+
         | Railway PG     |   | Local PG  |   | Railway   |
         | (Production)   |   | :5432     |   | Redis     |
         +----------------+   +-----+-----+   +-----------+
                                    |
                  +-----------------+------------------+
                  |                 |                   |
                  v                 v                   v
          +-------------+   +-------------+   +--------------+
          | slh_main    |   | slh_guardian |   | slh_botshop  |
          | slh_wallet  |   | slh_factory |   |              |
          +-------------+   +-------------+   +--------------+
                  |
    +-------------+-------------+-------------+
    |             |             |              |
    v             v             v              v
 +--------+  +--------+  +---------+  +-----------+
 |Core Bot|  |Guardian|  |BotShop  |  |Wallet Bot |
 |Academia|  |Security|  |Store    |  |TON/BNB    |
 +--------+  +--------+  +---------+  +-----------+
    |             |             |              |
    v             v             v              v
 +--------+  +--------+  +---------+  +-----------+
 |Factory |  |FUN Bot |  |Admin Bot|  |ExpertNet  |
 |Staking |  |Promo   |  |Mission  |  |Zvika/AIR  |
 +--------+  +--------+  |Control  |  +-----------+
                          +---------+
    |             |             |              |
    v             v             v              v
 +--------+  +--------+  +---------+  +-----------+
 |Airdrop |  |Campaign|  |Game Bot |  |NFTY Bot   |
 |HUB     |  |Sheets  |  |Match    |  |Madness    |
 +--------+  +--------+  +---------+  +-----------+
    |             |             |              |
    +-- 10+ more Template Bots (Dockerfile.template) --+
```

### Tech Stack

| Layer         | Technology                                   |
|---------------|----------------------------------------------|
| Language      | Python 3.11+                                 |
| Bot Framework | aiogram 3.x (some bots use python-telegram-bot) |
| Web API       | FastAPI + asyncpg + aiohttp                  |
| Database      | PostgreSQL 15 (local Docker + Railway cloud)  |
| Cache         | Redis 7 (local Docker + Railway cloud)        |
| Blockchain    | web3.py (BSC), TON Center API (TON)           |
| Website       | Static HTML/CSS/JS (GitHub Pages)             |
| Containers    | Docker Compose (all services)                 |
| Hosting API   | Railway (production FastAPI)                  |
| Hosting Site  | GitHub Pages (slh-nft.com)                   |
| OS            | Windows 10 Pro (Docker Desktop)               |

---

## Infrastructure

### Docker Services / שירותי Docker

All services defined in `docker-compose.yml`. Start with `docker compose up -d`.

#### Shared Infrastructure

| Container        | Image             | Port  | Purpose                    |
|------------------|--------------------|-------|----------------------------|
| `slh-postgres`   | postgres:15-alpine | 5432  | Main PostgreSQL database   |
| `slh-redis`      | redis:7-alpine     | 6379  | Caching, sessions, streams |

#### PostgreSQL Databases (Local)

Created via `init-db.sql`:

| Database       | Used By                                      |
|----------------|----------------------------------------------|
| `slh_main`     | Core bot, Admin, ExpertNet, Airdrop, all template bots |
| `slh_guardian`  | Guardian bot                                 |
| `slh_botshop`   | BotShop bot                                  |
| `slh_wallet`    | Wallet bot                                   |
| `slh_factory`   | Factory bot                                  |

#### Railway (Cloud Production)

| Resource       | URL / Connection String                                                   |
|----------------|---------------------------------------------------------------------------|
| API            | `https://slh-api-production.up.railway.app`                               |
| PostgreSQL     | `junction.proxy.rlwy.net:17913/railway`                                   |
| Redis          | `junction.proxy.rlwy.net:12921`                                           |

#### Redis DB Allocation

| DB Index | Used By         |
|----------|-----------------|
| 0        | Core bot, NFTY  |
| 1        | Guardian bot    |
| 2        | Airdrop bot     |

#### GitHub Pages

| Resource  | URL                       |
|-----------|---------------------------|
| Website   | `https://slh-nft.com`     |
| CNAME     | `slh-nft.com`             |

---

## Telegram Bots

### Core Bots / בוטים מרכזיים

These bots have dedicated codebases and custom logic.

| # | Bot Name         | Container          | Token Env Var          | Dockerfile              | Database       | Ports | Purpose                           |
|---|------------------|--------------------|------------------------|--------------------------|----------------|-------|-----------------------------------|
| 1 | SLH Academia     | `slh-core-bot`     | `CORE_BOT_TOKEN`       | `Dockerfile.core`        | `slh_main`     | -     | Main bot: store, tasks, XP, economy |
| 2 | Guardian         | `slh-guardian-bot`  | `GUARDIAN_BOT_TOKEN`   | `Dockerfile.guardian`    | `slh_guardian`  | 8001  | Security, monitoring, admin alerts |
| 3 | GATE BotShop     | `slh-botshop`      | `BOTSHOP_BOT_TOKEN`    | `Dockerfile.botshop`     | `slh_botshop`   | -     | Product store, AI shop             |
| 4 | SLH Wallet       | `slh-wallet`       | `WALLET_BOT_TOKEN`     | `Dockerfile.wallet`      | `slh_wallet`    | -     | TON/BNB wallet management          |
| 5 | BOT Factory      | `slh-factory`      | `FACTORY_BOT_TOKEN`    | `Dockerfile.factory`     | `slh_factory`   | -     | Investment & staking               |
| 6 | FUN Bot          | `slh-fun`          | `FUN_BOT_TOKEN`        | `Dockerfile.fun`         | - (stateless)  | 8002  | Promo, premium community           |
| 7 | Super Admin      | `slh-admin`        | `ADMIN_BOT_TOKEN`      | `Dockerfile.admin`       | `slh_main`     | -     | Mission control, admin panel       |
| 8 | ExpertNet/AIR    | `slh-expertnet`    | `EXPERTNET_BOT_TOKEN`  | `Dockerfile.expertnet`   | `slh_main`     | -     | Zvika Kaufman ambassador bot, arcade, ZVIKUSH tokens |
| 9 | SLH HUB/Airdrop  | `slh-airdrop`     | `AIRDROP_BOT_TOKEN`    | `Dockerfile.airdrop`     | `slh_main`     | -     | Central economic engine, airdrop, swap |

#### Dedicated Bot Directories

| Bot         | Source Code Path                                   |
|-------------|-----------------------------------------------------|
| Core        | `D:\SLH_PROJECT_V2\` (external)                     |
| Guardian    | `D:\telegram-guardian-DOCKER-COMPOSE-ENTERPRISE\` (external) |
| BotShop     | `D:\SLH_ECOSYSTEM\botshop\`                         |
| Wallet      | `D:\SLH_ECOSYSTEM\wallet\`                          |
| Factory     | `D:\SLH_ECOSYSTEM\factory\`                         |
| FUN         | `D:\SLH_ECOSYSTEM\fun\`                             |
| ExpertNet   | `D:\SLH_ECOSYSTEM\expertnet-bot\`                   |
| Airdrop     | `D:\SLH_ECOSYSTEM\airdrop\`                         |
| NFTY        | `D:\SLH_ECOSYSTEM\nfty-bot\`                        |
| Campaign    | Built from `D:\SLH_ECOSYSTEM\` root context         |
| TON MNH     | `D:\SLH_ECOSYSTEM\tonmnh-bot\`                      |
| UserInfo    | `D:\SLH_ECOSYSTEM\userinfo-bot\`                    |
| OSIF Shop   | `D:\SLH_ECOSYSTEM\osif-shop\` (webapp)              |

### Template Bots / בוטים מתבנית

These bots use `shared/bot_template.py` via `Dockerfile.template`. They share identical logic: `/start`, `/premium`, payment proof, admin approve/reject. Configured via environment variables.

| # | Bot Name      | Container          | Token Env Var        | BOT_KEY       | Price (ILS) | Price (TON) | Description              |
|---|---------------|--------------------|----------------------|---------------|-------------|-------------|--------------------------|
| 1 | SLH TON       | `slh-ton`          | `SLH_TON_TOKEN`     | `slh_ton`     | 79          | 4.0         | TON wallet & transfers   |
| 2 | SLH Ledger    | `slh-ledger`       | `SLH_LEDGER_TOKEN`  | `ledger`      | 49          | 2.5         | Finance & expense tracking |
| 3 | Chance Pais   | `slh-chance`       | `CHANCE_PAIS_TOKEN`  | `chance`      | 19          | 1.0         | Lottery & luck games     |
| 4 | SLH Selha     | `slh-selha`        | `SLH_SELHA_TOKEN`   | `selha`       | 49          | 2.5         | Community & trading      |
| 5 | TS Set        | `slh-ts-set`       | `TS_SET_TOKEN`       | `ts_set`      | 29          | 1.5         | Configuration & automation |
| 6 | CrazyPanel    | `slh-crazy-panel`  | `CRAZY_PANEL_TOKEN`  | `crazy_panel` | 49          | 2.5         | Advanced admin panel     |
| 7 | NFT Shop      | `slh-nft-shop`     | `MY_NFT_SHOP_TOKEN`  | `nft_shop`    | 49          | 2.5         | NFT e-commerce           |
| 8 | BeynoniBank   | `slh-beynonibank`  | `BEYNONIBANK_TOKEN`  | `beynonibank` | 39          | 2.0         | Banking & financial services |
| 9 | TestBot       | `slh-test-bot`     | `TEST_BOT_TOKEN`     | `test_bot`    | 0           | 0           | Development & testing    |

### Special Bots / בוטים מיוחדים

| # | Bot Name      | Container          | Token Env Var           | Dockerfile            | Notes                          |
|---|---------------|--------------------|--------------------------|------------------------|---------------------------------|
| 1 | Campaign      | `slh-campaign`     | `CAMPAIGN_TOKEN`         | `Dockerfile.campaign`  | Google Sheets integration, group routing |
| 2 | Game Bot      | `slh-game`         | `GAME_BOT_TOKEN`         | `Dockerfile.match`     | Gaming / match                 |
| 3 | TON MNH       | `slh-ton-mnh`     | `TON_MNH_TOKEN`          | `Dockerfile.tonmnh`   | TON mainnet operations         |
| 4 | OSIF Shop     | `slh-osif-shop`    | `OSIF_SHOP_TOKEN`        | `Dockerfile.osifshop`  | WebApp-enabled shop (port 8080)|
| 5 | Nifti         | `slh-nifti`        | `NIFTI_PUBLISHER_TOKEN`  | `Dockerfile.wellness`  | NFT/wellness publishing        |
| 6 | NFTY Madness  | `slh-nfty`         | `NFTY_MADNESS_TOKEN`     | `Dockerfile.nfty`      | NFT marketplace, CoinGecko     |
| 7 | UserInfo      | `slh-userinfo`     | `SLH_SELHA_TOKEN`        | Built in context       | Enhanced @userinfobot clone    |

---

## Website (slh-nft.com)

Hosted on GitHub Pages. Static HTML + JS connecting to Railway API.

**Path:** `D:\SLH_ECOSYSTEM\website\`

### HTML Pages

| Page                | File              | Purpose                                      |
|---------------------|-------------------|----------------------------------------------|
| Homepage            | `index.html`      | Landing page, hero, ecosystem overview        |
| Dashboard           | `dashboard.html`  | User dashboard (after Telegram login)         |
| Staking             | `staking.html`    | Staking plans UI, deposit/withdraw            |
| Wallet              | `wallet.html`     | Wallet balances, transfers                    |
| Referral            | `referral.html`   | Referral tree, link generation, stats         |
| Referral Card       | `referral-card.html` | Shareable referral card                    |
| Community           | `community.html`  | Community feed, posts, likes, comments        |
| Earn                | `earn.html`       | Earning opportunities                         |
| Trade               | `trade.html`      | Trading interface                             |
| Bots                | `bots.html`       | Bot catalog with prices                       |
| Blockchain          | `blockchain.html` | Blockchain explorer / info                    |
| Analytics           | `analytics.html`  | Analytics dashboard                           |
| Admin               | `admin.html`      | Admin panel                                   |
| Guides              | `guides.html`     | User guides                                   |
| Whitepaper          | `whitepaper.html` | Project whitepaper                            |

### Shared Assets

| File                | Purpose                                           |
|---------------------|---------------------------------------------------|
| `css/shared.css`    | Global styles, RTL support, dark theme            |
| `js/shared.js`      | API helpers, Telegram auth, shared utilities      |
| `js/analytics.js`   | Analytics tracking                                |
| `js/translations.js`| Multi-language support (HE, EN, RU, AR, FR)      |
| `manifest.json`     | PWA manifest                                      |
| `img/*.svg`         | Logo, avatar, favicon, apple-touch-icon           |

### API Connection

All pages connect to: `https://slh-api-production.up.railway.app/api/*`
Authentication: Telegram Login Widget -> `/api/auth/telegram`

---

## Shared Libraries

**Path:** `D:\SLH_ECOSYSTEM\shared\`

### wallet_engine.py

Blockchain wallet engine for BSC and TON chains. Importable by both the FastAPI API and Telegram bots.

**Capabilities:**
- BSC on-chain reads (SLH BEP-20 token via web3.py)
- TON balance queries (via TON Center API)
- Internal ledger transfers (off-chain)
- Deposit verification
- Portfolio queries
- Live price feeds (CoinGecko)

**Key constants:** `SLH_TOKEN_ADDRESS`, `SLH_DECIMALS=15`, `SLH_PRICE_ILS=444`, `TON_WALLET`

### wallet_api.py

FastAPI router that wraps `WalletEngine` for HTTP access. Provides endpoints for transfers, deposit verification, balances. Mounted in the Railway API app.

### community_api.py

Standalone FastAPI app for community features (posts, likes, comments). Connects to Railway PostgreSQL. Provides CORS for `slh-nft.com`. Rate-limited in-memory.

### slh_payments/

Payment processing module shared across all bots.

| File              | Purpose                                                |
|-------------------|--------------------------------------------------------|
| `__init__.py`     | Package init                                           |
| `config.py`       | Pricing per bot (`BotPricing` dataclass), TON wallet address, payment instructions |
| `db.py`           | Database helpers for payment tables                    |
| `payment_gate.py` | `PaymentGate` class - universal payment handler for aiogram & python-telegram-bot |
| `ledger.py`       | Internal token ledger - balances, transfers without blockchain |
| `referrals.py`    | `ReferralEngine` - cross-bot referral tracking, commission calc (15% tier 1, 5% tier 2) |
| `promotions.py`   | `PromoEngine` - time-limited deals, bundles, seasonal discounts |

### bot_template.py

Minimal bot template used by all `Dockerfile.template` bots. Provides: `/start` (with referral deep link), `/premium`, payment proof (photo), admin approve/reject. Configured entirely via env vars (`BOT_KEY`, `BOT_DISPLAY_NAME`, `BOT_DESCRIPTION`, `PRICE_ILS`, `PRICE_TON`).

### slh_bus/

Event bus module for inter-bot communication (directory exists, implementation TBD).

### slh_token_abi.json

ABI for the SLH BEP-20 token contract on BSC.

### group_config.json

Configuration for Telegram group mappings.

---

## API Endpoints

**Base URL:** `https://slh-api-production.up.railway.app`
**Source:** `D:\SLH_ECOSYSTEM\api\main.py`

### Authentication

| Method | Endpoint                   | Description                                |
|--------|----------------------------|--------------------------------------------|
| POST   | `/api/auth/telegram`       | Authenticate via Telegram Login Widget     |

### User

| Method | Endpoint                   | Description                                |
|--------|----------------------------|--------------------------------------------|
| GET    | `/api/user/{telegram_id}`  | Get user profile, balances, deposits, staking |

### Staking

| Method | Endpoint                         | Description                            |
|--------|----------------------------------|----------------------------------------|
| GET    | `/api/staking/plans`             | Get available staking plans (4 plans)  |
| POST   | `/api/staking/stake`             | Create a new staking position          |
| GET    | `/api/staking/positions/{user_id}` | Get user's staking positions         |

### Prices & Stats

| Method | Endpoint         | Description                                        |
|--------|------------------|----------------------------------------------------|
| GET    | `/api/prices`    | CoinGecko proxy (BTC, ETH, TON, BNB, SOL, XRP, DOGE) - 60s cache |
| GET    | `/api/stats`     | Ecosystem-wide stats (users, premium, staked, deposits) |
| GET    | `/api/health`    | Health check + DB connectivity                     |

### Transfers

| Method | Endpoint          | Description                                   |
|--------|-------------------|-----------------------------------------------|
| POST   | `/api/transfer`   | Transfer internal tokens (SLH, ZVK) between users |

### Referral System (10 Generations)

| Method | Endpoint                         | Description                            |
|--------|----------------------------------|----------------------------------------|
| POST   | `/api/referral/register`         | Register user in referral system       |
| GET    | `/api/referral/tree/{user_id}`   | Get referral tree for a user           |
| GET    | `/api/referral/link/{user_id}`   | Generate referral link                 |
| GET    | `/api/referral/leaderboard`      | Top referrers leaderboard              |
| GET    | `/api/referral/stats/{user_id}`  | Detailed referral stats for a user     |

### Activity & Transactions

| Method | Endpoint                          | Description                           |
|--------|-----------------------------------|---------------------------------------|
| GET    | `/api/activity/{user_id}`         | User activity feed                    |
| GET    | `/api/transactions/{user_id}`     | User transaction history              |
| GET    | `/api/leaderboard`                | Global leaderboard                    |

### Community

| Method | Endpoint                                  | Description                      |
|--------|-------------------------------------------|----------------------------------|
| GET    | `/api/community/posts`                    | Get community posts feed         |
| POST   | `/api/community/posts`                    | Create a new post                |
| POST   | `/api/community/posts/{post_id}/like`     | Like a post                      |
| POST   | `/api/community/posts/{post_id}/comments` | Comment on a post                |
| GET    | `/api/community/stats`                    | Community statistics             |
| GET    | `/api/community/health`                   | Community API health             |

### Analytics

| Method | Endpoint                  | Description                            |
|--------|---------------------------|----------------------------------------|
| POST   | `/api/analytics/event`    | Track analytics event                  |
| GET    | `/api/analytics/stats`    | Get analytics statistics               |

---

## Token Economics / כלכלת טוקנים

### SLH Token (BSC BEP-20)

| Property          | Value                                            |
|-------------------|--------------------------------------------------|
| Contract Address  | `0xACb0A09414CEA1C879c67bB7A877E4e19480f022`     |
| Chain             | Binance Smart Chain (BSC)                        |
| Decimals          | 15                                               |
| Price             | 444 ILS                                          |
| RPC               | `https://bsc-dataseed.binance.org/`              |

### TON Wallet

| Property          | Value                                            |
|-------------------|--------------------------------------------------|
| Address           | `UQCr743gEr_nqV_0SBkSp3CtYS_15R3LDLBvLmKeEv7XdGvp` |
| Network           | TON Mainnet                                       |
| API               | TON Center (`toncenter.com/api/v2`)              |

### Staking Plans

| Plan         | APY Monthly | APY Annual | Min TON | Lock Period |
|--------------|-------------|------------|---------|-------------|
| Monthly      | 4.0%        | 48%        | 1       | 30 days     |
| Quarterly    | 4.5%        | 55%        | 5       | 90 days     |
| Semi-Annual  | 5.0%        | 60%        | 10      | 180 days    |
| Annual       | 5.4%        | 65%        | 25      | 365 days    |

### Referral System (10 Generations)

| Generation | Commission Rate |
|------------|-----------------|
| 1 (direct) | 10%            |
| 2          | 5%             |
| 3          | 3%             |
| 4          | 2%             |
| 5          | 1%             |
| 6-10       | 0.5% each      |

Commissions are automatically distributed on staking deposits and other qualifying transactions.

### Internal Tokens

The shared ledger (`slh_payments/ledger.py`) supports multiple token types:

| Token | Description                    |
|-------|--------------------------------|
| SLH   | Main ecosystem token (BSC)     |
| ZVK   | ZVIKUSH token (ExpertNet)      |
| TON   | TON coin balances              |
| BNB   | Binance coin balances          |

### Bot Pricing (Premium Access)

| Bot          | Price (ILS) | Price (TON) |
|--------------|-------------|-------------|
| Factory      | 149         | 7.5         |
| BotShop      | 99          | 5.0         |
| Wallet       | 79          | 4.0         |
| Guardian     | 59          | 3.0         |
| Academia     | 41          | 2.0         |
| Community    | 41          | 2.0         |
| Template bots| 19-49       | 1.0-2.5     |

Payment flow: User sends TON to wallet address -> sends screenshot proof to bot -> admin approves -> user gets premium group invite link.

---

## Environment Variables

**File:** `D:\SLH_ECOSYSTEM\.env`

### Infrastructure

| Variable                | Purpose                              |
|-------------------------|--------------------------------------|
| `DB_PASSWORD`           | PostgreSQL password                  |
| `ADMIN_USER_ID`         | Telegram admin user ID               |
| `ADMIN_PASSWORD`        | Admin panel password                 |

### Bot Tokens (19 total)

| Variable                | Bot                    |
|-------------------------|------------------------|
| `CORE_BOT_TOKEN`        | SLH Academia           |
| `CORE_BOT_USERNAME`     | Academia username       |
| `GUARDIAN_BOT_TOKEN`    | Guardian                |
| `BOTSHOP_BOT_TOKEN`     | GATE BotShop           |
| `WALLET_BOT_TOKEN`      | SLH Wallet             |
| `FACTORY_BOT_TOKEN`     | BOT Factory            |
| `FUN_BOT_TOKEN`         | FUN/Community          |
| `ADMIN_BOT_TOKEN`       | Super Admin            |
| `EXPERTNET_BOT_TOKEN`   | ExpertNet/AIR          |
| `AIRDROP_BOT_TOKEN`     | Airdrop HUB            |
| `SLH_TON_TOKEN`         | SLH TON                |
| `SLH_LEDGER_TOKEN`      | SLH Ledger             |
| `CAMPAIGN_TOKEN`        | Campaign               |
| `GAME_BOT_TOKEN`        | Game Bot               |
| `SLH_SELHA_TOKEN`       | Selha + UserInfo       |
| `NIFTI_PUBLISHER_TOKEN` | Nifti Publisher        |
| `OSIF_SHOP_TOKEN`       | OSIF Shop              |
| `TON_MNH_TOKEN`         | TON MNH                |
| `CHANCE_PAIS_TOKEN`     | Chance Pais            |
| `NFTY_MADNESS_TOKEN`    | NFTY Madness           |
| `CRAZY_PANEL_TOKEN`     | CrazyPanel             |
| `TS_SET_TOKEN`          | TS Set                 |
| `MY_NFT_SHOP_TOKEN`     | NFT Shop               |
| `BEYNONIBANK_TOKEN`     | BeynoniBank            |
| `TEST_BOT_TOKEN`        | TestBot (dev)          |

### Blockchain

| Variable                | Purpose                              |
|-------------------------|--------------------------------------|
| `TON_API_KEY`           | TON Center API key                   |
| `TON_TESTNET_API_KEY`   | TON testnet API key                  |
| `BSC_RPC_URL`           | BSC RPC endpoint                     |
| `BSC_CHAIN_ID`          | BSC chain ID (56)                    |
| `BSC_TOKEN_ADDRESS`     | SLH contract address                 |
| `SLH_BSC_CONTRACT`      | SLH contract (duplicate)             |

### Trading (Binance)

| Variable                    | Purpose                          |
|-----------------------------|----------------------------------|
| `EXCHANGE_TESTNET_API_KEY`  | Binance testnet API key          |
| `EXCHANGE_TESTNET_SECRET_KEY` | Binance testnet secret         |
| `EXCHANGE_API_KEY`          | Binance mainnet API key          |
| `EXCHANGE_SECRET`           | Binance mainnet secret           |
| `EXCHANGE_NAME`             | Exchange name (binance)          |
| `TRADING_SYMBOL`            | Trading pair (BTC/USDT)          |
| `TRADING_CAPITAL`           | Trading capital amount           |

### Payment

| Variable                | Purpose                              |
|-------------------------|--------------------------------------|
| `PAYMENT_NETWORK`       | Payment network (ton)                |
| `PAYMENT_WALLET_ADDRESS`| TON wallet for payments              |
| `TON_WALLET`            | TON wallet address                   |

### Railway (Cloud)

| Variable                | Purpose                              |
|-------------------------|--------------------------------------|
| `RAILWAY_API_URL`       | Railway FastAPI URL                  |
| `RAILWAY_REDIS_URL`     | Railway Redis connection string      |
| `RAILWAY_DATABASE_URL`  | Railway PostgreSQL connection string  |

### Campaign Bot

| Variable                         | Purpose                          |
|----------------------------------|----------------------------------|
| `GOOGLE_CREDENTIALS_JSON`        | Google Sheets credentials        |
| `GOOGLE_SHEETS_SPREADSHEET_ID`   | Target spreadsheet ID            |
| `CAMPAIGN_LOG_GROUP_ID`          | Log group chat ID                |
| `CAMPAIGN_ALL_MEMBERS_GROUP_ID`  | All members group chat ID        |
| `CAMPAIGN_ACTIVISTS_GROUP_ID`    | Activists group chat ID          |
| `CAMPAIGN_EXPERTS_GROUP_ID`      | Experts group chat ID            |
| `CAMPAIGN_SUPPORT_GROUP_ID`      | Support group chat ID            |

### OSIF Shop

| Variable              | Purpose                              |
|-----------------------|--------------------------------------|
| `OSIFSHOP_WEBAPP_URL` | Cloudflare tunnel URL for WebApp     |

### Other

| Variable              | Purpose                              |
|-----------------------|--------------------------------------|
| `LETSEXCHANGE_REF`    | LetsExchange referral code           |
| `COINGECKO_BASE_URL`  | CoinGecko API base URL               |
| `LOG_LEVEL`           | Logging level (INFO)                 |

---

## Development Setup

### Prerequisites

- Windows 10/11 with Docker Desktop installed
- Python 3.11+ (for local development)
- Git
- `.env` file with all tokens (see above)

### Starting the System

```powershell
# Navigate to ecosystem root
cd D:\SLH_ECOSYSTEM

# Start all services
docker compose up -d

# Start only infrastructure
docker compose up -d postgres redis

# Start a specific bot
docker compose up -d core-bot

# Start script (PowerShell)
.\start.ps1 -Service all    # or: core, guardian, botshop, wallet, factory, fun, infra
```

### Common Docker Commands

```powershell
# View all running containers
docker compose ps

# View logs for a specific bot
docker compose logs -f core-bot

# Rebuild a specific bot (after code changes)
docker compose build core-bot
docker compose up -d core-bot

# Rebuild all bots
docker compose build
docker compose up -d

# Stop all services
docker compose down
# or
.\stop.ps1

# Restart a single bot
docker compose restart guardian-bot

# Enter a container shell
docker compose exec core-bot bash

# Check PostgreSQL directly
docker compose exec postgres psql -U postgres -d slh_main
```

### Deploying Website Changes

The website is hosted on GitHub Pages at `slh-nft.com`.

```powershell
cd D:\SLH_ECOSYSTEM\website
git add .
git commit -m "Update website"
git push origin main
# Changes go live within minutes on slh-nft.com
```

### Deploying API Changes

The API runs on Railway, connected to a GitHub repo.

```powershell
cd D:\SLH_ECOSYSTEM\api
git add .
git commit -m "Update API"
git push origin main
# Railway auto-deploys from the main branch
```

### Adding a New Template Bot

1. Add a new token to `.env`: `NEW_BOT_TOKEN=xxx`
2. Add service to `docker-compose.yml` using `Dockerfile.template`
3. Configure `BOT_KEY`, `BOT_DISPLAY_NAME`, `BOT_DESCRIPTION`, `PRICE_ILS`, `PRICE_TON`
4. Run: `docker compose up -d new-bot`

### Project Directory Structure

```
D:\SLH_ECOSYSTEM\
  +-- docker-compose.yml       # All services definition
  +-- .env                     # All environment variables
  +-- init-db.sql              # Database initialization
  +-- start.ps1 / stop.ps1    # PowerShell launchers
  +-- dockerfiles/             # 16 Dockerfiles
  +-- shared/                  # Shared Python libraries
  |     +-- bot_template.py
  |     +-- wallet_engine.py
  |     +-- wallet_api.py
  |     +-- community_api.py
  |     +-- slh_payments/      # Payment module
  |     +-- slh_bus/           # Event bus (WIP)
  +-- api/                     # Railway FastAPI backend
  +-- website/                 # GitHub Pages static site
  +-- airdrop/                 # Airdrop/HUB bot (large codebase)
  +-- expertnet-bot/           # ExpertNet bot (Zvika)
  +-- botshop/                 # BotShop bot
  +-- wallet/                  # Wallet bot
  +-- factory/                 # Factory bot
  +-- fun/                     # FUN bot
  +-- nfty-bot/                # NFTY Madness bot
  +-- tonmnh-bot/              # TON MNH bot
  +-- userinfo-bot/            # UserInfo bot
  +-- osif-shop/               # OSIF Shop bot
  +-- campaign-bot/            # Campaign bot assets
  +-- guardian/                # Guardian local files
  +-- core/                    # Core bot local files
  +-- backups/                 # Database backups
  +-- ops/                     # Operations scripts
  +-- logs.ps1                 # Log viewer script
  +-- build.ps1                # Build script
```

---

## Current Status & Known Issues

### What Works / מה עובד

- Docker Compose infrastructure (PostgreSQL + Redis) is stable
- All 22+ bot containers defined and can start in polling mode
- Railway API is live with 25+ endpoints
- Website (slh-nft.com) is live on GitHub Pages
- Telegram Login Widget authentication works
- Staking system (4 plans) is functional
- 10-generation referral system is implemented
- Shared payment gate works across template bots
- Internal token ledger (SLH, ZVK) is operational
- CoinGecko price proxy with caching works
- Community posts/likes/comments API works

### What Needs Fixing / מה צריך תיקון

- [ ] **Academia bot token** - expired/invalid, needs BotFather renewal
- [ ] **GitHub remote for Guardian** - repo returns 404, needs new remote or `gh auth` fix
- [ ] **Push all repos to GitHub** - not all bots have remote repos
- [ ] **AIRDROP_BOT_TOKEN shares the same token as EXPERTNET_BOT_TOKEN** - potential conflict
- [ ] **SLH_SELHA_TOKEN is used by both selha-bot and userinfo-bot** - token sharing may cause polling conflicts
- [ ] **slh_bus/ module** - directory exists but appears empty/unimplemented
- [ ] **Cloudflare Tunnel** for OSIF Shop webapp URL is hardcoded to a temporary tunnel
- [ ] **No health monitoring dashboard** yet
- [ ] **No centralized logging** - each bot logs independently
- [ ] **No automated backup strategy** - pg_dump not scheduled
- [ ] **Webhook mode not configured** - all bots run in polling mode

### Priority Tasks / משימות בעדיפות

1. Fix duplicate token assignments (AIRDROP/EXPERTNET, SELHA/USERINFO)
2. Renew Academia bot token via BotFather
3. Set up GitHub repos for all bots
4. Implement health monitoring (Guardian bot or dedicated dashboard)
5. Set up automated PostgreSQL backups (pg_dump cron)
6. Migrate from polling to webhook mode (Cloudflare Tunnel / Nginx)
7. Implement slh_bus for inter-bot event communication
8. Cross-bot SSO (unified user database)
9. Build React Native app (`D:\SLH_APP`)

---

> **Note:** This document should be updated whenever bots are added, removed, or reconfigured. Run `docker compose ps` to verify which containers are actually running vs. defined.
