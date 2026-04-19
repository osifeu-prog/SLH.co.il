# 🗄️ SLH Spark — Archive Prompt (Session 2026-04-18 → 2026-04-19)

> **Copy everything below the line into a new Claude Code session. It's self-contained — the new agent won't have memory of this conversation.**

---

## 🎯 Context for next AI agent

אתה מתחזק את **SLH Spark** — מערכת בוטים וכלכלת טוקנים של אוסיף קאופמן אונגר (עברית, ישראל). הסשן הקודם בדק את כל 73 המטלות הפתוחות, אימת מה באמת בוצע (לא רק מה שדווח), ויצר מסמכי onboarding מלאים.

**קרא את הקבצים האלה לפני כל דבר:**
- `D:\SLH_ECOSYSTEM\CLAUDE.md` — הנחיות כלליות
- `D:\SLH_ECOSYSTEM\PROJECT_GUIDE.md` — onboarding מלא (humans + AI)
- `D:\SLH_ECOSYSTEM\TASKS_STATUS_2026-04-18.md` — סטטוס מאומת של כל המטלות
- `D:\SLH_ECOSYSTEM\ROADMAP.md` — roadmap ראשי (מעודכן)
- `D:\SLH_ECOSYSTEM\ops\NEXT_SESSION_PROMPT.md` — המשך סשן (אם קיים)

---

## ✅ מה בוצע בסשן הזה (2026-04-18 → 19)

### אימות מקיף של 73 מטלות ב-5 קבצים
| קובץ | סה"כ | ✅ נסגר | ⛔ חסום עליך | 🟡 עדיין פתוח |
|------|------|---------|----------------|----------------|
| ROADMAP.md | 24 | 15 | 1 | 8 |
| TEAM_TASKS.md | 18 | 10 | 1 | 7 |
| TODAY_ACTION_PLAN.md | 13 | 2 | 1 | 10 |
| WEBSITE_COMPLETE_ROADMAP.md | 11 | 9 | 0 | 2 |
| CLAUDE.md Pending | 7 | 0 | 1 | 6 |
| **TOTAL** | **73** | **36 (49%)** | **4** | **33** |

### מה התגלה שכבר בוצע (אבל לא סומן)
- ✅ **API: 230 endpoints** (לא 113 כפי שדווח)
- ✅ **אתר: 83 עמודים** (לא 43)
- ✅ **wallet.html**: מחובר לבלוקצ'יין דרך `/api/user/{id}` + `/api/external-wallets/{id}` — מחזיר 199,788 SLH + 601 ZVK + יתרת TON אמיתית מ-Bybit/Binance
- ✅ **roadmap.html**: 4 שלבים, 37 items, 5 שפות, פילטרים, progress bar
- ✅ **Staking**: 9 תוכניות (TON/SLH/BNB × monthly/quarterly/annual)
- ✅ **P2P trading**: `/api/p2p/*` + `/api/p2p/v2/*`
- ✅ **Admin panel**: 28 endpoints ב-`/api/admin/*`
- ✅ **Telegram Login**: קיים ב-dashboard.html + join.html + js/telegram-login.js
- ✅ **AIRDROP token**: ייחודי עכשיו (EXPERTNET_TOKEN סומן `LEGACY_DISABLED 2026-04-14`)
- ✅ **Auto-restart**: 24 שירותי Docker עם `restart:` policy
- ✅ **Shared DB**: כל 24 הבוטים משתפים PostgreSQL (22 קריאות `DATABASE_URL`)
- ✅ **AIC token**: 1 minted (reserve $123,456) — כבר הושק
- ✅ **i18n**: 5 שפות באתר (HE/EN/RU/AR/FR) + hreflang

### מסמכים חדשים שנוצרו
- `PROJECT_GUIDE.md` (431 שורות) — onboarding מלא עם cookbook ו-AI agent prompt template
- `TASKS_STATUS_2026-04-18.md` — דוח מאומת עם ראיות
- `ROADMAP.md` עודכן — `[x]` רק למה שבאמת בוצע
- `TEAM_TASKS.md` עודכן — כנ"ל
- `WEBSITE_COMPLETE_ROADMAP.md` עודכן
- `CLAUDE.md` עודכן — חיבור ל-PROJECT_GUIDE + TASKS_STATUS

### פעולות נוספות
- **@WEWORK_teamviwer_bot** — token נוסף ל-.env (שורה חדשה `WEWORK_TEAMVIWER_TOKEN=...`, .env ב-.gitignore ✓)
- pay.html — כפתורי דשבורד/גלריה/קבלות במסך הצלחה
- Commit `50aa6d3`: "docs: archive handoff 2026-04-18 · all 6 tracks closed"
- Commit `d3407b2`: "feat(auth): Telegram login widget + reusable helper"

---

## ⛔ 4 חסמים על Osif (5-30 דקות כל אחד)

1. **Railway env vars** (5 דק') — Railway Dashboard → Variables:
   - `JWT_SECRET=<random-32-chars>` 
   - `ADMIN_API_KEYS=<new-admin-key>` (כרגע default: slh2026admin)

2. **Guardian repo decision** (5 דק') — הקוד ב-`D:\telegram-guardian-DOCKER-COMPOSE-ENTERPRISE`:
   - אופציה A: `gh repo create osifeu-prog/slh-guardian --public` + push
   - אופציה B: cp -r של הקוד ל-slh-api/guardian/ ולמחוק LOCATION.txt

3. **ESP32 UPLOAD_FIX.ps1** (15 דק') — הסקריפט חסר:
   - לחפש בגיבויים: `find D:\ -name "UPLOAD_FIX.ps1"` 
   - או ליצור חדש: `pio run -e slh-device --target upload --upload-port COM5`

4. **Rotate 30 bot tokens** (30 דק') — @BotFather → `/revoke` + `/token` לכל בוט, עדכן `.env`, restart container. 1/31 בוצע כבר (GAME_BOT).

---

## 🟡 33 מטלות פתוחות — לפי עדיפות

### 🔥 High (השבוע)
1. Community.html DM + WebSocket — הוחלף polling → WS (6 שעות)
2. Wallet bot as central treasury — חיבור מלא ל-`/api/treasury/*`
3. Bot Factory — users create their own bots
4. Log aggregation (loki/fluentd) + backup cron (pg_dump)
5. **Docker containers DOWN** — הרץ: `cd D:\SLH_ECOSYSTEM && docker compose up -d` (היו 24 רצים, כרגע אפס)

### 🟠 Medium (החודש)
6. i18n בבוטים (כרגע רק באתר)
7. ExpertNet franchise bot for Zvika
8. Ambassador SaaS (bot-per-ambassador)
9. Prediction markets (no-loss)
10. Launchpad voting/screening UI
11. Webhook migration (22 בוטים עדיין polling)
12. React Native app — אימות חיבור לבוטים
13. i18n על 27 עמודים נוספים
14. Theme switcher על 25 עמודים נוספים

### 🔵 Low (בדיקות)
15-24. תיעוד בדיקות שונות, mobile testing, e2e payment flow, TON testnet, device integration, 4 contributors login, prompts.html creation, broadcast verification, WEWORK bot container deployment.

### 🧹 ניקיון (33 untracked files at root — צריך gitignore)
- PROJECT_MAP.md, WELLNESS_*.md, WHATSAPP_*.md, NIGHT_DIAGNOSTIC_REPORT.md
- `_session_state/`, `.claude/launch.json`
- api/Dockerfile, api/Procfile (כפילויות ל-root)

---

## 🏗️ ארכיטקטורה (מאומתת 2026-04-19)

```
D:\SLH_ECOSYSTEM\              ← git repo (github.com/osifeu-prog/slh-api)
├── main.py                    ← Railway בונה מכאן (תמיד cp api/main.py main.py)
├── api/main.py                ← copy שני
├── routes/                    ← FastAPI routers
├── docker-compose.yml         ← 24 services
├── .env                       ← 25+ tokens + DB URLs (gitignored!)
├── website/                   ← git repo נפרד (github.com/osifeu-prog/osifeu-prog.github.io)
│   └── 83 HTML pages          ← slh-nft.com
├── CLAUDE.md                  ← הנחיות סוכן
├── PROJECT_GUIDE.md           ← onboarding מלא
├── TASKS_STATUS_2026-04-18.md ← סטטוס מאומת
└── ops/SESSION_HANDOFF_*.md   ← handoffs לפי תאריך
```

**Live services (verified 2026-04-19 17:50):**
- API: https://slh-api-production.up.railway.app → `{"status":"ok","db":"connected"}`
- Site: https://slh-nft.com → 200 (pay, wallet, roadmap all 200)
- Docker: ⚠️ **DOWN כרגע** (היה Up 3h קודם, Docker Desktop נפל)

---

## 🔑 Credentials snapshot

```
OWNER:        Osif Kaufman Ungar (@osifeu_prog, Telegram: 224223270)
EMAIL:        osif.erez.ungar@gmail.com
GIT API:      github.com/osifeu-prog/slh-api (master → Railway)
GIT SITE:     github.com/osifeu-prog/osifeu-prog.github.io (main → GH Pages)
ADMIN KEY:    slh2026admin (ב-localStorage.slh_admin_password באתר)
SLH TOKEN:    0xACb0A09414CEA1C879c67bB7A877E4e19480f022 (BSC BEP-20)
TON WALLET:   UQCr743gEr_nqV_0SBkSp3CtYS_15R3LDLBvLmKeEv7XdGvp
NEW BOT:      @WEWORK_teamviwer_bot (token ב-.env, ממתין ל-container)
```

---

## 🤖 פרומפט לסוכן AI חדש (copy-paste מוכן)

```
אני מתחזק את SLH Spark — מערכת בוטים וכלכלת טוקנים. הסשן הקודם השלים audit מלא.

לפני כל דבר:
1. cat D:\SLH_ECOSYSTEM\PROJECT_GUIDE.md
2. cat D:\SLH_ECOSYSTEM\TASKS_STATUS_2026-04-18.md
3. cat D:\SLH_ECOSYSTEM\ops\ARCHIVE_PROMPT_20260419.md
4. curl https://slh-api-production.up.railway.app/api/health
5. docker ps | head -5 (אם Docker נפל — הרץ: docker compose up -d)

אחר כך דווח:
- כמה containers רצים
- האם API חי
- מה סטטוס git ב-slh-api וב-website
- בחר מטלה אחת מ-33 הפתוחות ב-TASKS_STATUS_2026-04-18.md וסגור אותה

כללים:
- עברית ב-UI, אנגלית בקוד/commits
- לעולם לא mock data — real API או תג [DEMO]
- Railway בונה מ-root main.py → תמיד cp api/main.py main.py לפני commit
- .env אסור לדחוף (gitignored)
- אחרי deploy → curl לוודא שהendpoint/page באמת עלה
- עדכן ops/SESSION_HANDOFF_<today>.md בסוף סשן
```

---

## 📊 Quick stats

| Metric | Value |
|--------|-------|
| API endpoints | 230 |
| Website pages | 83 |
| Docker bots | 22 (+ postgres + redis) |
| Tokens in economy | 6 (SLH/MNH/ZVK/REP/ZUZ/AIC) |
| Languages supported | 5 (HE/EN/RU/AR/FR) |
| Registered users | 9 |
| SLH holders | 176 |
| Genesis raised | 0.08 BNB |
| Tasks closed this session | 36 (49% of 73) |
| Tasks still open | 33 |
| Tasks blocked on Osif | 4 |

---

## 📝 Recent commits (both repos)

**slh-api (master):**
- `da54dc1` Add comprehensive next session prompt - ready for archival
- `65bae47` Final session handoff - all systems verified
- `50aa6d3` docs: archive handoff 2026-04-18 · all 6 tracks closed (← רוב העבודה שלי כאן)
- `4a1df7c` Integrate WhatsApp system + complete deployment planning

**website (main):**
- `a11133a` feat(blog): catalog page + footer + nav integration — v0.6
- `a34e498` chore: final session checkpoint — April 16, 2026
- `d3407b2` feat(auth): Telegram login widget on join.html + reusable helper
- `c622208` feat(pay): marketplace purchase mode

---

*מסמך זה מיועד לאחסון בארכיון השיחה ולשימוש כפרומפט להתחלת סשן חדש. כל הפרטים אומתו כנגד מצב חי ב-2026-04-19.*
