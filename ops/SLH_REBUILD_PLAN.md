# SLH Ecosystem — תוכנית הרמה מלאה
**נוצר:** 04/05/2026 | **לקוח:** Osif Kaufman Ungar (@osifeu_prog)  
**בסיס:** סריקת 3,581 קבצים ב-3 ריפוזים + לוגים + handoff docs

---

## 📊 מה נסרק — ממצאים

### 3 ריפוזים / 3 שכבות
| ריפו | תוכן | בעיה |
|------|------|------|
| `slh-api` (master) | FastAPI 11,780 שורות · 33 routes · 17 shared · 26 Docker services | **זהה ל-SLH.co.il** |
| `SLH.co.il` (main) | **אותו קוד בדיוק** כמו slh-api | כפילות מיותרת |
| `osifeu-prog.github.io` (main) | 164 דפי HTML · JS · CSS | theme 22% · i18n 40% |

### 26 שירותי Docker שזוהו
`admin-bot · academia-bot · airdrop · wallet · guardian · g4mebot · botshop · campaign-bot · match-bot · nfty-bot · expertnet-bot · school · fun · slh-claude-bot · slh-core-bot · slh-guardian-bot · slh-botshop · slh-test-bot · tonmnh-bot · userinfo-bot · wellness-bot · factory · postgres · redis + 2 נוספים`

### 33 Route Modules
`treasury · payments_auto · payments_monitor · blockchain_verify · ai_chat · agent_hub · courses · dating · community_plus · creator_economy · investor_engine · ambassador_crm · bot_registry · admin_rotate · rotation_pipeline · pancakeswap_tracker · arkham_bridge · esp_events · device_inventory · system_audit · system_status · broadcast · wellness · therapists · tasks · sudoku · whatsapp · aic_tokens · love_tokens · academia_ugc · campaign_admin · railway_client · ...`

### 🔴 קריטי — בעיות שזוהו
1. **כפילות ריפוזים** — `slh-api` ו-`SLH.co.il` אותו קוד, Railway build מבלבל
2. **Monolith** — `api/main.py` = 11,780 שורות. FastAPI לא deployed בפועל (Railway רץ `http.server`)
3. **סודות חשופים** — JWT_SECRET ריק, ADMIN_API_KEYS=DEFAULT, 30 bot tokens לא מוחלפו
4. **102 קבצי .bak** פזורים בכל הפרויקט
5. **305 קבצי ops** — ידע חשוב אבוד בתוך טקסט לא מובנה
6. **Bot registry** — `/registry` מחזיר `Bots: 0` (3/5/2026)
7. **Polling בלבד** — כל 26 בוטים polling, אין webhooks, ביצועים גרועים

---

## 🏗️ ארכיטקטורה מוצעת — מבנה חדש

```
SLH_ECOSYSTEM/                      ← ריפו יחיד (slh-core)
│
├── 📁 api/                          ← FastAPI Backend
│   ├── main.py                      ← ~200 שורות (init בלבד)
│   ├── routes/                      ← 33 route files (כבר קיים, לנקות)
│   ├── shared/                      ← shared modules (כבר קיים)
│   ├── core/                        ← engine · brain · observer
│   └── config.py                    ← env vars centralized
│
├── 📁 bots/                         ← כל הבוטים (מאוחד)
│   ├── _shared/                     ← bot_template · payments · guardian
│   ├── admin/                       ← @MY_SUPER_ADMIN_bot
│   ├── academia/                    ← @SLH_Academia_bot
│   ├── airdrop/                     ← @AIRDROP_bot
│   ├── wallet/                      ← @SLH_Wallet_bot
│   ├── guardian/                    ← anti-fraud system
│   ├── g4me/                        ← gaming + dating
│   ├── tonmnh/                      ← TON/MNH marketplace
│   ├── wellness/                    ← wellness scheduler
│   └── [others...]
│
├── 📁 frontend/                     ← ריפו נפרד (GitHub Pages)
│   ├── css/
│   │   ├── slh-neural.css           ← design system (קיים)
│   │   └── components/              ← tokens, cards, nav
│   ├── js/
│   │   ├── shared.js                ← nav · themes (קיים)
│   │   ├── translations.js          ← i18n (קיים)
│   │   └── api-client.js            ← חדש: wrapper ל-API calls
│   ├── pages/                       ← 164 דפים מאורגנים
│   │   ├── public/                  ← index · ido · whitepaper · join
│   │   ├── user/                    ← dashboard · wallet · profile
│   │   ├── academy/                 ← courses · challenges
│   │   ├── community/               ← feed · leaderboard
│   │   └── admin/                   ← ops panel
│   └── assets/
│
├── 📁 infra/                        ← DevOps
│   ├── docker-compose.yml           ← 26 services (לנקות)
│   ├── docker-compose.dev.yml       ← dev override
│   ├── railway.json                 ← Railway config
│   └── .github/workflows/           ← CI/CD
│
├── 📁 docs/                         ← תיעוד (מחליף 305 קבצי ops)
│   ├── ARCHITECTURE.md
│   ├── API_REFERENCE.md
│   ├── BOTS_GUIDE.md
│   ├── SECURITY.md
│   └── CHANGELOG.md
│
├── 📁 archive/                      ← גרייבארד (לא נמחק!)
│   ├── ops_snapshots/               ← 305 קבצי ops ← ZIP
│   ├── bak_files/                   ← 102 .bak files ← ZIP
│   └── legacy/                      ← SLH.co.il duplicate
│
├── CLAUDE.md                        ← הוראות לסוכן AI (לעדכן)
├── .env.example                     ← template ללא סודות
└── README.md
```

---

## 🗓️ שלב 0 — יציבות (~שבוע)
**מטרה: לא לשבור כלום, רק לייצב ולאבטח**

### 0.1 אבטחה (P0 — לפני כל דבר)
```bash
# Railway env vars — חובה להגדיר:
JWT_SECRET=<generate: openssl rand -hex 32>
ADMIN_API_KEYS=<generate new>
ENCRYPTION_KEY=<generate>
ADMIN_BROADCAST_KEY=<generate>
INITIAL_ADMIN_PASSWORD=<strong password>
INITIAL_TZVIKA_PASSWORD=<strong password>
ADMIN_USER_ID=224223270

# Binance — לסובב מיד:
EXCHANGE_API_KEY=<new key>
EXCHANGE_SECRET=<new secret>

# Telegram — לסובב 30 bot tokens ב-@BotFather
# (נשאר: 1/31 נעשה)
```

### 0.2 ניקוי קבצים
```bash
# יצור archive ושמור:
mkdir -p archive/bak_files
find . -name "*.bak*" -not -path "./archive/*" | xargs -I{} mv {} archive/bak_files/

# zip ops folder:
zip -r archive/ops_snapshots/ops_$(date +%Y%m%d).zip ops/

# הסר .env backups:
rm -f .env.bak .env.backup .env.old
```

### 0.3 bot registry fix
- תקן `init_bot_registry failed: missing pool` — connection pool לא מאותחל
- תקן `init_admin_rotate failed: missing pool`
- תקן `Wellness scheduler TypeError`

### 0.4 Railway
- פרוס FastAPI כ-service חדש `slh-fastapi`
- וודא `cp api/main.py main.py` לפני כל push
- בדוק: `curl https://slh-fastapi-production.up.railway.app/api/health`

---

## 🗓️ שלב 1 — ארגון (~2 שבועות)
**מטרה: מערכת מודולרית, ריפו יחיד, תיעוד נגיש**

### 1.1 איחוד ריפוזים
```
slh-api (master) → ריפו ראשי (שמור)
SLH.co.il → archive (לא מוחק, רק מפסיק לעדכן)
osifeu-prog.github.io → נשאר נפרד (GitHub Pages)
```

**ב-CLAUDE.md:**
```
Single source of truth:
  API: github.com/osifeu-prog/slh-api (master) ← זה הריפו
  SITE: github.com/osifeu-prog/osifeu-prog.github.io (main)
  
SLH.co.il is DEPRECATED — read-only archive
```

### 1.2 פיצול main.py
**כרגע:** 11,780 שורות monolith  
**יעד:** main.py = ~200 שורות + includes

```python
# main.py החדש:
from fastapi import FastAPI
from routes import (
    users, economy, academy, bots_registry,
    blockchain, payments, guardian, esp, wellness,
    admin, investor, community, creator
)

app = FastAPI(title="SLH API", version="2.0.0")

for router in [users.router, economy.router, ...]:
    app.include_router(router, prefix="/api")
```

**routes שצריך להפריד מ-main.py:**
`users · wallets · staking · ido · whitelist · tokens · referrals · leaderboard · notifications · admin · settings`

### 1.3 Bot consolidation
**כרגע:** bot code מפוזר ב-`airdrop/bot/`, `tonmnh-bot/src/`, `wallet/`, `academia-bot/`...  
**יעד:** `bots/_shared/` + `bots/<name>/bot.py` אחיד

Template אחיד לכל בוט:
```python
# bots/_shared/base_bot.py
class SLHBot:
    def __init__(self, token, db_pool, redis, api_url):
        self.dp = Dispatcher()
        self.api = SLHApiClient(api_url)
    
    async def start(self):
        await self._register()  # bot registry
        await self.dp.start_polling(self.bot)
```

### 1.4 תיעוד — 305 ops → 5 מסמכים
```
docs/ARCHITECTURE.md     ← מה קיים, מה עובד, dependencies
docs/API_REFERENCE.md    ← endpoints, auth, examples (auto from OpenAPI)
docs/BOTS_GUIDE.md       ← כל 26 בוטים: מה עושה, איך להפעיל, env vars
docs/SECURITY.md         ← secrets rotation schedule, audit log
docs/CHANGELOG.md        ← per-version changelog
```

**CLAUDE.md** — לעדכן לגרסה 2.0:
- מסיר ref ל-SLH.co.il
- מוסיף bot consolidation rules
- מוסיף "start session" checklist מקוצר (5 שורות)

---

## 🗓️ שלב 2 — חזון (~חודש+)
**מטרה: הפוטנציאל המלא — קהילה, אקדמיה, IDO**

### 2.1 Frontend — slh-neural 100%
- מיגרציה 109 דפים שנותרו ל-`data-theme="neural"`
- i18n מלא (HE/EN/RU/AR/FR) לכל 164 דפים
- `js/api-client.js` — wrapper אחיד לכל API calls (לא hardcoded URLs)
- `tokens.html` — תיקון 404, דף 5 טוקנים פעיל

### 2.2 Webhooks
```python
# docker-compose.yml — כל בוט מקבל WEBHOOK_URL:
environment:
  - WEBHOOK_URL=https://slh-fastapi-production.up.railway.app/webhook/${BOT_NAME}
  - WEBHOOK_SECRET=${WEBHOOK_SECRET}
```
- מיגרציה מ-polling ל-webhooks (חוסך ~50MB RAM, תגובות מהירות יותר)

### 2.3 Academy — מערכת חינוך מלאה
כבר קיים: `courses.py`, `academia-bot/`, `academia_ugc.py`  
להשלים:
- Course builder UI (frontend)
- ZVK rewards per lesson completed
- REP badges per course level
- Quiz engine עם leaderboard

### 2.4 Community Layer
- Activity feed (ZVK rewards per contribution)
- Ambassador program (referral tracking)
- Guardian dashboard (ZUZ anti-fraud visibility)
- Merchant onboarding (tonmnh-bot sandbox קיים)

### 2.5 IDO Readiness
- `tokens.html` תיקון 404
- `bots.html` — מילוי תוכן 25 בוטים
- Supply consistency: קבע מספר אחד (**110,750,000 SLH**) ועדכן בכל הדפים
- Staking disclaimer — asterisk + "variable rate" בכל אזכור
- Whitepaper — תיקון Founder = Osif Kaufman Ungar

---

## 📋 Session Start Checklist — v2

```bash
# 1. API health
curl https://slh-fastapi-production.up.railway.app/api/health

# 2. Bot registry
curl https://slh-fastapi-production.up.railway.app/api/bots/registry

# 3. Git status (שני ריפוזים)
cd D:\SLH_ECOSYSTEM && git status
cd D:\SLH_ECOSYSTEM\website && git status

# 4. Railway logs (tail 20)
railway logs --tail 20

# 5. Check ops/SESSION_HANDOFF_*.md (latest)
```

---

## 🔑 Data Conventions (ללא שינוי)
| Marker | משמעות |
|--------|--------|
| `test_` prefix | נתון ניסוי |
| `[DEMO]` | placeholder |
| `[SEED]` | ערך התחלתי |
| `--` | אין נתון |
| `N/A` | לא רלוונטי |

---

## 🧭 Token Economy — Ground Truth
| Token | Supply | מטרה | סטטוס |
|-------|--------|------|-------|
| SLH | **110,750,000** | Premium / Governance / 444₪ target | Live BSC |
| MNH | unlimited | Stablecoin = 1₪ | Internal |
| ZVK | unlimited | Activity reward ~4.4₪ | Internal |
| REP | 0-1000+ | Reputation score | Internal |
| ZUZ | unlimited | Anti-fraud marker | Guardian system |

**Contract:** `0xACb0A09414CEA1C879c67bB7A877E4e19480f022` (BSC, 15 decimals)

---

## ⚡ פקודות מהירות — Windows (PowerShell)

```powershell
# הפעלת כל המערכת
cd D:\SLH_ECOSYSTEM
docker-compose up -d

# עצירה
docker-compose down

# sync main.py לפני push
cp api\main.py main.py
git add main.py api\main.py
git commit -m "sync: api/main.py → main.py"
git push origin master

# bot logs
docker-compose logs -f admin-bot --tail 50

# DB access
docker exec -it slh-postgres psql -U postgres -d slh_db
```

---

*תוכנית זו נוצרה על ידי סריקה של כל הקוד הקיים. היא שומרת את כל הידע הקיים ב-archive ובונה מעליו — לא מוחקת.*
