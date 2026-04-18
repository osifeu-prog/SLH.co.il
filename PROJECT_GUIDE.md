# 📘 SLH Spark — Project Guide / מדריך פרויקט
**For humans, contributors, and AI agents**
Last updated: 2026-04-18 · Verified against live state

> אם אתה סוכן AI שמקבל פרומפט לתחזק את הפרויקט, **קרא קובץ זה לפני כל דבר אחר**. הוא מכיל את כל מה שצריך לדעת כדי להתחבר, להבין, ולבצע משימות בצורה בטוחה.

---

## 🎯 TL;DR — הפרומפט הקצר ביותר לסוכן AI

```
אתה סוכן שמתחזק את SLH Spark — מערכת בוטים וכלכלת טוקנים בעברית.

מידע בסיסי:
- קוד ראשי: D:\SLH_ECOSYSTEM
- API: https://slh-api-production.up.railway.app (FastAPI, 230 endpoints)
- אתר: https://slh-nft.com (GitHub Pages, 83 pages)
- Git API: github.com/osifeu-prog/slh-api (branch: master)
- Git Site: github.com/osifeu-prog/osifeu-prog.github.io (branch: main)
- Docker: 24 containers רצים (docker compose up -d)

תהליך לכל משימה:
1. קרא PROJECT_GUIDE.md + TASKS_STATUS_2026-04-18.md
2. בצע curl ל-/api/health לוודא API חי
3. עשה את העבודה
4. בדוק בפועל (לא רק קומפילציה) — הרץ curl על endpoint חדש, בדוק שדף עלה ב-200
5. git commit + push (master ל-API, main לאתר)
6. עדכן SESSION_HANDOFF_YYYYMMDD.md

כללים:
- עברית ב-UI, אנגלית בקוד
- לעולם לא הארדקוד סיסמאות ב-HTML (localStorage+API בלבד)
- לעולם לא mock data כנתון אמיתי (השתמש בתג [DEMO] או prefix test_)
- Railway בונה מ-root main.py — תמיד סנכרן עם api/main.py
- לעולם לא לדחוף .env ל-git
```

---

## 📁 מבנה הפרויקט

```
D:\SLH_ECOSYSTEM\              ← שורש הפרויקט
├── main.py                    ← ROOT COPY (Railway בונה מכאן!)
├── api/main.py                ← עותק שני (תמיד לסנכרן: cp api/main.py main.py)
├── routes/                    ← FastAPI routers
├── docker-compose.yml         ← 22 bot services + postgres + redis
├── .env                       ← tokens + API keys (אסור לdחוף ל-git!)
├── .env.example               ← דוגמה ללא סודות (כן ב-git)
├── CLAUDE.md                  ← הנחיות לסוכני AI (הקובץ הזה)
├── PROJECT_GUIDE.md           ← המדריך הזה
├── TASKS_STATUS_2026-04-18.md ← סטטוס משימות מעודכן
├── ROADMAP.md                 ← roadmap ראשי
├── TEAM_TASKS.md              ← משימות צוות
├── website/                   ← repo נפרד! (GitHub Pages)
│   ├── index.html             ← slh-nft.com
│   ├── admin.html             ← admin panel (19 sidebar pages)
│   ├── ops-dashboard.html     ← health monitoring
│   ├── js/shared.js           ← navigation, themes, i18n
│   ├── js/translations.js     ← 5 lang (HE/EN/RU/AR/FR)
│   └── ...83 HTML files
├── ops/                       ← operations docs, handoffs, plans
│   └── SESSION_HANDOFF_*.md   ← start each session by reading latest
├── admin-bot/                 ← @MY_SUPER_ADMIN_bot
├── guardian/                  ← LOCATION.txt → D:\telegram-guardian-...
├── nfty-bot/                  ← NIFTI_Publisher_Bot
├── g4mebot/                   ← @G4meb0t_bot_bot (gaming/dating)
├── wallet/                    ← @SLH_Wallet_bot
├── factory/                   ← @Osifs_Factory_bot
├── botshop/                   ← @Buy_My_Shop_bot
├── airdrop/                   ← @AIRDROP_bot
├── campaign/                  ← @Campaign_SLH_bot
├── nfty-shop/                 ← NFT shop bot
├── expertnet/                 ← @SLH_Academia_bot (future: Zvika franchise)
├── school/                    ← Education bot
├── fun/                       ← @SLH_Fun_bot
├── device-registry/           ← ESP32 CYD device code
├── slh-genesis/               ← Genesis wallet logic
├── scripts/                   ← utility scripts (no backup cron yet!)
└── backups/                   ← state backups
```

---

## 🔌 איך להתחבר למערכת

### 1. API (read-only, always available)

```bash
# Health check (תמיד קודם כל)
curl https://slh-api-production.up.railway.app/api/health
# → {"status":"ok","db":"connected","version":"1.0.0"}

# Full OpenAPI schema
curl https://slh-api-production.up.railway.app/openapi.json

# Interactive docs
https://slh-api-production.up.railway.app/docs
```

### 2. Admin API (requires X-Admin-Key header)

```bash
# Admin key נמצא ב-localStorage.slh_admin_password באתר admin.html
# או ב-.env תחת ADMIN_API_KEYS
curl -H "X-Admin-Key: slh2026admin" \
     https://slh-api-production.up.railway.app/api/admin/dashboard
```

### 3. Git — repositories

```bash
# API repo (master branch → Railway auto-deploy)
cd D:\SLH_ECOSYSTEM
git pull
git add main.py api/main.py routes/
git commit -m "message"
git push origin master

# Website repo (main branch → GitHub Pages deploy)
cd D:\SLH_ECOSYSTEM\website
git pull
git add .
git commit -m "message"
git push origin main
```

### 4. Docker — local bots

```bash
cd D:\SLH_ECOSYSTEM
docker compose up -d              # start all 22 bots
docker ps                         # check status
docker logs slh-guardian-bot --tail 50  # check specific bot
docker compose restart factory    # restart one bot
docker compose down               # stop all
```

### 5. Database — PostgreSQL

```bash
# Into postgres container
docker exec -it slh-postgres psql -U postgres -d slhdb

# Quick queries
SELECT count(*) FROM users;
SELECT * FROM token_balances ORDER BY slh DESC LIMIT 10;
```

---

## 🤖 25 הבוטים — רשימה מעודכנת (2026-04-18)

### Active / פעילים (22 ב-Docker)

| Container | Bot | Token env | Purpose |
|-----------|-----|-----------|---------|
| slh-guardian-bot | @Grdian_bot | GUARDIAN_BOT_TOKEN | Anti-fraud ZUZ scores, moderation |
| slh-botshop | @Buy_My_Shop_bot | BOTSHOP_BOT_TOKEN | Trading + AI store |
| slh-wallet | @SLH_Wallet_bot | WALLET_BOT_TOKEN | TON/BNB wallet |
| slh-factory | @Osifs_Factory_bot | FACTORY_BOT_TOKEN | Investment + staking |
| slh-core-bot | @SLH_community_bot | CORE_BOT_TOKEN | Community + broadcasts |
| slh-airdrop | @AIRDROP_bot | AIRDROP_BOT_TOKEN | Airdrop distribution |
| slh-nifti | NIFTII marketplace | NIFTI_PUBLISHER_TOKEN | NFT listings |
| slh-nfty | NIFTII publisher | NIFTI_PUBLISHER_TOKEN | Approved listing broadcasts |
| slh-campaign | @Campaign_SLH_bot | CAMPAIGN_TOKEN | Marketing campaigns |
| slh-game | @G4meb0t_bot_bot | GAME_BOT_TOKEN / G4MEBOT_TOKEN | Gaming + dating |
| slh-ledger | @SLH_Ledger_bot | SLH_LEDGER_TOKEN / BOT_TOKEN | Financial ledger |
| slh-ts-set | @ts_set_bot | TS_SET_TOKEN | Settings/Config |
| slh-ton | @SLH_ton_bot | SLH_TON_TOKEN | TON dedicated ops |
| slh-osif-shop | @OsifShop_bot | OSIF_SHOP_TOKEN | Secondary shop |
| slh-crazy-panel | @My_crazy_panel_bot | CRAZY_PANEL_TOKEN | Admin panel |
| slh-chance | @Chance_Pais_bot | CHANCE_PAIS_TOKEN | Lottery/Chance |
| slh-ton-mnh | @TON_MNH_bot | TON_MNH_TOKEN | TON MNH operations |
| slh-admin | @MY_SUPER_ADMIN_bot | ADMIN_BOT_TOKEN | Super admin |
| slh-fun | @SLH_Fun_bot | FUN_BOT_TOKEN | Fun/entertainment |
| slh-nft-shop | NFT shop | MY_NFT_SHOP_TOKEN | NFT marketplace |
| slh-beynonibank | @BeynoniBank_bot | BEYNONIBANK_TOKEN | Banking ops |
| slh-test-bot | @test_bot | TEST_BOT_TOKEN | Testing |

### Infrastructure
- slh-postgres (Up healthy)
- slh-redis (Up healthy)

### Pending / ממתין לפריסה
- **@WEWORK_teamviwer_bot** — token נוסף ל-.env (2026-04-18), צריך container

### Disabled (legacy)
- EXPERTNET_BOT_TOKEN → disabled 2026-04-14 (היה mirror של SELHA_TOKEN)
- SLH_SELHA_TOKEN → disabled 2026-04-14

---

## 🎨 עמודי האתר (83 pages)

### Tiers
- **Landing:** index.html, about.html, how.html, tour.html
- **User:** profile.html, wallet.html, dashboard.html, referral.html, member.html
- **Community:** community.html, p2p.html, dating.html, experts.html
- **Admin (localStorage auth):** admin.html, admin-bugs.html, admin-experts.html, admin-tokens.html, broadcast-composer.html, control-center.html, mass-gift.html, mission-control.html, system-health.html, ops-dashboard.html
- **Payment:** pay.html, receipts.html, card-payment.html, buy.html, deposits (via API)
- **Guides:** getting-started.html, ecosystem-guide.html, join-guide.html, wallet-guide.html, learning-path.html, tour.html, guides.html, docs/, blog/
- **Tokens:** staking.html, kosher-wallet.html, liquidity.html, tokenomics (via API)

### Shared infrastructure
- `css/shared.css` — shared styles + theming
- `js/shared.js` — navigation, themes, i18n
- `js/translations.js` — 5 languages (HE/EN/RU/AR/FR)
- `js/slh-skeleton.js` — skeleton/loading API (show/hide/withSkeleton/fetchJson)
- `assets/`, `img/` — images
- All pages: analytics + AI assistant integrated

---

## 🛠 משימות נפוצות — cookbook

### A. הוספת endpoint חדש ל-API

```python
# routes/my_feature.py
from fastapi import APIRouter
router = APIRouter(prefix="/api/my-feature", tags=["my-feature"])

@router.get("/")
async def list_items():
    return {"items": []}

# main.py (root) AND api/main.py — add:
from routes.my_feature import router as my_feature_router
app.include_router(my_feature_router)
```

```bash
# Sync + deploy
cp api/main.py main.py
git add main.py api/main.py routes/my_feature.py
git commit -m "feat: add /api/my-feature endpoints"
git push origin master  # Railway auto-deploys

# Verify after deploy (~1 min)
curl https://slh-api-production.up.railway.app/api/my-feature/
```

### B. הוספת עמוד חדש לאתר

```bash
cd D:\SLH_ECOSYSTEM\website
cp about.html my-new-page.html
# Edit: title, content, data fetching
# Test locally: open my-new-page.html in browser
git add my-new-page.html
git commit -m "feat(site): add my-new-page"
git push origin main  # GitHub Pages auto-deploys

# Verify
curl -I https://slh-nft.com/my-new-page.html
```

### C. הוספת בוט חדש

```yaml
# docker-compose.yml
  new-bot:
    build: ./new-bot
    container_name: slh-new-bot
    env_file: .env
    depends_on: [postgres, redis]
    restart: unless-stopped
```

```python
# new-bot/bot.py (aiogram 3.x template)
import os, asyncio
from aiogram import Bot, Dispatcher

bot = Bot(token=os.getenv("NEW_BOT_TOKEN"))
dp = Dispatcher()

@dp.message(commands=["start"])
async def start(msg):
    await msg.answer("ברוך הבא!")

if __name__ == "__main__":
    asyncio.run(dp.start_polling(bot))
```

```bash
# .env — add token
echo "NEW_BOT_TOKEN=<token_from_botfather>" >> .env

# Build + start
docker compose up -d new-bot
docker logs slh-new-bot --tail 30
```

### D. לעדכן עמוד קיים עם נתוני API אמיתיים

```html
<!-- my-page.html -->
<div id="stats">טוען...</div>
<script>
async function loadStats() {
  try {
    const r = await fetch('https://slh-api-production.up.railway.app/api/stats');
    const d = await r.json();
    document.getElementById('stats').innerHTML = `
      <p>סה"כ משתמשים: ${d.total_users}</p>
      <p>SLH במחזור: ${d.total_slh}</p>
    `;
  } catch(e) {
    document.getElementById('stats').textContent = 'שגיאה';
  }
}
loadStats();
</script>
```

### E. אימות admin page (localStorage pattern)

```html
<script>
const adminKey = localStorage.getItem('slh_admin_password');
if (!adminKey) {
  location.href = '/admin.html';  // redirect to login
}
async function adminCall(path, opts={}) {
  const r = await fetch(`https://slh-api-production.up.railway.app${path}`, {
    ...opts,
    headers: {...opts.headers, 'X-Admin-Key': adminKey}
  });
  if (r.status === 401) { localStorage.removeItem('slh_admin_password'); location.href = '/admin.html'; }
  return r.json();
}
</script>
```

---

## 🤖 פרומפט מוכן לסוכן AI חיצוני (copy-paste)

**לשימוש כשאתה רוצה לשלוח משימה ל-ChatGPT/Claude/אחר:**

```
You are maintaining the SLH Spark ecosystem — a Hebrew-speaking Israeli crypto project.

## Quick facts
- Owner: Osif Kaufman Ungar (@osifeu_prog, Telegram 224223270)
- Code: D:\SLH_ECOSYSTEM (Windows 10, bash via Claude Code)
- API: https://slh-api-production.up.railway.app (230 endpoints, FastAPI v1.1.0)
- Site: https://slh-nft.com (83 HTML pages, GitHub Pages)
- 24 Docker bots share PostgreSQL + Redis

## Git
- API: github.com/osifeu-prog/slh-api (master → Railway)
- Site: github.com/osifeu-prog/osifeu-prog.github.io (main → Pages)

## Critical rules
1. Write Hebrew in UI text. English in code/commits.
2. NEVER hardcode passwords/tokens in HTML — use localStorage.slh_admin_password + X-Admin-Key header
3. NEVER commit .env to git
4. NEVER show mock data as real — use [DEMO] tag or test_ prefix
5. Railway builds from ROOT main.py — always also sync api/main.py (cp api/main.py main.py)
6. Check ops/SESSION_HANDOFF_*.md (latest date) at start of session
7. Verify after every deploy: curl /api/health and curl the page

## Your task
[INSERT TASK HERE]

## Expected deliverable
- Code committed + pushed
- curl evidence that it works live
- Updated SESSION_HANDOFF_<today>.md in ops/
```

---

## 🔐 Security & .env

### מה נמצא ב-.env (אסור לדחוף!)
- 22 bot tokens
- Database URLs (PostgreSQL, Redis)
- Blockchain keys (BSC, TON)
- Admin keys (slh2026admin — יש להחליף)
- JWT_SECRET (ריק! צריך למלא ב-Railway dashboard)
- External API keys (Binance, OpenAI, etc.)

### איך לרוטט token בבוט

1. Telegram → @BotFather → `/mybots` → select bot → "API Token" → "Revoke current token"
2. Copy new token → `.env` → update relevant `*_BOT_TOKEN`
3. `docker compose restart <service>`
4. `docker logs slh-<service> --tail 10` — וודא שעובד

---

## 📚 קבצים חיוניים לקרוא לפי משימה

| משימה | קבצים |
|--------|--------|
| להתחיל סשן | `ops/SESSION_HANDOFF_*.md` (latest), `CLAUDE.md`, `TASKS_STATUS_2026-04-18.md` |
| לעבוד על API | `routes/`, `main.py`, `api/main.py`, `init-db.sql` |
| לעבוד על אתר | `website/js/shared.js`, `website/js/translations.js`, `website/admin.html` |
| לעבוד על בוט | `docker-compose.yml`, `<bot-name>/bot.py`, `.env` |
| להבין טוקנים | `TOKEN_AUDIT.md`, `TOKEN_ECONOMICS_AUDIT.md` |
| להבין מצב משימות | **`TASKS_STATUS_2026-04-18.md`** (המעודכן) |

---

## 🚨 גישות אסורות

1. ❌ לשנות git config
2. ❌ `--no-verify` / `--no-gpg-sign`
3. ❌ force push ל-master/main
4. ❌ לדחוף .env
5. ❌ להחזיר 50 SLH כפרס (יקר מדי ב-444 ש"ח!)
6. ❌ להציג mock data כאמיתי
7. ❌ הארדקוד סיסמה ב-HTML
8. ❌ `_ensure_tables` — טבלאות נוצרות ב-startup
9. ❌ להניח עמודת `display_name` (יש try/except fallback)

---

## 📞 תמיכה

- **Owner:** Osif (Telegram 224223270, email osif.erez.ungar@gmail.com)
- **Testers:** Zohar Shefa Dror, Tzvika, Eli, Yakir Lisha
- **Future team:** Zvika (co-founder, ExpertNet franchise), Eliezer (worker)

---

*מסמך זה מתעדכן בכל סשן. אם משהו כאן לא תואם את המציאות, עדכן אותו מיד.*
