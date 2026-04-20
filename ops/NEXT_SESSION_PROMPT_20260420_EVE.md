# 🔑 פרומפט לסשן הבא · SLH Spark · המשך מה-20.4.26 אחה"צ
**הדבק את כל הקובץ הזה בסשן Claude Code חדש. מכיל את כל ההקשר הנדרש.**

---

## מי אני (המשתמש)
Osif Kaufman Ungar · @osifeu_prog · Telegram 224223270 · ישראלי · מפתח יחיד · בונה SLH Spark.
`D:\SLH_ECOSYSTEM\` · Windows 10 · Hebrew UI, English commits · "כן לכל ההצעות" = proceed.

## מה קרה בסשן הקודם (24 שעות · commits `bdbd177` → `aac69ff`)

### נפתרו קריטית:
1. ✅ Railway env vars (ENV=prod · JWT · ADMIN · DOCS_ENABLED=0 · RATE_LIMIT) — `/docs=404` ✅
2. ✅ Bot heartbeat endpoint — `routes/bot_registry.py` + `shared/bot_heartbeat.py`
3. ✅ Forensic legal audit — `ops/FORENSIC_AUDIT_20260420.md`
4. ✅ Revenue channel diagnosis — `ops/REVENUE_SYNC_DIAGNOSIS_20260420.md`
5. ✅ **"65% APY" מת** ב-17 דפי אתר → "Variable Yield (4-12%)"
6. ✅ **`/academia.html` חדש** — 260 שורות · highest potential channel

### ממתין לאתה (OSIF):
- [ ] BotFather: רוטציית 5 tokens קריטיים (`SLH_LEDGER` דחוף — 401)
- [ ] ANTHROPIC_API_KEY → `slh-claude-bot/.env`
- [ ] Admin password localStorage update: `slh_admin_2026_rotated_04_20`
- [ ] seed content: 3 academia קורסים · 5 marketplace items · profile לעוד 2 מומחים

## מצב המערכת עכשיו (20.4 · 13:00)
```
Railway API: v1.2.0 · 280 endpoints · /docs=404 (secured)
Database: 95 tables · 108,945 rows · 0 errors/hour
Docker: 24/25 bots UP · slh-ledger stopped (token) · slh-claude-bot stopped (api key)
Website: 94 HTML pages (academia.html חדש!) · 22 users · 12 premium
Tokens: SLH 200K · ZVK 3K · MNH 3.1K · REP 1.2K · ZUZ 9.6K · AIC 1
```

## ארכיטקטורה מהירה
- `api/main.py` → routes/*.py (25 modules) → Postgres 95 tables
- `slh-api` repo → Railway auto-deploy · root `main.py` חייב סנכרון עם `api/main.py`
- `osifeu-prog.github.io` repo (branch=`main`) → GitHub Pages = slh-nft.com
- `website/js/shared.js` → nav/theme/i18n · `translations.js` → 5 שפות
- `.env` ב-root · NEVER commit · tokens + DATABASE_URL + secrets
- Local: `D:\AISITE\` ← control_api/esp_bridge/panel (separate system!)

## 3 אפיקי הכנסה הראשיים (לפי פוטנציאל):

| # | Channel | Backend | Frontend | Status | Need |
|---|---|---|---|---|---|
| 1 | **Academia UGC** (70/30) | ✅ `/api/academia/*` | ✅ `/academia.html` (NEW!) | 🟡 0 courses | seed 3 קורסים |
| 2 | **Marketplace** (5% fees) | ✅ `/api/marketplace/*` | ✅ `gallery/shop/sell.html` | 🟡 0 items | seed 5 פריטים |
| 3 | **Experts** (20% cut) | ✅ `/api/experts/*` | ✅ `/experts.html` | 🟡 1 expert | onboard 2 |

פרטים מלאים: `ops/REVENUE_SYNC_DIAGNOSIS_20260420.md` (20 ערוצים)

## אזהרה משפטית קריטית
**אל תוסיף בחזרה שום טקסט של "65% APY" או "guaranteed return".** 
- זה שונה רק לפני 20 דקות
- כל מופע = סיכון אישי לאוסיף (securities fraud under Israeli law)
- אם רוצה להוסיף yield language → תמיד `variable · may be zero · not guaranteed`

פרטים: `ops/FORENSIC_AUDIT_20260420.md`

## משימות לסשן הזה (בחר 2-3, לא יותר)

### 🔥 המשך Tier 1 production hardening:
- **1.1 pg_dump cron** (2h) — תשתית backups חסרה לגמרי
- **1.4 log aggregation** (2h) — loki + grafana ב-docker
- **1.5 Sentry** (30min) — רק אם יש לי `SENTRY_DSN` מ-OSIF

### 🔥 Revenue activation (שלב 2 מה-REVENUE_SYNC):
- **Seed content**: admin ב-UI מעלה 3 קורסי אוסיף + 5 marketplace items + 2 experts
- **`/love.html`** חדש — Love Tokens widget (ערוץ רדום)
- **ESP dedicated page** `/esp.html` — עם Utility Spec ברור (במקום להסתיר ב-agent-tracker)

### 🟠 UX sync (שלב 3):
- **`index.html` hero**: החלף stats בנתונים LIVE מ-`/api/system/audit`
- **Nav cleanup**: צמצם מ-19 דפים → 5 קטגוריות (Learn · Earn · Trade · Shop · Community)
- **Footer**: הוסף "Risk Disclaimer" link

### 🟡 כלים תומכים:
- **GitHub Actions CI**: build check לכל push (מההצעה של הסוכן החיצוני)
- **Docker healthchecks**: לכל service ב-compose

## כיצד לפתוח את הסשן

```bash
cd D:\SLH_ECOSYSTEM

# ודא שהכל מסונכרן
git pull
curl -s https://slh-api-production.up.railway.app/api/health  # → 1.2.0
curl -so NUL -w "%{http_code}" https://slh-api-production.up.railway.app/docs  # → 404
python D:\AISITE\verify_slh.py  # → 11/12 pass
```

**אז תשאל את אוסיף**: "בוקר טוב / ערב טוב. ראיתי את ה-handoff. מה קודם — Tier 1 (backups) או Revenue activation (seed content)?"

## לינקים מהירים

| מה | URL |
|---|---|
| Website live | https://slh-nft.com |
| API health | https://slh-api-production.up.railway.app/api/health |
| Academia (חדש!) | https://slh-nft.com/academia.html |
| Admin panel | https://slh-nft.com/admin.html (pass: `slh_admin_2026_rotated_04_20` אחרי update) |
| Ecosystem repo | https://github.com/osifeu-prog/slh-api (master) |
| Website repo | https://github.com/osifeu-prog/osifeu-prog.github.io (main) |
| Guardian repo | https://github.com/osifeu-prog/slh-guardian (private) |

## Commits של היום (לקרוא את המצב)

```
aac69ff  feat+fix(revenue): /academia.html + kill 65% APY (17 pages)
6e51063  diagnosis(revenue): 20 channels · 2 LIVE · 11 READY · 4 DORMANT
7088242  audit(forensic): pivot required within 7 days
a8c333e  feat(bot-registry): live heartbeat system
bdbd177  docs(roadmap): comprehensive upgrade plan — 5 tiers
```

## אל תעשה

- ❌ אל תחזיר "65% APY" לשום מקום
- ❌ אל תוסיף דור 3+ ל-referral system
- ❌ אל תקבל fiat deposits ב-`/api/deposits/*` (banking law)
- ❌ אל תמכור ESP ב-888 ₪ עד שיש Utility Spec אמיתי
- ❌ אל תשדר ל-10K+ משתמשים לפני legal entity
- ❌ אל תדחוף קוד בלי `verify_slh.py` → 11/12 או יותר

## תעשה

- ✅ תאמת כל שינוי עם curl + python syntax check
- ✅ תתעד כל decision ב-`ops/*.md`
- ✅ תשמור context שלך מתחת ל-150K tokens (אל תמתח את הסשן)
- ✅ תהיה ישר עם אוסיף — גם כשזה כואב
- ✅ תוביל כשהוא אומר "תוביל" — אבל תעצור אם יש סיכון משפטי

## הטון הנכון

אוסיף הוא מפתח חרוץ, בונה מערכת מרהיבה, אבל היסטורית נופל לסיכונים משפטיים. התפקיד שלך: לעזור לו **להרוויח כסף אמיתי** (זו המטרה שלו) **בצורה שלא תהרוס לו את החיים**.

"רק שאתחיל להרוויח" — זו הבקשה האמיתית. Academia + marketplace + experts = הדרך הכי בטוחה לשם. לא staking, לא yields, לא ESP עד Utility Spec.

---

**בהצלחה.** 🚀
