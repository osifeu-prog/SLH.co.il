# SLH Ecosystem — פרומפט Handoff מלא | 13 אפריל 2026 ערב
## העתק את כל הקובץ הזה כהודעה ראשונה לסשן חדש

---

אתה ממשיך פיתוח של **SLH Spark Ecosystem** — פלטפורמת קריפטו ישראלית עם 25+ בוטי טלגרם, אתר עם 43 דפים, API עם 117 endpoints, ו-Pool חי על PancakeSwap.

**חובה לקרוא לפני שתתחיל:**
- `D:\SLH_ECOSYSTEM\CLAUDE.md` — הוראות עבודה + מבנה פרויקט
- `D:\SLH_ECOSYSTEM\ops\NEXT_SESSION_PLAN.md` — תוכנית מלאה
- `D:\SLH_ECOSYSTEM\ops\FULL_PROJECT_REPORT_20260413.md` — דוח 114 endpoints

---

## 1. מי אני

- **Osif Kaufman Ungar** (@osifeu_prog, Telegram ID: 224223270)
- מפתח יחיד, דובר עברית, פרפקציוניסט
- **רוצה פעולה ישירה** — לא הסברים ארוכים. בנה, תקן, דחוף.
- "כן לכל ההצעות" = תמשיך עם הכל
- 10+ משקיעים מוסדיים מתעניינים (1M+ ש"ח כל אחד)

---

## 2. מצב המערכת הנוכחי (13/04/2026 20:30)

### תשתית
| רכיב | סטטוס | פרטים |
|------|--------|-------|
| **Railway API** | ✅ חי | https://slh-api-production.up.railway.app · v1.1.0 · 117 endpoints · DB connected |
| **GitHub Pages** | ✅ חי | https://slh-nft.com · 43 דפים |
| **Docker** | ✅ 24 קונטיינרים | כולם Up 2+ ימים (slh-osif-shop רענן 25 דקות) |
| **PostgreSQL** | ✅ | Railway + Local port 5432 |
| **Redis** | ✅ | slh_redis + redis-nifty |
| **PancakeSwap Pool** | ✅ חי | 0xacea26b6e132cd45f2b8a4754170d4d0d3b8bbee |

### נתונים חיים מה-API
```
health: ok, db: connected, version: 1.1.0
users: 9 registered, admin=osifeu_prog (224223270)
balances: SLH=199,788.32, ZVK=501.0, TON_available=0
beta coupon: GENESIS49 — 6 used, 43 remaining out of 49
marketplace: 0 items, 0 orders
registration price: 22.221 ILS (~$6.09)
SLH price: 444 ILS ($121.64)
genesis contributors: 5 verified, 0.08 BNB raised
```

---

## 3. מה בוצע בסשן הנוכחי (Session 11 — 13/04/2026 ערב)

### שינויים ב-API (api/main.py) — 943 שורות חדשות, **לא נדחפו עדיין!**

| # | מה | פרטים |
|---|---|-------|
| 1 | **Beta Coupon System** | טבלאות `beta_coupons` + `beta_redemptions`, עמודות `beta_user`, `beta_coupon_code`, `beta_nft_number` ב-`web_users`. קופון `GENESIS49` נוצר אוטומטית ב-startup (49 מקומות, 100 SLH בונוס) |
| 2 | **`POST /api/registration/unlock`** | Endpoint חדש שעובד **בלי JWT** (עיקרי!). תומך ב-3 שיטות: `payment_proof` (TX hash → pending_review), `coupon` (GENESIS49 → instant unlock + 100 SLH + NFT Genesis #N), `admin` (admin_key → instant). מוריד `used_count` אטומית, מונע כפל redemption |
| 3 | **`GET /api/beta/status`** | ציבורי — מחזיר כמה מקומות נותרו בכל קופון פעיל |
| 4 | **`POST /api/beta/create-coupon`** | Admin only — יצירת קופון חדש עם code, max_uses, slh_bonus |

### שינויים באתר (website/) — **לא נדחפו עדיין!**

| # | קובץ | מה שונה |
|---|------|---------|
| 5 | **dashboard.html** | פאנל Genesis 49 חדש מתחת לטופס הרשמה — input קוד + כפתור "🔑 הזן קוד Genesis" + status indicator. `submitRegistration()` שוכתב לחלוטין — קורא ל-`/api/registration/unlock` (ללא JWT!) במקום ל-`/api/registration/submit-proof` (שדרש JWT). `initiateRegistration()` עכשיו בודק `/api/beta/status` + `/api/user/full/{id}`. הוספת `redeemBetaCoupon()` + `showRegCouponStatus()` |
| 6 | **community.html** | Paywall הוחלף — במקום "🔒 תכונה זו דורשת הרשמה" + מחיר ₪44.4 הישן, עכשיו יש: banner Genesis 49 עם input קוד ישירות בדף, demo mode (יכול לקרוא/ללייק אבל לא לפרסם), מחיר עודכן ל-₪22.221, הוספת `handleCommunityCoupon()` + `loadCommunityBetaStatus()` |
| 7 | **invite.html** | banner Genesis 49 חדש עם כמות נותרת דינמית מ-API, כפתור "📋 העתק קוד", `loadBetaRemaining()` + `copyCouponCode()` |
| 8 | **11 HTML pages** | cache-bust bump v=20260409d (sessions קודמים — כבר נדחף) |

### שינויים בבוט (airdrop/app/bot_server.py) — **הופעל בקונטיינר בלבד!**

| # | מה | פרטים |
|---|---|-------|
| 9 | **Fix payment false-positive** | `handle_text()` שוכתב — דורש state machine (`awaiting_username` → `awaiting_payment`), TX hash מזוהה רק כ-regex מדויק (BSC 0x+64hex / TON base64-44), כל שאר הטקסט → "🤖 לא הבנתי" |
| 10 | **Auto-sync /start** | כל `/start` קורא ל-`POST /api/auth/bot-sync` עם secret — יוצר/מעדכן משתמש ב-DB, מחזיר `login_url` אישי |
| 11 | **Branding חדש** | ASCII header מקצועי עם `<code>` blocks, כפתור inline keyboard "🌐 היכנס לאתר האישי" + 4 כפתורי URL (חנות/בלוג/הזמן חברים/מדריכים) |
| 12 | **⚠️ לא נשמר ל-git!** | `docker cp` + `docker restart` בלבד. אם הקונטיינר נבנה מחדש, השינויים יאבדו. צריך לדחוף לרפו ולעדכן Dockerfile/compose |

---

## 4. מה פרוס בפרודקשן (חי עכשיו)

### API (Railway) — commits שנדחפו:
```
bfe75e0 feat: auto-rewards on contributions + P2P v2 with JWT auth
2189c40 security: add auth to tokenomics burn/reserves/transfer (SEC-2)
79b1c9d fix+feat: member card PNG route + personal card broadcast
04e45c1 feat(api): Member Card system — identity card per user
dccda77 feat(api): REP reputation system — personal score per member
b66be23 feat(og): rich visual OG images with gradients, circles, grid patterns
e9025ad fix(broadcast): accept admin panel passwords for broadcast + launch verify
efe99a7 security: fix 3 critical + 3 high findings from overnight audit
f391532 feat: Genesis Launch backend + dynamic OG image generator + share tracking
718b029 feat(api): broadcast system + BROADCAST_BOT_TOKEN
a4ae608 feat(api): BitQuery fallback for BSC holders (free 10k/month)
a8eff99 feat: tokenomics engine + strategy engine + backtest simulation
```

### Website (GitHub Pages) — commits שנדחפו:
```
9dec168 fix: remove ALL demo/fake data from community page
84b47e0 feat: AI trading signals + neural network insights on trade page
37bf732 feat: full Day 2 content — muscles, weekly table, links, resources
bf09ae7 feat: dynamic team section from API + Genesis contributors
947e58f feat: 21-day challenge Day 2 — handstand guide + blog update
a07fa7f feat: add About & Transparency page with team, verification, disclaimers
e3230f9 fix: OG image points to liquidity.png not earn.png
b24c4ca feat: major upgrade to liquidity page + add to sitemap & nav
0bb143d feat: add liquidity education page with staking guide + roadmap
bfd8d1d feat: add 21-Day Challenge + Healing Vision to main navigation
```

### Endpoints חיים ומאומתים (38 GET + 79 POST = 117 total)
- Full inventory: `D:\SLH_ECOSYSTEM\ops\FULL_PROJECT_REPORT_20260413.md`
- Swagger: https://slh-api-production.up.railway.app/docs

---

## 5. מה שבור / חסר (Known Bugs)

### 🔴 קריטי — חוסם גיוס
| # | בעיה | פרטים |
|---|------|-------|
| 1 | **api/main.py לא מסונכרן עם root main.py** | Railway בונה מ-ROOT `main.py` (7404 שורות). `api/main.py` יש 7475 שורות + שינויים חדשים (beta coupon, unlock endpoint). **חובה:** `cp api/main.py main.py` לפני push! |
| 2 | **שינויי API לא נדחפו** | 943 שורות חדשות (beta system + unlock) קיימות רק מקומית. Railway רץ על גרסה ישנה. |
| 3 | **שינויי website לא נדחפו** | dashboard.html + community.html + invite.html שונו אבל לא committed |
| 4 | **שינויי bot לא שמורים ב-git** | `bot_server.py` שונה רק בקונטיינר (docker cp). rebuild = איבוד שינויים |
| 5 | **JWT_SECRET ריק ב-Railway** | כל endpoint שדורש JWT (auth/telegram, registration/initiate, registration/submit-proof) נכשל. ה-unlock endpoint החדש עוקף זאת (לא דורש JWT) |
| 6 | **Admin passwords ב-HTML** | `broadcast-composer.html` שורה 201 + `ecosystem-guide.html` שורה 290 — 4 סיסמאות חשופות: slh2026admin, slh_admin_2026, slh-spark-admin, slh-institutional |
| 7 | **ארנק בבוט = RAM בלבד** | `_user_data` dict (199,788 SLH) לא מסונכרן עם DB (שמראה SLH=199788.32 דרך API). אם הבוט מתרסט, הנתונים שונים |

### 🟠 חשוב
| # | בעיה | פרטים |
|---|------|-------|
| 8 | **NFTY bot שבור** | מציג garbled unicode + merged עם marketplace bot. ראה NEXT_SESSION_PLAN.md סעיף P0 |
| 9 | **community.html עדיין מציג "₪44.4"** | בטקסט hardcoded בתוך `renderAuthSection()` — תוקן מקומית אבל לא נדחף |
| 10 | **invite.html ה-ref link מראה "?ref=User"** | כי ה-`localStorage.slh_user` שומר `first_name` כ-"User" כש-login דרך `?uid=` בלי name param. צריך שילוב עם username או telegram_id |
| 11 | **blockchain.html "Loading blockchain data..."** | טעינת TX נתקעת — BSCScan free API rate limited. BitQuery fallback קיים ב-API אבל הדף לא משתמש בו |

### 🟡 שיפורים
| # | בעיה |
|---|------|
| 12 | Theme switcher חסר ב-25/43 דפים |
| 13 | i18n חסר ב-27/43 דפים |
| 14 | Webhook migration (polling → webhooks) לא התחיל |
| 15 | 0% test coverage |
| 16 | BOT_SYNC_SECRET = default value |

---

## 6. קבצים עם שינויים לא מחוייבים (uncommitted)

### Website repo (`D:\SLH_ECOSYSTEM\website\`):
```
M admin.html              (478 insertions, 478 deletions — security fixes)
M analytics.html           (26+)
M broadcast-composer.html  (223 changes — password removal)
M morning-checklist.html   (209 changes)
M morning-handoff.html     (193 changes)
M ops-dashboard.html       (58 changes)
M ops-report-20260411.html (381 changes)
M partner-launch-invite.html (121 changes)
M rotate.html              (84 changes)
M system-health.html       (61 changes)
M test-bots.html           (114 changes)
```
**+ שינויים שעדיין לא staged:** dashboard.html, community.html, invite.html

### API repo (`D:\SLH_ECOSYSTEM\api\`):
```
M main.py  (943 insertions, 178 deletions)
```
**ROOT main.py NOT SYNCED** — חובה: `cp api/main.py main.py`

---

## 7. משימות הבאות לפי עדיפות

### 🔴 מיידי — לפני כל דבר
1. **`cp api/main.py main.py`** ← **בלי זה Railway לא יקבל את ה-beta coupon system!**
2. **Commit + push API** (master branch) — beta coupon + unlock + auto-rewards
3. **Commit + push Website** (main branch) — dashboard genesis panel + community fix + invite upgrade
4. **Test:** `curl -X POST .../api/registration/unlock -d '{"user_id":224223270,"method":"admin","admin_key":"slh2026admin"}'` — לוודא שהאדמין מקבל גישה מלאה
5. **Test:** `curl -X POST .../api/registration/unlock -d '{"user_id":TEST_ID,"method":"coupon","coupon_code":"GENESIS49"}'` — לוודא שקופון עובד
6. **הסר סיסמאות מ-HTML** — broadcast-composer.html + ecosystem-guide.html

### 🟠 היום
7. **שמור שינויי bot ל-git** — `airdrop/app/bot_server.py` (handle_text rewrite, auto-sync, branding)
8. **admin.html** — הוסף UI לניהול קופונים + unlock ידני
9. **Bot: /coupon command** — משתמש שולח `/coupon GENESIS49` ומקבל גישה מלאה
10. **invite.html: OG meta tags** — שהשיתופים ברשתות יציגו תמונה יפה (og:image)

### 🟡 השבוע
11. **איחוד יתרות RAM↔DB** — הבוט כותב ל-`_user_data` dict, האתר קורא מ-DB. צריך migration
12. **NFTY bot fix** — broken encoding + wrong bot code loaded
13. **P2P marketplace frontend** — endpoints כבר קיימים (`/api/p2p/v2/*`)
14. **Community image upload** — תמונות לפוסטים (backend קיים, frontend חלקי)
15. **PancakeSwap pool guide** — מדריך צעד-אחר-צעד למשתמש
16. **Railway env vars** — JWT_SECRET, ADMIN_API_KEYS, BOT_SYNC_SECRET

---

## 8. הערות טכניות חשובות

### Git Repos & Deploy
```
Website: github.com/osifeu-prog/osifeu-prog.github.io (branch: main) → slh-nft.com
API:     github.com/osifeu-prog/slh-api (branch: master) → Railway auto-deploy
CRITICAL: Railway builds from ROOT main.py, NOT api/main.py!
Always: cp api/main.py main.py && git add main.py api/main.py
```

### Addresses
```
SLH Contract:     0xACb0A09414CEA1C879c67bB7A877E4e19480f022 (BSC BEP-20, 15 decimals)
PancakeSwap Pool: 0xacea26b6e132cd45f2b8a4754170d4d0d3b8bbee
Genesis Wallet:   0xd061de73B06d5E91bfA46b35EfB7B08b16903da4
Main MetaMask:    0xD0617B54FB4b6b66307846f217b4D685800E3dA4 (holds 199K SLH)
TON Wallet:       UQCr743gEr_nqV_0SBkSp3CtYS_15R3LDLBvLmKeEv7XdGvp
```

### 5-Token Economy
```
SLH — Premium/governance, target 444 ILS, live on BSC + PancakeSwap
MNH — Stablecoin pegged 1:1 to ILS (internal)
ZVK — Activity rewards, ~4.4 ILS (100 ZVK = 1 SLH)
REP — Reputation score 0-1000+ (internal)
ZUZ — Anti-fraud "Mark of Cain", auto-ban at 100 (Guardian system)
```

### Tech Stack
```
Backend: FastAPI (Python 3.11) on Railway, asyncpg → PostgreSQL 15
Frontend: 43 static HTML pages on GitHub Pages, no framework
Bots: 25 containers (aiogram 3.x / python-telegram-bot), Docker Compose
JS: shared.js (nav+auth+i18n+themes), translations.js (5 langs), web3.js (ethers v6)
CSS: shared.css (7 themes: dark/terminal/crypto/cyberpunk/ocean/sunset/light)
AI: 4 LLM providers (Groq→Gemini→Together→OpenAI) in ai-assistant.js
```

### Admin Auth
```
Admin Telegram ID: 224223270
Admin API keys: slh2026admin (primary), slh_admin_2026, slh-spark-admin
Header: X-Admin-Key
localStorage: slh_admin_password
```

### Key People
```
Osif — Owner/developer (224223270)
Zohar Shefa Dror — Active contributor, QA
Tzvika — Co-founder, crypto trader
Eli — Contributor
Yakir Lisha — Contributor
Total Genesis: 0.08 BNB raised from 5 contributors
```

---

## 9. פקודות בדיקה מיידיות

```bash
# Health check
curl -s https://slh-api-production.up.railway.app/api/health

# Beta coupon status
curl -s https://slh-api-production.up.railway.app/api/beta/status

# Full user data
curl -s https://slh-api-production.up.railway.app/api/user/full/224223270

# Docker status
docker ps --format "table {{.Names}}\t{{.Status}}" | head -25

# Git status
cd D:/SLH_ECOSYSTEM/website && git status --short
cd D:/SLH_ECOSYSTEM/api && git status --short

# Sync check (MUST be synced before push!)
diff D:/SLH_ECOSYSTEM/api/main.py D:/SLH_ECOSYSTEM/main.py
```

---

## 10. כללי עבודה

- **עברית ב-UI, אנגלית בקוד/commits**
- **אל תמעיט בהיקף** — 25 בוטים, 43 דפים, 117 endpoints, 5 טוקנים. כל אלה חשובים.
- **נתונים אמיתיים בלבד** — אין mock data בפרודקשן. `[DEMO]` tag אם חובה.
- **אל תשנה כתובות ארנק** בלי לשאול
- **עדכן handoff** בסוף הסשן: `ops/SESSION_HANDOFF_*.md`
- **CLAUDE.md** — מכיל את כל הכללים. קרא אותו ראשון.
