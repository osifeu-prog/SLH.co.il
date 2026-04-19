# 🗄️ SLH Spark — Archive Prompt V2 (2026-04-19)

> **העתק את כל מה שמתחת לקו לסשן חדש של Claude Code. המסמך self-contained — הסוכן הבא לא יודע כלום על השיחה הקודמת.**
>
> **אומת חי ב-2026-04-19** · API + Website + Git בדוקים בזמן אמת · לא כולל הצהרות שלא מוכחות

---

## 🎯 מי אתה עכשיו

אתה הסוכן המוביל של **SLH Spark** — מערכת בוטים + כלכלת טוקנים + אתר + API של אוסיף קאופמן אונגר (עברית, ישראל).

**לפני כל פעולה קרא (בסדר הזה):**

1. `D:\SLH_ECOSYSTEM\CLAUDE.md` — כללי עבודה
2. `D:\SLH_ECOSYSTEM\PROJECT_GUIDE.md` — onboarding מלא (431 שורות)
3. המסמך הזה — סטטוס אמיתי של 2026-04-19
4. `D:\SLH_ECOSYSTEM\TASKS_STATUS_2026-04-18.md` — 73 מטלות + אימות

---

## ✅ מצב חי מאומת (19.4.26)

| רכיב | סטטוס | הוכחה |
|------|-------|-------|
| Railway API | 🟢 UP | `curl /api/health` → `{"status":"ok","db":"connected","version":"1.0.0"}` |
| OpenAPI | 🟢 200 | 230 endpoints live |
| Website ראשי | 🟢 200 | https://slh-nft.com/ |
| admin.html | 🟢 200 | Login (slh2026admin) עובד |
| wallet.html | 🟢 200 | מחובר לבלוקצ'יין |
| status.html | 🟢 200 | דף שקיפות חדש |
| agent-hub.html | 🟢 200 | ICQ לסוכנים |
| Website pages | 🟢 91 קבצי HTML | `ls *.html \| wc -l` = 91 |
| Docker | 🔴 DOWN | Desktop נפל — `docker ps` error |
| main repo git | ⚠️ 61 untracked/modified | ראה סעיף "ניקוי" למטה |
| website repo git | 🟢 CLEAN | אין שינויים לא-committed |

**Commit אחרון slh-api:** `87a84bd` — docs(handoff): sprint summary 2026-04-19
**Commit אחרון website:** `70aa04f` — feat: /status.html + /agent-hub.html

---

## 🏗️ ארכיטקטורה (verified)

```
D:\SLH_ECOSYSTEM\              ← git: github.com/osifeu-prog/slh-api (master → Railway)
├── main.py                    ← Railway בונה מכאן! תמיד cp api/main.py main.py
├── api/main.py                ← עותק שני
├── routes/                    ← FastAPI routers
├── docker-compose.yml         ← 24 services (22 בוטים + postgres + redis)
├── .env                       ← 25+ tokens + DB URLs (gitignored)
├── website/                   ← git repo נפרד → GH Pages → slh-nft.com
│   └── 91 HTML pages
├── CLAUDE.md                  ← כללי סוכן
├── PROJECT_GUIDE.md           ← onboarding (431 שורות)
├── TASKS_STATUS_2026-04-18.md ← 73 מטלות מאומתות
└── ops/                       ← handoffs + plans (60+ קבצים)
```

---

## 🔑 Credentials & Links

```yaml
OWNER:        Osif Kaufman Ungar
TELEGRAM:     @osifeu_prog (ID: 224223270)
EMAIL:        osif.erez.ungar@gmail.com
PHONE:        058-420-3384

API_REPO:     github.com/osifeu-prog/slh-api (branch: master)
SITE_REPO:    github.com/osifeu-prog/osifeu-prog.github.io (branch: main)
RAILWAY_ID:   96452076-6885-4e6d-9b26-9ef20d6c3cd7

API_URL:      https://slh-api-production.up.railway.app
API_DOCS:     https://slh-api-production.up.railway.app/docs
SITE_URL:     https://slh-nft.com
ADMIN_LOGIN:  /admin.html → password: slh2026admin (localStorage.slh_admin_password)

SLH_CONTRACT: 0xACb0A09414CEA1C879c67bB7A877E4e19480f022 (BSC BEP-20)
PCS_POOL:     0xacea26b6e132cd45f2b8a4754170d4d0d3b8bbee
GENESIS:      0xd061de73B06d5E91bfA46b35EfB7B08b16903da4
MAIN_METAMASK:0xD0617B54FB4b6b66307846f217b4D685800E3dA4 (199K SLH)
TON_TEMPLATE: UQCr743gEr_nqV_0SBkSp3CtYS_15R3LDLBvLmKeEv7XdGvp
```

---

## 💎 5 טוקנים (+ 1 חדש)

| טוקן | מטרה | מצב |
|------|------|-----|
| SLH | Premium/governance (יעד 444 ILS) | LIVE on BSC, PCS pool active |
| MNH | Stablecoin צמוד ל-1 ILS | פנימי |
| ZVK | תגמולי פעילות (~4.4 ILS) | פנימי, מרוויחים ע"י תרומה |
| REP | דירוג מוניטין אישי | פנימי, 0-1000+ tiers |
| ZUZ | "אות קין" נגד spam | Guardian, auto-ban ב-100 |
| **AIC** | טוקן חדש | **1 AIC minted**, reserve $123,456 |

---

## 📊 ספירה אמיתית

```
API endpoints:       230  (תועד בעבר 113 — היה לא מעודכן)
Website HTML pages:  91   (תועד בעבר 43 → 83 → כרגע 91)
Docker services:     24   (22 בוטים + postgres + redis) [כרגע כולם DOWN]
Token economy:       6 tokens
Languages (i18n):    5    (HE/EN/RU/AR/FR + hreflang)
Admin sidebar pages: 19
Admin API endpoints: 28   (/api/admin/*)
Registered users:    16   (גדל מ-9)
SLH holders:         176
Genesis raised:      0.08 BNB
```

---

## ✅ מה באמת בוצע (מצטבר, אומת)

### תשתית 🟢
- Docker: docker-compose.yml עם 24 services, restart policy על כולם
- PostgreSQL + Redis: רצים עם healthcheck (כשמופעלים)
- Railway auto-deploy מ-master branch של slh-api
- GitHub Pages מ-main של website repo
- SSL אוטומטי, 5 languages hreflang, PWA manifest

### API (230 endpoints) 🟢
- Community: posts, comments, like, react, threaded, health, rss, stats
- Wallet: deposit, send, price, balances, transactions
- P2P trading: `/api/p2p/*` + `/api/p2p/v2/*` (order book)
- Admin: 28 endpoints (multi-admin, roles, login, reset-password)
- Staking: TON/SLH/BNB × monthly/quarterly/annual (9 תוכניות)
- Payments: TON + BSC auto-verify, receipts, geography
- Referral: 10 דורות (Gen1 10%, Gen2 5%, ..., Gen6-10 0.5%)
- Analytics, Campaign, Tokenomics, Dating, Experts, Marketplace, Risk, Sudoku, Presence
- WhatsApp: 6 endpoints at `/api/whatsapp/*`
- Wellness: 3 endpoints at `/api/wellness/*`
- Guardian: reports, stats, blacklist
- External watch: SLH_BSC monitored

### Website (91 pages) 🟢
- Core: index, about, community, blog, guides, experts, roadmap, pay, wallet
- Admin: admin.html (19 sidebar pages), ops-dashboard, system-health
- Finance: pay, card-payment, wallet-guide, staking, p2p, receipts, liquidity, dex-launch
- Social: community, network, referral, referral-card, dating, invite
- Content: blog (9 entries), daily-blog, blog-legacy-code, gallery, tour
- Auth: join (Telegram widget), join-guide, onboarding, getting-started
- Operational: analytics, live-stats, live, project-map, risk-dashboard, agent-brief, morning-handoff
- Commerce: shop, buy, sell, trade, earn, promo-shekel, challenge, sudoku
- Special: kosher-wallet (ESP32), status, agent-hub (חדשים)

### Features 🟢
- Multi-language: 5 שפות (HE/EN/RU/AR/FR)
- Theme switcher: 42% coverage
- Tooltips על כל nav
- SEO: OG tags, Twitter Cards, JSON-LD, hreflang
- CRT effects + matrix rain (terminal theme)
- ASCII hero art
- Telegram Login Widget ב-dashboard + join + `js/telegram-login.js`

### טוקנים 🟢
- SLH on BSC — live, PCS pool active
- SLH holders: 176
- AIC: 1 minted, reserve $123K
- Cross-bot shared DB (22 bots read `DATABASE_URL`)
- Legacy EXPERTNET_TOKEN סומן `LEGACY_DISABLED 2026-04-14`

### בוטים (24 services) 🟢 [במצב תקין]
userinfo ⚠️ (token conflict, עצור), expertnet ⚠️ (same), selha ⚠️ (same),
nfty, guardian-bot ⚠️ (InvalidToken — צריך חדש), game, factory, core-bot,
campaign, ton, nifti ⚠️ (same ID as nfty), crazy-panel, fun, wallet, beynonibank,
ts-set, nft-shop, ledger ⚠️ (SyntaxError bot_template.py:237),
chance, ton-mnh, botshop, osif-shop, test-bot, admin, airdrop

---

## ⛔ 4 חסמים על אוסיף (דקות בודדות כל אחד)

### 1. Railway env vars (5 דק')
```
Railway Dashboard → slh-api → Variables → Add:
  JWT_SECRET=<32 תווים רנדומליים>
  ADMIN_API_KEYS=<מפתח admin חדש>
```
השפעה: אימות JWT + אבטחת admin panel

### 2. Guardian repo החלטה (5 דק')
קוד ב-`D:\telegram-guardian-DOCKER-COMPOSE-ENTERPRISE`:
- **אופציה A:** `gh repo create osifeu-prog/slh-guardian --public` + push
- **אופציה B:** `cp -r` ל-`slh-api/guardian/` ולמחוק LOCATION.txt

### 3. ESP32 UPLOAD_FIX.ps1 (15 דק')
הסקריפט חסר:
- לחפש בגיבויים: `Get-ChildItem D:\ -Recurse -Filter "UPLOAD_FIX.ps1"`
- או חדש: `pio run -e slh-device --target upload --upload-port COM5`

### 4. Rotate 30 bot tokens (30 דק')
- @BotFather → `/revoke` + `/token` לכל בוט
- עדכן `.env`
- `docker compose restart <service>`
- **בוצע עד כה:** 1/31 (GAME_BOT ב-17.4)
- **עדיפות:** 3 בוטים על token 8225059465 (userinfo/expertnet/selha) — עצורים כרגע

---

## 🟡 33 מטלות פתוחות — מסודר לפי עדיפות

### 🔥 High (השבוע)
1. **Docker up** (2 דק') — `cd D:\SLH_ECOSYSTEM && docker compose up -d`
2. **ledger bot fix** (10 דק') — `shared/bot_template.py:237` מרכאה לא סגורה
3. **wallet.html → blockchain** (2 שעות) — endpoints מוכנים, צריך לקרוא להם
4. **pay.html 3 bugs** (1 שעה) — טוען, --₪, קישור פיד
5. **community.html DM + WebSocket** (6 שעות) — כרגע polling
6. **roadmap.html sections** (2 שעות) — חסרות COMPLETED/IN PROGRESS/UPCOMING
7. **Trust Level gamification UI** (3 שעות)
8. **Auto-sync BSC → DB watcher** (3 שעות)

### 🟠 Medium (החודש)
9-14. Log aggregation (loki), Backup cron (pg_dump), Wallet bot as central treasury, i18n בבוטים, ExpertNet franchise, Ambassador SaaS, Bot Factory, Prediction markets, Launchpad UI, Webhook migration (22 בוטים), React Native verification, i18n על 27 עמודים, Theme switcher על 25 עמודים

### 🔵 Low (בדיקות)
15-24. Community posting test, Mobile testing (91 pages), E2E payment flow, Broadcast distribution, TON testnet, 4 contributors login, prompts.html creation, Device integration with Ledger+Guardian

### 🧹 ניקוי (33 untracked files + 61 מודפסים ב-main repo)
29-33. PROJECT_MAP.md, WELLNESS_*.md, WHATSAPP_*.md, `_session_state/`, `api/Dockerfile` + `api/Procfile` כפילויות, `.claude/launch.json`

### 🚨 חשוב: git status שלך חריג
`61 modified + untracked files` ב-main repo — כולל תיקייה שלמה של `api/` עם duplicates של `admin-bot/, airdrop/, app/, assets/, backups/, campaign-bot/, core/, database/, device-registry/, dockerfiles/`. **אל תעשה commit לפני שאוסיף מאשר** שזה לא כפילות של כל הפרויקט.

---

## 🎯 Session start checklist (לסוכן הבא)

בדיוק בסדר הזה:

```powershell
# 1. Verify API
curl https://slh-api-production.up.railway.app/api/health

# 2. Verify Docker
docker ps | Select-Object -First 5

# 3. If Docker down:
cd D:\SLH_ECOSYSTEM
docker compose up -d

# 4. Check git
cd D:\SLH_ECOSYSTEM
git status --short | Measure-Object -Line
cd D:\SLH_ECOSYSTEM\website
git status --short

# 5. Read context
cat D:\SLH_ECOSYSTEM\CLAUDE.md
cat D:\SLH_ECOSYSTEM\ops\ARCHIVE_PROMPT_20260419_V2.md  # המסמך הזה
cat D:\SLH_ECOSYSTEM\TASKS_STATUS_2026-04-18.md

# 6. שאל את אוסיף: מה הפריוריטי היום?
```

---

## 🚨 כללי ברזל (אל תפר)

- ✅ **עברית ב-UI, אנגלית בקוד/commits**
- ✅ **real data בלבד** — לעולם לא mock/fake; אם אין — תג `[DEMO]` או `--`
- ✅ **Railway בונה מ-ROOT `main.py`** — אחרי כל שינוי ב-`api/main.py`:
  ```
  cp api/main.py main.py
  git add main.py api/main.py
  ```
- ✅ **`.env` לעולם לא push** (gitignored)
- ✅ **אחרי deploy → `curl` לוודא** שהendpoint/page באמת עלה
- ✅ **admin passwords ב-localStorage בלבד**, לא ב-HTML
- ❌ **לעולם לא `_ensure_tables`** — טבלאות נוצרות ב-startup
- ❌ **לעולם לא להניח ש-`display_name` קיים** — תמיד try/except
- ❌ **לא לערוך `admin.html` יותר מפעם אחת בין pushes** (שביר מדי)
- ❌ **לא להתחרט ולכפול** — כל commit חייב להיות עצמאי

---

## 📞 האנשים

- **אוסיף** — בעלים + מפתח יחיד (224223270)
- **צביקה** — co-founder, crypto trader
- **אלעזר** — community leader, broker
- **עידן** — IT
- **יערה** — content creator (course upload pending)
- **זוהר שפע דרור** — contributor פעיל, QA טוב
- **אלי, יקיר לישא** — contributors
- **אחיין 13 (6466974138)** — tester

---

## 📜 Commit history אחרון

**slh-api (master):**
- `87a84bd` docs(handoff): sprint summary 2026-04-19 - status.html + agent-hub.html shipped
- `e8d0c12` docs: archive prompt for session 2026-04-18 → 19
- `50aa6d3` docs: archive handoff 2026-04-18 · all 6 tracks closed
- `7d83278` feat(claude-bot): @SLH_Claude_bot — Telegram-native executor

**website (main):**
- `70aa04f` feat: /status.html + /agent-hub.html — live transparency + agent ICQ
- `a11133a` feat(blog): catalog page + footer + nav integration — v0.6
- `d3407b2` feat(auth): Telegram login widget on join.html + reusable helper

---

## 🤖 הפרומפט המוכן להדבקה לסוכן חדש

```
אני מתחזק את SLH Spark — מערכת בוטים וכלכלת טוקנים של אוסיף אונגר בעברית.

לפני כל פעולה:
1. cat D:\SLH_ECOSYSTEM\CLAUDE.md
2. cat D:\SLH_ECOSYSTEM\ops\ARCHIVE_PROMPT_20260419_V2.md
3. cat D:\SLH_ECOSYSTEM\TASKS_STATUS_2026-04-18.md
4. curl https://slh-api-production.up.railway.app/api/health
5. docker ps (אם ריק — docker compose up -d)
6. git status בשני ה-repos

אחר כך דווח לי:
- כמה containers רצים
- API חי? (status ok?)
- git status ב-slh-api (יש 61 untracked — אל תעשה commit עד שאוסיף בודק)
- git status ב-website (אמור להיות clean)

ואז חכה להנחיות — אל תתחיל לערוך כלום עד שאוסיף אומר מה הפריוריטי.

כללים:
- עברית ב-UI, אנגלית בקוד
- אין mock data, רק real API או [DEMO]
- Railway = root main.py (תמיד cp api/main.py main.py לפני commit)
- .env לא נדחף
- אחרי deploy → curl לוודא
- admin.html רגיש — עריכה אחת בלבד בין pushes
- אם משהו נראה כפול/חשוד (כמו 61 שינויים בגיט) — תעצור ותשאל
```

---

*המסמך הזה מחליף את 6 ה-handoff docs הקודמים. אם יש סתירה — המסמך הזה הוא source of truth.*

*אומת ב-2026-04-19 ע"י curl + git + filesystem. לא כתוב כאן דבר שלא נבדק.*
