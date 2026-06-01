# SLH Spark — Full Project Report & Work Plan
## 13 April 2026

---

## 1. ALL 114 API ENDPOINTS — Complete Inventory

### WORKING (31 GET + 7 param = 38 verified)

| # | Method | Endpoint | Status | Notes |
|---|--------|----------|--------|-------|
| 1 | GET | /api/health | OK 219ms | DB connected, v1.1.0 |
| 2 | GET | /api/admin/dashboard | OK 309ms | 9 users, 7 premium |
| 3 | GET | /api/admin/all-users | OK 245ms | Full user list + balances |
| 4 | GET | /api/admin/activity | OK 244ms | Recent logins + payments |
| 5 | GET | /api/ai/providers | OK 226ms | AI chat providers |
| 6 | GET | /api/analytics/stats | OK 287ms | Page views, visitors |
| 7 | GET | /api/audit/recent | OK 245ms | Last 100 audit entries |
| 8 | GET | /api/audit/verify-chain | OK 247ms | SHA-256 chain INTACT |
| 9 | GET | /api/beta/status | OK 235ms | Genesis 49 coupon status |
| 10 | GET | /api/broadcast/history | OK 228ms | Message broadcast log |
| 11 | GET | /api/community/health | OK 211ms | Community service OK |
| 12 | GET | /api/community/posts | OK 229ms | 11 real posts |
| 13 | GET | /api/community/stats | OK 227ms | 11 users, 11 posts |
| 14 | GET | /api/guardian/blacklist | OK 259ms | Anti-fraud blacklist |
| 15 | GET | /api/guardian/stats | OK 273ms | ZUZ system stats |
| 16 | GET | /api/launch/status | OK 241ms | 5 contributors, 0.08 BNB |
| 17 | GET | /api/leaderboard | OK 227ms | XP/balance rankings |
| 18 | GET | /api/marketplace/items | OK 265ms | Marketplace listings |
| 19 | GET | /api/marketplace/stats | OK 245ms | Marketplace overview |
| 20 | GET | /api/member-cards/all | OK 242ms | All member cards |
| 21 | GET | /api/network/slh-holders | OK 352ms | Token holder graph |
| 22 | GET | /api/p2p/orders | OK 221ms | P2P order book v1 |
| 23 | GET | /api/p2p/v2/orders | OK 230ms | P2P order book v2 (JWT) |
| 24 | GET | /api/prices | OK 434ms | CoinGecko live prices |
| 25 | GET | /api/referral/leaderboard | OK 264ms | Top referrers |
| 26 | GET | /api/shares/stats | OK 255ms | Social share tracking |
| 27 | GET | /api/staking/plans | OK 219ms | 4 APY tiers (48-65%) |
| 28 | GET | /api/stats | OK 248ms | Global platform stats |
| 29 | GET | /api/strategy/list | OK 199ms | Trading strategies |
| 30 | GET | /api/tokenomics/stats | OK 262ms | Token supply/burns |
| 31 | GET | /api/wallet/price | OK 210ms | SLH price in ILS/USD |

### WORKING WITH USER PARAMS (7 verified with user 224223270)

| # | Method | Endpoint | Status |
|---|--------|----------|--------|
| 32 | GET | /api/user/{telegram_id} | OK |
| 33 | GET | /api/wallet/{user_id} | OK |
| 34 | GET | /api/wallet/{user_id}/balances | OK |
| 35 | GET | /api/referral/stats/{user_id} | OK |
| 36 | GET | /api/staking/positions/{user_id} | OK |
| 37 | GET | /api/member-card/{user_id} | OK |
| 38 | GET | /api/guardian/check/{user_id} | OK |

### POST ENDPOINTS (45 — functional, not auto-tested)

| # | Method | Endpoint | Purpose |
|---|--------|----------|---------|
| 39 | POST | /api/admin/credit-rewards | Bulk credit missing ZVK |
| 40 | POST | /api/admin/manual-credit | Manual token credit |
| 41 | POST | /api/ai/chat | AI assistant chat |
| 42 | POST | /api/analytics/event | Track page view |
| 43 | POST | /api/audit/write | Write audit entry |
| 44 | POST | /api/auth/bot-sync | Bot↔website sync |
| 45 | POST | /api/auth/telegram | Telegram login |
| 46 | POST | /api/beta/create-coupon | Create beta coupon |
| 47 | POST | /api/broadcast/send | Send broadcast message |
| 48 | POST | /api/broadcast/personal-cards | Send member cards |
| 49 | POST | /api/cashback/process/{user_id} | Process cashback |
| 50 | POST | /api/cashback/record-distribution | Record distribution |
| 51 | POST | /api/cex/add-key | Add exchange API key |
| 52 | POST | /api/cex/sync/{key_id} | Sync CEX balances |
| 53 | POST | /api/community/posts | Create community post |
| 54 | POST | /api/community/posts/{id}/comments | Add comment |
| 55 | POST | /api/community/posts/{id}/like | Toggle like |
| 56 | POST | /api/external-wallets/add | Link external wallet |
| 57 | POST | /api/external-wallets/refresh/{id} | Refresh balance |
| 58 | POST | /api/external-wallets/refresh-all/{id} | Refresh all wallets |
| 59 | POST | /api/guardian/report | Report scammer |
| 60 | POST | /api/guardian/scan-message | Scan message for risk |
| 61 | POST | /api/launch/contribute | Submit contribution |
| 62 | POST | /api/launch/verify/{id} | Verify contribution |
| 63 | POST | /api/marketplace/list | List item for sale |
| 64 | POST | /api/marketplace/buy | Purchase item |
| 65 | POST | /api/marketplace/admin/approve | Approve listing |
| 66 | POST | /api/p2p/create-order | Create P2P order |
| 67 | POST | /api/p2p/fill-order | Fill P2P order |
| 68 | POST | /api/p2p/v2/create-order | Create P2P v2 order |
| 69 | POST | /api/p2p/v2/fill-order | Fill P2P v2 order |
| 70 | POST | /api/referral/register | Register referral |
| 71 | POST | /api/registration/initiate | Start registration |
| 72 | POST | /api/registration/submit-proof | Submit payment proof |
| 73 | POST | /api/registration/approve | Approve registration |
| 74 | POST | /api/registration/unlock | Unlock registration |
| 75 | POST | /api/rep/add | Add reputation points |
| 76 | POST | /api/shares/track | Track social share |
| 77 | POST | /api/staking/stake | Create staking position |
| 78 | POST | /api/tokenomics/burn | Burn tokens |
| 79 | POST | /api/tokenomics/reserves/add | Add reserves |
| 80 | POST | /api/tokenomics/internal-transfer | Internal transfer |
| 81 | POST | /api/transfer | Transfer tokens between users |
| 82 | POST | /api/user/ensure | Ensure user exists |
| 83 | POST | /api/user/profile | Update profile |
| 84 | POST | /api/user/link-wallet | Link BSC/TON wallet |
| 85 | POST | /api/user/unlink-wallet | Unlink wallet |
| 86 | POST | /api/wallet/deposit | Record deposit |
| 87 | POST | /api/wallet/send | Send tokens |

### GET WITH PARAMS (not auto-tested, 27)

| # | Method | Endpoint | Purpose |
|---|--------|----------|---------|
| 88 | GET | /api/activity/{user_id} | User activity feed |
| 89 | GET | /api/cashback/{user_id} | Cashback history |
| 90 | GET | /api/cex/keys/{user_id} | CEX API keys |
| 91 | GET | /api/cex/portfolio/{user_id} | CEX portfolio |
| 92 | GET | /api/external-wallets/{user_id} | External wallets |
| 93 | GET | /api/marketplace/items/{item_id} | Item details |
| 94 | GET | /api/marketplace/my-listings/{user_id} | My listings |
| 95 | GET | /api/marketplace/orders/{user_id} | My orders |
| 96 | GET | /api/member-card/image/{user_id} | Card PNG image |
| 97 | GET | /api/og/{slug}.png | OG social image |
| 98 | GET | /api/referral/link/{user_id} | Referral link |
| 99 | GET | /api/referral/tree/{user_id} | Referral tree |
| 100 | GET | /api/registration/status/{user_id} | Registration status |
| 101 | GET | /api/rep/{user_id} | REP score |
| 102 | GET | /api/strategy/backtest/{id} | Strategy backtest |
| 103 | GET | /api/strategy/{id} | Strategy details |
| 104 | GET | /api/transactions/{user_id} | Transaction history |
| 105 | GET | /api/user/full/{telegram_id} | Full user profile |
| 106 | GET | /api/user/wallet/{user_id} | User wallet info |
| 107 | GET | /api/wallet/{user_id}/transactions | Wallet TX history |

### DELETE ENDPOINTS (3)

| # | Method | Endpoint | Purpose |
|---|--------|----------|---------|
| 108 | DELETE | /api/cex/keys/{key_id} | Remove CEX key |
| 109 | DELETE | /api/external-wallets/{wallet_id} | Remove wallet |
| 110 | DELETE | /api/p2p/cancel-order/{order_id} | Cancel P2P order |
| 111 | DELETE | /api/p2p/v2/cancel-order/{order_id} | Cancel P2P v2 |

### ERRORS (3)

| # | Method | Endpoint | Error | Fix |
|---|--------|----------|-------|-----|
| 112 | GET | /api/registration/pending | 500 | DB query issue |
| 113 | GET | /api/marketplace/admin/pending | 422 | Missing query param |
| 114 | GET | /api/rep/leaderboard | 422 | Missing query param |

---

## 2. ALL 44 WEBSITE PAGES — Status Matrix

| Page | Live | API | Theme | i18n | Analytics | AI |
|------|------|-----|-------|------|-----------|-----|
| index.html | OK | -- | -- | YES | YES | YES |
| dashboard.html | OK | 14 endpoints | -- | YES | YES | YES |
| trade.html | OK | CoinGecko | -- | YES | YES | YES |
| earn.html | OK | API | -- | YES | YES | YES |
| wallet.html | OK | API+Web3 | -- | YES | YES | YES |
| bots.html | OK | -- | -- | YES | YES | YES |
| referral.html | OK | API | -- | YES | YES | YES |
| community.html | OK | API+demo fallback | -- | YES | YES | YES |
| daily-blog.html | OK | -- | -- | YES | YES | YES |
| guides.html | OK | -- | YES | YES | YES | YES |
| wallet-guide.html | OK | -- | -- | -- | YES | YES |
| blockchain.html | OK | BSCScan+TON | -- | YES | YES | YES |
| network.html | OK | API | -- | YES | YES | YES |
| roadmap.html | OK | -- | -- | YES | YES | YES |
| staking.html | OK | API | -- | YES | YES | YES |
| p2p.html | OK | API | YES | -- | YES | YES |
| ecosystem-guide.html | OK | -- | YES | -- | YES | YES |
| whitepaper.html | OK | -- | -- | YES | YES | YES |
| healing-vision.html | OK | -- | YES | -- | YES | YES |
| challenge.html | OK | API | YES | -- | YES | YES |
| for-therapists.html | OK | -- | YES | -- | YES | YES |
| invite.html | OK | API | -- | -- | YES | YES |
| member.html | OK | API | YES | -- | YES | YES |
| partner-dashboard.html | OK | API | YES | -- | YES | YES |
| launch-event.html | OK | API+CoinGecko | YES | -- | YES | YES |
| dex-launch.html | OK | -- | YES | -- | YES | YES |
| partner-launch-invite.html | OK | -- | YES | -- | YES | YES |
| jubilee.html | OK | -- | YES | -- | YES | YES |
| admin.html | OK | API (19 pages) | YES | -- | YES | YES |
| analytics.html | OK | API | -- | -- | YES | YES |
| broadcast-composer.html | OK | API | YES | -- | YES | YES |
| system-health.html | OK | API | YES | -- | YES | YES |
| morning-checklist.html | OK | -- | YES | -- | YES | YES |
| morning-handoff.html | OK | -- | YES | -- | YES | YES |
| overnight-report.html | OK | -- | YES | -- | YES | YES |
| ops-report-20260411.html | OK | -- | YES | -- | YES | YES |
| ops-dashboard.html | OK | API (live) | -- | -- | YES | YES |
| onboarding.html | OK | API | -- | -- | YES | YES |
| getting-started.html | OK | -- | -- | -- | YES | YES |
| referral-card.html | OK | -- | -- | YES | YES | YES |
| rotate.html | OK | -- | -- | -- | YES | YES |
| test-bots.html | OK | -- | -- | -- | YES | YES |
| privacy.html | OK | -- | -- | -- | YES | YES |
| terms.html | OK | -- | -- | -- | YES | YES |

**Coverage: 44/44 live (100%), 21 with API (48%), 18 theme (41%), 16 i18n (36%), 44 analytics (100%), 44 AI (100%)**

---

## 3. 5-TOKEN ECONOMY

| Token | Role | Status | Mechanism |
|-------|------|--------|-----------|
| **SLH** | Premium/governance | Live on BSC, PancakeSwap pool | BEP-20, 15 decimals, 111M supply |
| **MNH** | Stablecoin (₪1) | Internal | 1:1 ILS backed |
| **ZVK** | Activity rewards | Internal | Earned via contributions, staking |
| **REP** | Personal reputation | Internal | 0-1000+ (Basic→Elder tiers) |
| **ZUZ** | Anti-fraud "Mark of Cain" | NEW | Guardian system, auto-ban at 100 |

---

## 4. WORK PLAN

### Week 3 (Apr 14-20) — Security + User Experience
| Day | Task | Priority | Est. |
|-----|------|----------|------|
| Mon | Set Railway env vars (JWT_SECRET, ADMIN_API_KEYS) | P0 | 10min |
| Mon | Railway redeploy + credit ZVK to 4 contributors | P0 | 15min |
| Mon | Fix 3 broken endpoints (registration, rep, marketplace) | P1 | 1h |
| Tue | Theme switcher on remaining 26 pages | P1 | 2h |
| Tue | P2P frontend activation (connect to v2 endpoints) | P1 | 3h |
| Wed | wallet.html: clarify internal vs on-chain labels | P1 | 1h |
| Wed | Community feed improvements + image upload | P2 | 2h |
| Thu | i18n on 28 pages (5 languages) | P2 | 4h |
| Thu | Set /commands for 12 bots via @BotFather | P2 | 1h |
| Fri | LP Lock on Mudra (anti-rug proof) | P2 | 2h |
| Fri | Personal outreach to 5 users | P2 | 30min |
| Sat | Webhook migration start (3 priority bots) | P3 | 4h |
| Sun | Test coverage for key endpoints | P3 | 3h |

### Week 4 (Apr 21-27) — Growth + Infrastructure
| Task | Priority | Est. |
|------|----------|------|
| Split main.py into route modules (7000 lines!) | P2 | 4h |
| Trust Wallet logo PR | P2 | 1h |
| GemPad Presale consideration | P3 | 2h |
| Redis caching for slow endpoints | P3 | 2h |
| Backup cleanup + fresh pg_dump | P3 | 1h |
| Open source page (careers/contributors) | P3 | 3h |
| MEXC/Gate.io listing research | P3 | 2h |
| Database migrations system | P3 | 2h |

### Month 2 (May) — Scale + Revenue
| Task | Priority |
|------|----------|
| Course marketplace (150 ILS, first course) | P1 |
| Fiat on-ramp (MoonPay/Transak) | P2 |
| Auto-compound vault | P2 |
| Strategy Engine live execution | P2 |
| Mobile app (React Native) MVP | P3 |
| CertiK audit consideration | P3 |
| Ambassador SaaS (bot-per-ambassador) | P3 |

### Month 3 (June) — Jubilee Vision
| Task | Priority |
|------|----------|
| Full Jubilee year integration | P1 |
| Cross-bot economy unification | P1 |
| Shariah-compliant staking option | P2 |
| Prediction markets (no-loss model) | P3 |
| Launchpad for ethical projects | P3 |
| 100 registered users target | P1 |

---

## 5. MICROSERVICES ARCHITECTURE (Current → Target)

### Current (Monolith + Bots)
```
Railway API (1 monolith, 7000 lines, 114 endpoints)
├── Auth + Users
├── Wallet + Balances
├── Staking + Earnings
├── Community + Social
├── P2P Trading
├── Marketplace
├── Guardian/ZUZ
├── Tokenomics
├── Analytics
├── Admin
├── CEX Integration
├── Broadcast
├── Member Cards
└── Launch/Genesis

25 Telegram Bots (Docker Compose, polling)
├── 9 Custom bots
└── 16 Template bots
```

### Target (Microservices)
```
API Gateway (nginx/traefik)
├── auth-service (users, JWT, Telegram login)
├── wallet-service (balances, transfers, on-chain)
├── staking-service (positions, rewards, APY)
├── community-service (posts, comments, likes)
├── p2p-service (orders, matching, escrow)
├── marketplace-service (listings, purchases)
├── guardian-service (ZUZ, blacklist, scanning)
├── tokenomics-service (burns, reserves, supply)
├── analytics-service (events, stats, dashboards)
├── broadcast-service (Telegram messages, notifications)
├── cex-service (Bybit, Binance integration)
├── member-service (cards, NFTs, REP)
├── launch-service (Genesis, fundraising)
├── strategy-service (backtests, execution)
└── onboarding-service (registration, coupons)

Bot Gateway (webhook mode)
├── Core bots (Academia, Guardian, Wallet)
├── Commerce bots (Shop, Factory, NFT)
├── Community bots (Fun, Campaign, Game)
└── Utility bots (Admin, Ledger, TON)

Shared Infrastructure
├── PostgreSQL 15 (primary)
├── Redis 7 (cache + pub/sub)
├── RabbitMQ (event bus)
├── MinIO (file storage)
└── Grafana + Loki (monitoring)
```

---

## 6. JUBILEE YEAR INTEGRATION

### Vision: Digital Economic Reset
Based on Leviticus 25, Deuteronomy 15, Isaiah 61:

| Biblical Principle | SLH Implementation |
|---|---|
| Debt release (שמיטת חובות) | Auto-forgive small debts every 7th cycle |
| Land return (שיבת הנחלה) | Token redistribution mechanism |
| Freedom (דרור) | Open source ecosystem, free tier access |
| Community healing | 21-Day Challenge, therapist network |
| Equal opportunity | Genesis 49 — first 49 get equal access |

### Jubilee Features (Planned)
- Jubilee token burn event (every 49 days)
- Community healing circles (Telegram groups)
- Therapist marketplace (for-therapists.html)
- Open source contribution rewards (ZVK)
- Ambassador program for communities

---

## 7. OPEN SOURCE / HIRING PAGE

### Proposed: /careers.html
- Mission statement (Hebrew + English)
- Open roles: Bot developers, Frontend, Community managers
- How to contribute (GitHub, Telegram)
- ZVK rewards for open source contributions
- Apply via Telegram bot (@SLH_careers_bot)
