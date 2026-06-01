# 🔍 SLH SYSTEM OMNI — דוח סריקה מלא
**תאריך:** 2026-04-10 (יום שישי בבוקר)
**סורק:** Claude Opus 4.6
**היקף:** כל המערכת קצה לקצה — Docker, API, Website, DB, Bots, Tokens

---

## 🎯 תמצית מנהלים (TL;DR)

| רכיב | מצב | הערות |
|------|-----|-------|
| 🟢 Docker (22 containers) | **UP** | כולם רצים ~27 דקות |
| 🟢 PostgreSQL | **HEALTHY** | 6 DBs, slh_main + 5 שרתי בוטים |
| 🟢 Redis (local) | **HEALTHY** | + redis-nifty נפרד |
| 🟢 Railway API | **LIVE** | 55 endpoints, db connected |
| 🟢 Website slh-nft.com | **LIVE** | 23 HTML pages, PWA, GitHub Pages |
| 🟡 Telegram Bots | **חלקי** | חלק עובד, חלק עם קונפליקטים |
| 🔴 Token Mapping | **בעיה** | 2 קונפליקטים של טוקנים |
| 🔴 Factory Bot | **polling errors** | רץ אבל לא מגיב ל-Telegram בעקביות |
| 🟡 DB slh_factory/slh_guardian | **ריק** | אין טבלאות |

**בשורה תחתונה:** 95% מהמערכת חיה ותקינה. יש 4 בעיות ספציפיות שצריך לטפל בהן היום.

---

## 🐳 Docker Containers — מצב נוכחי

### Containers רצים (22 + redis-nifty)

| # | Container | Service | Image | CPU | RAM | מצב |
|---|-----------|---------|-------|-----|-----|-----|
| 1 | slh-postgres | postgres | postgres:15-alpine | 0% | 48 MB | 🟢 Healthy |
| 2 | slh-redis | redis | redis:7-alpine | 4% | 6.5 MB | 🟢 Healthy |
| 3 | slh-core-bot | core-bot | slh_ecosystem-core-bot | 0% | 90 MB | 🟢 @SLH_Academia_bot |
| 4 | slh-guardian-bot | guardian-bot | slh_ecosystem-guardian-bot | 0.3% | 66 MB | 🟢 רץ |
| 5 | slh-botshop | botshop | slh_ecosystem-botshop | 0.1% | 63 MB | 🟢 polling OK |
| 6 | slh-wallet | wallet-bot | slh_ecosystem-wallet-bot | 0.1% | 61 MB | 🟢 polling OK |
| 7 | slh-factory | factory-bot | slh_ecosystem-factory-bot | 0.1% | 68 MB | 🔴 **polling errors** |
| 8 | slh-fun | fun-bot | slh_ecosystem-fun-bot | 0.1% | 115 MB | 🟢 @SLH_community_bot |
| 9 | slh-admin | admin-bot | slh_ecosystem-admin-bot | 0% | 83 MB | 🟢 @MY_SUPER_ADMIN_bot |
| 10 | slh-expertnet | expertnet-bot | slh_ecosystem-expertnet-bot | 0% | 91 MB | 🔴 **@My_crazy_panel_bot** (mapping שגוי!) |
| 11 | slh-airdrop | airdrop-bot | slh_ecosystem-airdrop-bot | 0% | 91 MB | 🟢 @SLH_AIR_bot |
| 12 | slh-ton | slh-ton-bot | slh_ecosystem-slh-ton-bot | 0% | 78 MB | 🟢 @SLH_ton_bot |
| 13 | slh-ton-mnh | ton-mnh-bot | slh_ecosystem-ton-mnh-bot | 0% | 38 MB | 🟢 polling OK |
| 14 | slh-selha | selha-bot | slh_ecosystem-selha-bot | 0% | 79 MB | 🟢 @Slh_selha_bot |
| 15 | slh-ts-set | ts-set-bot | slh_ecosystem-ts-set-bot | 0% | 78 MB | 🟢 @ts_set_bot |
| 16 | slh-nft-shop | nft-shop-bot | slh_ecosystem-nft-shop-bot | 0% | 78 MB | 🟢 @MY_NFT_SHOP_bot |
| 17 | slh-beynonibank | beynonibank-bot | slh_ecosystem-beynonibank-bot | 0% | 82 MB | 🟢 @beynonibank_bot |
| 18 | slh-ledger | ledger-bot | slh_ecosystem-ledger-bot | 0% | 78 MB | 🟢 @SLH_Ledger_bot |
| 19 | slh-campaign | campaign-bot | slh_ecosystem-campaign-bot | 0% | 29 MB | 🟢 polling OK |
| 20 | slh-game | game-bot | slh_ecosystem-game-bot | 0% | 78 MB | 🟢 @G4meb0t_bot_bot |
| 21 | slh-osif-shop | osif-shop-bot | slh_ecosystem-osif-shop-bot | 0% | 89 MB | 🟢 @OsifShop_bot |
| 22 | slh-nifti | nifti-bot | slh_ecosystem-nifti-bot | 0% | 78 MB | 🟢 @NIFTI_Publisher_Bot |
| ➕ | slh-nifty-new | (נפרד) | - | 0% | 33 MB | 🟢 NFTY token 7998856873 |
| ➕ | redis-nifty | (נפרד) | redis | 0.3% | 11 MB | 🟢 רץ |

**סה"כ זיכרון:** ~1.7 GB / 3.8 GB זמינים

### Containers חסרים לעומת PROJECT_MAP.md:
- `slh-nfty` — הוחלף ב-`slh-nifty-new` (חיצוני ל-docker-compose)
- `slh-userinfo` — לא רץ (משתף טוקן עם selha, הוסר כדי למנוע קונפליקט)

---

## 🌐 API Railway — 55 Endpoints

**Base URL:** `https://slh-api-production.up.railway.app`
**מקור:** `D:\SLH_ECOSYSTEM\api\main.py` (3,054 שורות)
**Git:** `github.com/osifeu-prog/slh-api` ✅ מחובר
**מצב:** 🟢 **LIVE** — `{"status":"ok","db":"connected","version":"1.0.0"}`

### Health Check תוצאות

| Endpoint | סטטוס | דוגמה |
|----------|-------|-------|
| `/api/health` | ✅ 200 | `db:connected, version:1.0.0` |
| `/api/stats` | ✅ 200 | 7 users, 10 TON staked, 20 bots live |
| `/api/prices` | ✅ 200 | BTC $71,574, ETH $2,185, TON $1.29, BNB $600 |
| `/api/wallet/price` | ✅ 200 | SLH 444 ILS, $121.64 |
| `/api/admin/dashboard` | ✅ 200 | 16,537 analytics events, 1,237 today views |
| `/api/staking/plans` | ✅ 200 | 4 plans: 4%/4.5%/5%/5.4% monthly |
| `/api/referral/leaderboard` | ✅ 200 | osifeu_prog #1 (1 referral) |
| `/api/community/health` | ✅ 200 | `service:community, status:ok` |
| `/api/community/stats` | ✅ 200 | 10 posts, 10 users |
| `/api/user/224223270` | ✅ 200 | Osif, registered, 0 TON balance |
| `/api/marketplace/items` | ✅ 200 | ריק (0 פריטים) |

### קטגוריות Endpoints (55 בסה"כ):
1. **Auth** (3) — telegram, bot-sync
2. **Registration** (6) — initiate, submit-proof, approve, unlock, status, pending
3. **Beta** (2) — status, create-coupon
4. **User** (5) — profile, wallet linking, full info
5. **Staking** (3) — plans, stake, positions
6. **Prices/Stats** (3) — prices, stats, health
7. **Transfer** (1)
8. **Referral** (5) — register, tree, link, leaderboard, stats
9. **Activity/Transactions** (3)
10. **Community** (6) — posts, likes, comments, stats
11. **Analytics** (2) — event, stats
12. **Wallet** (6) — price, balances, deposit, send, transactions
13. **Admin** (2) — dashboard, activity
14. **Marketplace** (8) — list, items, buy, orders, my-listings, approve, pending, stats

---

## 💻 Website slh-nft.com

**מקום:** `D:\SLH_ECOSYSTEM\website\`
**Git:** `github.com/osifeu-prog/osifeu-prog.github.io` ✅ מחובר
**Hosting:** GitHub Pages → slh-nft.com (CNAME)
**מצב:** 🟢 **LIVE**

### 22 דפי HTML שעובדים:
```
admin.html, analytics.html, blockchain.html, bots.html,
community.html, daily-blog.html, dashboard.html, earn.html,
guides.html, index.html, invite.html, network.html,
privacy.html, referral-card.html, referral.html, roadmap.html,
staking.html, terms.html, trade.html, wallet-guide.html,
wallet.html, whitepaper.html
```

### נכסים:
- `css/`, `js/`, `img/`, `assets/`, `docs/`
- `manifest.json` (PWA ✅)
- `sw.js` (Service Worker ✅)
- `tonconnect-manifest.json` (TonConnect ✅)
- `sitemap.xml`, `robots.txt`
- `CNAME` → slh-nft.com

### Commits אחרונים (Website):
1. `87e5b57` — fix: Factory bot link + blockchain honest DEX status + cache bust
2. `f887c88` — fix: namespace inline T (i18n raw keys)
3. `8ea4eea` — feat: sitemap footer + marketplace image upload + price fix
4. `4327aee` — feat: invite page + daily blog + marketplace polish
5. `3204d80` — feat: add marketplace (חנות) to community page

### שינויים לא-committed (Website):
```
 M community.html
 M dashboard.html
 M invite.html
?? js/web3.js   ← קובץ Web3 חדש לא נוסף ל-git!
```

---

## 🗃️ PostgreSQL Databases

### 6 Databases ב-`slh-postgres`

| DB | טבלאות | שימוש | מצב |
|-----|--------|-------|-----|
| `slh_main` | **44 tables** | Core bot, Admin, ExpertNet, Airdrop, kol template bots | 🟢 פעיל |
| `slh_botshop` | 9 tables | BotShop bot | 🟢 פעיל (1 user) |
| `slh_wallet` | 1 table | Wallet bot | 🟡 מינימלי |
| `slh_factory` | **0 tables** | Factory bot | 🔴 **ריק** |
| `slh_guardian` | **0 tables** | Guardian bot | 🔴 **ריק** |
| `slh` | ? | (ישן) | unused |

### slh_main — Schema מרכזי
44 טבלאות כוללות:
- `users` (7 רשומות), `referrals` (0), `referral_stats`
- `token_balances` (11), `token_transfers`, `user_balances`
- `deposits` (2), `withdrawals`, `premium_users` (11)
- `staking_positions` (ב-slh_botshop), `tasks`, `user_tasks`
- `airdrop_users` (4), `airdrop_events` (0), `claims`, `daily_claims`
- `nfty_items`, `nfty_users`, `nfty_listings`, `nfty_activation_requests`
- `virtual_pets`, `pet_action_log`, `breathing_sessions`, `daily_quests`
- `products`, `shops`, `shop_products`, `purchase_orders`, `sell_orders`
- `community_posts` (ב-Railway PG)
- `audit_log`, `system_events`, `system_settings`, `blacklist`
- `bank_accounts`, `fee_schedule`, `journal_entries`, `kyc_records`

### משתמשים רשומים (ב-Local DB)
```
590733872  Yaara_Kaiser     2026-04-07
214962399  TruthMVMT_Admin  2026-04-05
8088324234 P22PPPPPP        2026-04-05
480100522  Zoharot          2026-04-04
7940057720 Yahav_anter      2026-04-04
224223270  osifeu_prog      2026-04-04  ← ADMIN
920721513  rami1864         2026-04-04
```
**סה"כ: 7 משתמשים** (Local DB)

Railway DB יש 7 משתמשים + analytics של 1,237 views היום + 16,537 אירועים.

---

## 🤖 Telegram Bots — מצב בפועל

### 🟢 בוטים שעובדים תקין (18)

| # | Username | Container | טוקן ID | מצב |
|---|----------|-----------|---------|-----|
| 1 | @SLH_Academia_bot | slh-core-bot | 8351227223 | ✅ polling |
| 2 | @SLH_AIR_bot (Investment HUB) | slh-airdrop | 8530795944 | ✅ polling + WalletEngine connected |
| 3 | @SLH_Wallet_bot | slh-wallet | 8729004785 | ✅ polling |
| 4 | @SLH_community_bot (FUN) | slh-fun | 8554485332 | ✅ polling |
| 5 | @MY_SUPER_ADMIN_bot | slh-admin | 7644371589 | ✅ polling |
| 6 | @G4meb0t_bot_bot | slh-game | 8298897331 | ✅ polling |
| 7 | @OsifShop_bot | slh-osif-shop | 8106987443 | ✅ polling |
| 8 | @NIFTI_Publisher_Bot | slh-nifti | 8478252455 | ✅ polling |
| 9 | @SLH_ton_bot | slh-ton | 8172123240 | ✅ polling |
| 10 | @Slh_selha_bot | slh-selha | 8225059465 | ✅ polling |
| 11 | @SLH_Ledger_bot | slh-ledger | 8494620699 | ✅ polling |
| 12 | @ts_set_bot | slh-ts-set | 8692123720 | ✅ polling |
| 13 | @MY_NFT_SHOP_bot | slh-nft-shop | 8394483424 | ✅ polling |
| 14 | @beynonibank_bot | slh-beynonibank | 8384883433 | ✅ polling |
| 15 | (TON MNH) | slh-ton-mnh | 8508943909 | ✅ polling |
| 16 | (Campaign) | slh-campaign | 8075933581 | ✅ polling |
| 17 | @Buy_My_Shop_bot | slh-botshop | 8288632241 | ✅ polling |
| 18 | (NFTY) | slh-nifty-new | 7998856873 | ✅ polling |

### 🔴 בוטים עם בעיות (4)

| בעיה | פרטים |
|------|--------|
| **slh-expertnet = @My_crazy_panel_bot** | ה-container `slh-expertnet` מריץ את `@My_crazy_panel_bot` (id=8238076648) במקום @SLH_AIR_bot או בוט ExpertNet ייעודי. **TOKEN_AUDIT.md** (2026-04-07) מציין ש-EXPERTNET_BOT_TOKEN = AIRDROP_BOT_TOKEN — אבל עכשיו נראה שה-token הוחלף ל-CRAZY_PANEL_TOKEN. בעיה: אין בוט ExpertNet ייעודי רץ. |
| **slh-factory polling errors** | הבוט רץ אבל יש היסטוריית שגיאות DNS ו-"All connection attempts failed". Uvicorn עובד אבל polling ל-Telegram לא יציב. בוט: `@Osifs_Factory_bot`. |
| **slh_factory DB ריק** | אין טבלאות ב-PostgreSQL slh_factory. הבוט לא יצר schema או שהוא לא משתמש ב-DB הנכון. |
| **slh_guardian DB ריק** | אין טבלאות. Guardian בוט רץ אבל לא מייצר נתונים ב-DB. |

### 🟡 קונפליקטים ידועים (מ-TOKEN_AUDIT.md)

**1. EXPERTNET vs AIRDROP**
```
EXPERTNET_BOT_TOKEN ↔ AIRDROP_BOT_TOKEN
→ שניהם היו של @SLH_AIR_bot (8530795944)
→ גורם לקונפליקט 409 אם שניהם polling
→ נראה ש-EXPERTNET הוחלף ל-@My_crazy_panel_bot כתיקון
→ המשמעות: אין בוט ExpertNet ייעודי לציקה! (הבוט של זביקה)
```

**2. SELHA vs USERINFO**
```
SLH_SELHA_TOKEN = 8225059465
→ נמצא גם ב-selha-bot וגם ב-userinfo-bot
→ פתרון נוכחי: slh-userinfo פשוט לא רץ
→ המשמעות: אין @SLH_UserInfo_bot זמין
```

---

## 🔑 Tokens & Environment Variables

**קובץ `.env`:** `D:\SLH_ECOSYSTEM\.env` (60 משתנים, 25 טוקני בוט)

### SLH BEP-20 Token (BSC)
- **Contract:** `0xACb0A09414CEA1C879c67bB7A877E4e19480f022`
- **Chain:** Binance Smart Chain (56)
- **Decimals:** 15
- **Price:** 444 ILS / $121.64 (נתון sourced מ-API)
- **RPC:** `https://bsc-dataseed.binance.org/`

### TON Wallet
- **Address:** `UQCr743gEr_nqV_0SBkSp3CtYS_15R3LDLBvLmKeEv7XdGvp`
- **Network:** TON Mainnet
- **API:** toncenter.com/api/v2

### Railway Cloud
- **API URL:** `https://slh-api-production.up.railway.app` ✅
- **PostgreSQL:** `junction.proxy.rlwy.net:17913/railway`
- **Redis:** `junction.proxy.rlwy.net:12921`

### 🚨 SECURITY (מ-SECURITY_TOKEN_ROTATION.md)
**דחוף:** כל 20 הטוקנים היו exposed ב-chat של Claude. צריך לבצע rotation דרך BotFather. **אף טוקן עדיין לא הוחלף!**

---

## 📁 מבנה ספריות מרכזי

```
D:\SLH_ECOSYSTEM\
├─ docker-compose.yml          ← 23 services מוגדרים
├─ .env                        ← 60 vars, 25 tokens
├─ init-db.sql
├─ start.ps1 / stop.ps1
├─ dockerfiles/                ← 16 Dockerfiles
├─ api/                        ← FastAPI 3,054 lines
│   ├─ main.py                 ← 55 endpoints
│   ├─ routes/ai_chat.py
│   ├─ requirements.txt
│   └─ railway.json
├─ website/                    ← GitHub Pages
│   ├─ 22 HTML pages
│   ├─ js/web3.js              ← חדש, לא committed!
│   ├─ css/, img/, assets/
│   └─ CNAME → slh-nft.com
├─ shared/                     ← wallet_engine, slh_payments, bot_template
├─ airdrop/                    ← @SLH_AIR_bot (HUB מרכזי)
├─ expertnet-bot/              ← ExpertNet (running @My_crazy_panel_bot currently)
├─ botshop/                    ← @Buy_My_Shop_bot
├─ wallet/                     ← @SLH_Wallet_bot
├─ factory/                    ← @Osifs_Factory_bot (polling errors)
├─ fun/                        ← @SLH_community_bot
├─ nfty-bot/                   ← NFTY Madness (old location)
├─ tonmnh-bot/, userinfo-bot/, osif-shop/, campaign-bot/
├─ ops/                        ← תיעוד + scripts
│   ├─ WORK_PLAN_2026-04.md    ← ROADMAP אפריל
│   ├─ NEXT_SESSION_PLAN.md    ← משימות מיידיות
│   ├─ DAILY_BLOG.md           ← יומן פיתוח
│   ├─ TASK_BOARD.md           ← משימות פעילות
│   ├─ SECURITY_TOKEN_ROTATION.md ← דחוף
│   ├─ REBOOT_GUIDE.md
│   ├─ ARCHITECTURE.md
│   ├─ PROJECT_BRIEF.md
│   ├─ TOKENOMICS.md
│   ├─ WEB3_MARKETPLACE_PLAN.md
│   ├─ WEB3_WALLET_PLAN.md
│   ├─ TEST_GUIDE_2026-04-09.md
│   ├─ migrations/20260409_web3_wallet.sql
│   ├─ slh-startup.bat / slh-shutdown.bat / slh-backup.bat
└─ backups/                    ← PG backups ישנים
```

---

## ✅ מה עובד מצוין (GREEN)

1. **Infrastructure** — PostgreSQL + Redis יציבים
2. **Railway API** — 55 endpoints חיים, DB connected, prices מתעדכנים
3. **Website slh-nft.com** — 22 HTML pages, PWA, Service Worker, i18n (5 שפות)
4. **Analytics** — 16,537 events tracked, 1,237 views היום
5. **Wallet Engine** — @SLH_AIR_bot מחובר ל-DB + Redis + BSC + TON
6. **Community** — posts/likes/comments דרך Railway API (10 posts)
7. **Staking Plans** — 4 plans, 10 TON staked (test)
8. **Referral System** — 10 generations, leaderboard עובד
9. **CoinGecko Proxy** — מחירי 7 מטבעות חיים (BTC, ETH, TON, BNB וכו')
10. **Admin Dashboard** — endpoint מחזיר נתונים אמיתיים
11. **18/22 Telegram Bots** — רצים ותקשורת תקינה עם Telegram
12. **Payment Gate** — shared/slh_payments עובד כ-module משותף
13. **Git Integration** — API + Website עם remotes תקינים

---

## 🔴 מה לא עובד (צריך תיקון היום)

### 🚨 קריטי (P0)
1. **slh-expertnet container מריץ את הבוט הלא נכון**
   - currently: @My_crazy_panel_bot
   - expected: @SLH_ExpertNet_bot או דומה (של זביקה)
   - **פעולה נדרשת:** ליצור בוט חדש דרך BotFather לExpertNet וללבדכן את `.env`

2. **slh-factory — polling errors חוזרים**
   - Uvicorn רץ אבל Telegram polling לא יציב
   - DNS resolution failures בעבר
   - **פעולה נדרשת:** `docker compose restart factory-bot` ובדיקת logs

3. **slh_factory ו-slh_guardian DBs ריקים**
   - אין schema initialization
   - **פעולה נדרשת:** להריץ alembic migrations או init scripts לכל אחד

4. **Token Rotation — 20 טוקנים exposed**
   - מ-SECURITY_TOKEN_ROTATION.md: לא הוחלף עדיין
   - **פעולה נדרשת:** rotation דרך @BotFather (User action only)

### ⚠️ חשוב (P1)
5. **Selha/UserInfo token conflict** — slh-userinfo לא רץ כי משתף טוקן
   - **פעולה נדרשת:** ליצור @SLH_UserInfo_bot ייעודי

6. **website/js/web3.js לא committed** — קובץ חדש שלא בגיט
   - **פעולה נדרשת:** `git add js/web3.js` + commit

7. **ecosystem git: ops/DAILY_BLOG.md + ops/TEST_GUIDE_2026-04-09.md staged אבל לא committed**
   - **פעולה נדרשת:** commit + push

8. **Academia Bot token** — לפי ROADMAP היה expired, עכשיו רץ — לאמת ב-BotFather

9. **wallet.html — mock data** (מ-STATUS_REPORT) — עדיין משתמש בנתונים מדומים
   - **פעולה נדרשת:** לחבר ל-Railway /api/wallet/{user_id}/balances

10. **Guardian GitHub remote 404** — מ-ROADMAP

### 📝 בינוני (P2)
11. **slh_bus/ module** — קיים כ-directory אבל לא מיושם (event bus בין בוטים)
12. **Centralized logging** — כל בוט logs נפרד
13. **Automated PostgreSQL backups** — אין cron schedule
14. **Webhook mode** — כל הבוטים polling, לא webhooks (Cloudflare Tunnel לא מוגדר)
15. **Cross-bot SSO** — אין unified user DB
16. **TonConnect** — רק EVM chains ב-web3.js, TON לא מחובר ל-dashboard
17. **Facebook/YouTube feed integration** — חסר Facebook App
18. **Marketplace ריק** — 0 items (infra מוכן, צריך content)
19. **No courses** — Sprint 4 goal, 0 courses בינתיים
20. **ExpertNet Zvika spec** — לא מיושם (ambassador bot per memory)

---

## 📊 מדדים נוכחיים

| מדד | ערך נוכחי | יעד 2 שבועות | יעד 4 שבועות |
|-----|-----------|---------------|----------------|
| Registered users | 7 (local) / ~7 (Railway) | 100 | 300 |
| Bots operational | 18/22 (81%) | 23/23 | 23/23 |
| P0 bugs | 4 | 0 | 0 |
| Languages supported | 5 (UI) / 1 (bots) | 5 (all bots) | 5 (all bots) |
| Courses for sale | 0 | 1 | 5 |
| Analytics events/day | 1,237 | 5,000 | 15,000 |
| Total SLH staked | 10 TON (test) | 50 TON | 200 TON |
| Memory usage | ~1.7 GB / 3.8 GB | ~2 GB | ~2.5 GB |

---

## 🎯 תכנית עבודה מומלצת להיום (2026-04-10)

### Morning (2-3 שעות) — Critical Fixes
1. **רישום git + push**
   ```bash
   cd D:\SLH_ECOSYSTEM/website
   git add js/web3.js community.html dashboard.html invite.html
   git commit -m "feat: Web3 integration + community updates"
   git push origin main

   cd D:\SLH_ECOSYSTEM
   git commit -m "docs: daily blog + test guide 2026-04-09"
   # (DAILY_BLOG + TEST_GUIDE already staged)
   ```

2. **תקן slh-factory**
   - `docker compose restart factory-bot`
   - `docker logs slh-factory -f` לאמת polling
   - אם לא עוזר — לבדוק `.env` ו-Dockerfile.factory

3. **פתור ExpertNet token conflict**
   - ב-BotFather: יצירת בוט חדש @SLH_Expert_bot או @SLH_Zvika_bot
   - לעדכן `EXPERTNET_BOT_TOKEN=...` ב-`.env`
   - `docker compose restart expertnet-bot`

4. **Initialize factory + guardian DBs**
   - לרוץ migrations של factory (alembic)
   - ל-guardian: init schema

### Midday (1-2 שעות) — Work Plan Tasks
5. **Sprint 1 P0 remaining:**
   - Auto-registration: בוט `/start` → POST `/api/auth/telegram-sync`
   - (לא עובד עדיין — יש `/api/auth/bot-sync` אבל לא מופעל)

6. **MetaMask Web3 integration live testing:**
   - לאמת ש-web3.js עובד בדשבורד ובוואלט
   - לבדוק balance reads מ-BSC

### Afternoon (2 שעות) — Optional
7. **wallet.html — החלפת mock data לAPI אמיתי**
8. **Token rotation** — אם יש זמן להתעסק עם BotFather
9. **פרסום daily-blog** entry חדש ליום 2026-04-10

---

## 🔗 Quick Reference

### Live URLs
- **Website:** https://slh-nft.com
- **API:** https://slh-api-production.up.railway.app
- **Health:** https://slh-api-production.up.railway.app/api/health
- **Docs:** https://slh-api-production.up.railway.app/docs

### מעקב אחרי Logs
```bash
# בוט ספציפי
docker logs slh-factory -f
docker logs slh-airdrop -f

# כל הקונטיינרים
docker compose -f D:\SLH_ECOSYSTEM\docker-compose.yml ps

# סטטוס DB
docker exec slh-postgres psql -U postgres -d slh_main -c "SELECT COUNT(*) FROM users;"
```

### Restart פקודות
```bash
cd D:\SLH_ECOSYSTEM

# בוט בודד
docker compose restart factory-bot
docker compose restart expertnet-bot

# הכל
docker compose down && docker compose up -d
.\start.ps1 -Service all
```

### API Smoke Tests
```bash
curl https://slh-api-production.up.railway.app/api/health
curl https://slh-api-production.up.railway.app/api/stats
curl https://slh-api-production.up.railway.app/api/prices
curl https://slh-api-production.up.railway.app/api/user/224223270
```

---

## 📝 נושאים פתוחים (User Action Required)

מתוך `WORK_PLAN_2026-04.md` — דברים שרק אתה (Osif) יכול לעשות:

1. 🔑 **Rotate 20 bot tokens** דרך @BotFather (SECURITY_TOKEN_ROTATION.md)
2. 🚂 **Railway CLI link** — `railway link` בתיקיית api/
3. 📱 **Create Facebook App** ב-developers.facebook.com
4. 💻 **Windows startup shortcut** לslh-startup.bat
5. 🔌 **Reconnect ESP32** לSLH_Ledger_bot integration
6. ✅ **Approve first test payments** דרך admin panel

---

## ❓ שאלות פתוחות (מ-WORK_PLAN)

- מה @Slh_selha_bot צריך לעשות? (כרגע ללא ייעוד)
- @Chance_Pais_bot להפוך ל-Gambling Recovery Bot? (המענה שלך היה "pivot")
- איזה קורס להיות ה-sample הראשון?
- Facebook page IDs להצגה בדשבורד?
- YouTube channel IDs להצגה בדשבורד?

---

**דוח נוצר על ידי Claude Opus 4.6 | 2026-04-10**
**אין שינויים בוצעו — סריקה בלבד**
