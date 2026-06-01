# System Status Report — 2026-04-07

> SLH Ecosystem | SPARK IND
> Generated: April 7, 2026

---

## Live Services / שירותים פעילים

### Railway API
- **URL:** https://slh-api-production.up.railway.app
- **Framework:** FastAPI (Python)
- **Database:** PostgreSQL on Railway + Local PostgreSQL
- **Redis:** Railway Redis

#### API Endpoints (25 total)

| # | Method | Endpoint | Description |
|---|--------|----------|-------------|
| 1 | POST | `/api/auth/telegram` | Telegram login authentication |
| 2 | GET | `/api/user/{telegram_id}` | Get user profile |
| 3 | GET | `/api/staking/plans` | List available staking plans |
| 4 | POST | `/api/staking/stake` | Create new staking position |
| 5 | GET | `/api/staking/positions/{user_id}` | Get user staking positions |
| 6 | GET | `/api/prices` | Get token prices (CoinGecko) |
| 7 | GET | `/api/stats` | Get ecosystem stats |
| 8 | GET | `/api/health` | Health check |
| 9 | POST | `/api/transfer` | Transfer tokens between users |
| 10 | POST | `/api/referral/register` | Register referral relationship |
| 11 | GET | `/api/referral/tree/{user_id}` | Get user's referral tree |
| 12 | GET | `/api/referral/link/{user_id}` | Get referral link |
| 13 | GET | `/api/referral/leaderboard` | Referral leaderboard |
| 14 | GET | `/api/referral/stats/{user_id}` | User referral stats |
| 15 | GET | `/api/activity/{user_id}` | User activity feed |
| 16 | GET | `/api/transactions/{user_id}` | User transaction history |
| 17 | GET | `/api/leaderboard` | Global leaderboard |
| 18 | GET | `/api/community/posts` | List community posts |
| 19 | POST | `/api/community/posts` | Create community post |
| 20 | POST | `/api/community/posts/{post_id}/like` | Like a post |
| 21 | POST | `/api/community/posts/{post_id}/comments` | Comment on a post |
| 22 | GET | `/api/community/stats` | Community statistics |
| 23 | GET | `/api/community/health` | Community health check |
| 24 | POST | `/api/analytics/event` | Track analytics event |
| 25 | GET | `/api/analytics/stats` | Get analytics statistics |

### Website (slh-nft.com)
- **Hosting:** GitHub Pages
- **URL:** https://slh-nft.com
- **Pages (15 total):**

| Page | File | Description |
|------|------|-------------|
| Home | `index.html` | Landing page / דף נחיתה |
| Wallet | `wallet.html` | Token wallet / ארנק |
| Trade | `trade.html` | Trading interface / מסחר |
| Earn | `earn.html` | Staking & earning / השקעות |
| Bots | `bots.html` | Telegram bots showcase / בוטים |
| Referral | `referral.html` | Referral program / הפניות |
| Dashboard | `dashboard.html` | User dashboard / לוח בקרה |
| Guides | `guides.html` | User guides / מדריכים |
| Staking | `staking.html` | Staking page / סטייקינג |
| Whitepaper | `whitepaper.html` | Whitepaper / ספר לבן |
| Admin | `admin.html` | Admin panel / פאנל ניהול |
| Referral Card | `referral-card.html` | Referral card / כרטיס הפניה |
| Blockchain | `blockchain.html` | Blockchain explorer / בלוקצ'יין |
| Analytics | `analytics.html` | Analytics dashboard / ניתוח נתונים |
| Community | `community.html` | Community forum / קהילה |

---

## Docker Containers / קונטיינרים

| Container | Status | Ports | Notes |
|-----------|--------|-------|-------|
| slh-postgres | Up 2 days (healthy) | 5432 | PostgreSQL database |
| slh-redis | Up 2 days (healthy) | 6379 | Redis cache |
| slh-core-bot | Up 47 hours | — | Core SLH bot |
| slh-selha | Up 47 hours | — | Selha bot |
| slh-botshop | Up 47 hours | — | Bot Shop |
| slh-ton-mnh | Up 47 hours | — | TON MNH bot |
| slh-wallet | Up 47 hours | — | Wallet bot |
| slh-fun | Up 47 hours | 8002 | Fun bot |
| slh-ledger | Up 47 hours | — | Ledger bot |
| slh-game | Up 47 hours | — | Game bot |
| slh-campaign | Up 47 hours | — | Campaign bot |
| slh-ton | Up 47 hours | — | TON bot |
| slh-admin | Up 47 hours | — | Admin bot |
| slh-osif-shop | Up 22 hours | 8080 | OSIF Shop |
| slh-guardian-bot | Up 9 hours | 8001 | Guardian bot |
| slh-expertnet | Up 8 hours | — | ExpertNet (Zvika) |
| slh-nifti | Up 8 hours | — | NIFTI Publisher |
| slh-nft-shop | Up 8 hours | — | NFT Shop |
| slh-nfty | Up 8 hours | — | NFTY Madness |
| slh-ts-set | Up 8 hours | — | TS Set bot |
| slh-beynonibank | Up 8 hours | — | Beynoni Bank |
| slh-airdrop | Up 7 hours | — | Airdrop bot |
| **slh-factory** | **Exited (0) 4h ago** | — | **STOPPED - needs restart** |

**Summary:** 22/23 containers running, 1 stopped (slh-factory)

---

## Recent Changes (Today - 2026-04-07) / שינויים אחרונים

1. **Community backend** — PostgreSQL-backed posts, comments, likes via Railway API
   - קהילה עם פוסטים, תגובות ולייקים דרך Railway API
2. **Analytics dashboard** — Real-time stats from Railway API
   - דאשבורד אנליטיקה בזמן אמת
3. **Navigation fixed on community.html** — topnav-root + translations
   - תיקון ניווט בדף קהילה
4. **Factory bot** — New token deployed
   - בוט פקטורי - טוקן חדש
5. **PROJECT_MAP.md created** — 747 lines comprehensive project map
   - מפת פרויקט מלאה נוצרה

---

## Environment Variables Checklist / משתני סביבה

> Names only - NO values shown / שמות בלבד - ערכים לא מוצגים

### Database & Infrastructure
- [x] DB_PASSWORD
- [x] DATABASE_URL
- [x] REDIS_URL
- [x] RAILWAY_API_URL
- [x] RAILWAY_REDIS_URL
- [x] RAILWAY_DATABASE_URL

### Admin
- [x] ADMIN_USER_ID
- [x] ADMIN_BOT_TOKEN

### Bot Tokens (19 total)
- [x] CORE_BOT_TOKEN
- [x] CORE_BOT_USERNAME
- [x] GUARDIAN_BOT_TOKEN
- [x] BOTSHOP_BOT_TOKEN
- [x] WALLET_BOT_TOKEN
- [x] FACTORY_BOT_TOKEN
- [x] FUN_BOT_TOKEN
- [x] SLH_TON_TOKEN
- [x] SLH_LEDGER_TOKEN
- [x] CAMPAIGN_TOKEN
- [x] GAME_BOT_TOKEN
- [x] SLH_SELHA_TOKEN
- [x] NIFTI_PUBLISHER_TOKEN
- [x] OSIF_SHOP_TOKEN
- [x] TON_MNH_TOKEN
- [x] CHANCE_PAIS_TOKEN
- [x] NFTY_MADNESS_TOKEN
- [x] CRAZY_PANEL_TOKEN
- [x] TS_SET_TOKEN
- [x] EXPERTNET_BOT_TOKEN
- [x] MY_NFT_SHOP_TOKEN
- [x] AIRDROP_BOT_TOKEN
- [x] BEYNONIBANK_TOKEN
- [x] TEST_BOT_TOKEN
- [x] BOT_TOKEN (alias for NFTY_MADNESS_TOKEN)

### Blockchain & TON
- [x] TON_API_KEY
- [x] TON_TESTNET_API_KEY
- [x] BSC_RPC_URL
- [x] BSC_CHAIN_ID
- [x] BSC_TOKEN_ADDRESS
- [x] SLH_BSC_CONTRACT
- [x] PAYMENT_NETWORK
- [x] PAYMENT_WALLET_ADDRESS
- [x] TON_WALLET

### Exchange / Trading
- [x] EXCHANGE_TESTNET_API_KEY
- [x] EXCHANGE_TESTNET_SECRET_KEY
- [x] EXCHANGE_API_KEY
- [x] EXCHANGE_SECRET
- [x] EXCHANGE_NAME
- [x] TRADING_SYMBOL
- [x] TRADING_CAPITAL

### Other
- [x] COINGECKO_BASE_URL
- [x] LOG_LEVEL

**Total: 44 environment variables configured**

---

## Known Issues / בעיות ידועות

### Critical
1. **slh-factory container is stopped** — Exited with code 0 four hours ago. Needs restart.
   - קונטיינר slh-factory עצר - צריך הפעלה מחדש
2. **AIRDROP_BOT_TOKEN = EXPERTNET_BOT_TOKEN** — Both bots share the same token. This may cause conflicts.
   - טוקן משותף בין שני בוטים - עלול לגרום להתנגשויות

### Warnings
3. **wallet.html** — Currently uses mock data, not connected to real API
   - דף ארנק עובד עם נתונים מדומים
4. **GitHub Guardian repo** — Returns 404, needs new remote or auth fix
   - ריפו Guardian ב-GitHub מחזיר 404

---

## Next Steps / Roadmap / צעדים הבאים

### Short Term (This Week)
- [ ] Restart slh-factory container
- [ ] Connect `wallet.html` to real API endpoints
- [ ] Deploy `wallet_api.py` to Railway
- [ ] Fix AIRDROP_BOT_TOKEN duplicate issue
- [ ] Test community.html from multiple devices

### Medium Term (This Month)
- [ ] Build trading engine (order book) / מנוע מסחר
- [ ] Add i18n to Telegram bots (HE, EN, RU, AR, FR) / תמיכה ב-5 שפות
- [ ] Real-time WebSocket for community page
- [ ] Build admin dashboard with real data
- [ ] Fix Guardian GitHub remote

### Long Term (Next Quarter)
- [ ] Shariah-compliant finance features
  - Staking PoS (deterministic yield) / סטייקינג
  - Prediction Markets (no-loss model) / שווקי חיזוי
  - Launchpad for ethical projects / לאנצ'פד
- [ ] Ambassador SaaS (bot-per-ambassador) / מערכת שגרירים
- [ ] Mobile app (React Native / PWA) / אפליקציה ניידת

---

*Report generated automatically. See PROJECT_MAP.md for full architecture details.*
