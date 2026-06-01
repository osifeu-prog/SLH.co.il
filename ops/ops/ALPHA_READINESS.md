# 🚀 SLH Spark · Alpha Readiness Map

> **תאריך:** 2026-04-17 · **מצב נוכחי:** Late Alpha / Early Beta (80% ready)
> **הגרסה הבאה:** v0.9.0-alpha → v1.0.0-beta (אחרי 20 משתמשים פעילים + 7 ימים יציבים)

---

## מה זה "אלפא" באמת?

באופן מעשי, **אלפא = המערכת עובדת כל הדרך, אבל צפויים באגים**. ההבחנה מ-Beta:

| שלב | קהל | הגדרה | שינויים צפויים |
|------|-----|--------|---------------|
| **Pre-alpha** | רק אתה | POC, קצוות שבורים | שינויים רדיקליים |
| **Alpha** | 5-20 אנשים קרובים | כל הזרימות עובדות, אבל עם באגים | פיצ'רים עדיין משתנים |
| **Closed Beta** | 50-200 משתמשי בדיקה | יציב, מצומצם | בעיקר תיקוני באגים |
| **Open Beta** | 1000+ | פתוח לציבור עם אזהרה | polish + מיטוב |
| **GA** | כולם | פרודקשן מלא | שמירה על stability |

**איפה אתה:** באמצע **Closed Alpha** — כל הצינור מ-הרשמה→תשלום→קבלה עובד (הוכחת זאת עכשיו!).

---

## 🗺 מה עוד צריך לפני מעבר ל-Beta

### 🔴 קריטי (שבוע הקרוב)

| # | מה | למה זה חשוב | מי יעשה | זמן |
|---|------|------------|--------|-----|
| 1 | **תיקון /api/payment/status (500)** | משתמשים לא יכולים לראות Premium status | Railway deploy של commit `0e8c528` | 2 דק' המתנה |
| 2 | **Deploy @G4meb0t_bot_bot ל-Railway** | הבוט חייב להיות חי 24/7 | אתה · [g4mebot/README.md](https://github.com/osifeu-prog/slh-api/blob/master/g4mebot/README.md) | 3 דק' |
| 3 | **Error monitoring (Sentry free)** | לדעת מתי יש crashes ברגע שזה קורה | אתה · https://sentry.io/signup/ | 15 דק' |
| 4 | **Uptime monitoring (UptimeRobot free)** | התראה כש-Railway יורד | אתה · https://uptimerobot.com (חינם עד 50 monitors) | 10 דק' |
| 5 | **CHANGELOG.md + tag v0.9.0-alpha** | משתמשים רואים מה חדש | אני בקריאה הבאה | 10 דק' |

### 🟡 חשוב (2 שבועות)

| # | מה | פתרון |
|---|-----|--------|
| 6 | 5-10 משתמשים אמיתיים פעילים | פתח את [invite.html](https://slh-nft.com/invite.html) ל-3 חברים קרובים תחילה |
| 7 | CI/CD אוטומטי | GitHub Actions workflow (אני אעשה) |
| 8 | Test coverage בסיסי | `scripts/e2e-smoke-test.ps1` כבר קיים — פשוט להריץ בקביעות |
| 9 | Rate limiting על API | FastAPI slowapi middleware |
| 10 | Backup אוטומטי של DB | Railway → Postgres → Enable daily backups |

### 🟢 נחמד (חודש)

| # | מה |
|---|------|
| 11 | Documentation site (GitBook / Docusaurus) |
| 12 | Public API docs (כבר ב-`/docs` של Railway) |
| 13 | Onboarding video (3-5 דק' על YouTube) |
| 14 | Press release מסודר |
| 15 | CertiK audit (~$5-15K, לכשיהיה volume ראוי) |

---

## 🤖 שלושת שלבי העדכון (עם כל AI)

כל שינוי במערכת עובר דרך 3 שלבים. **כל AI יכול לעשות את זה** אם נותנים לו את התיעוד הנכון.

### שלב 1 · Context (5 דק' של קריאה)
AI זר קורא:
1. `CLAUDE.md` (שורש) — מי המשתמש, מה הפרויקט
2. `ops/SESSION_STATUS.md` — מה פתוח עכשיו
3. `ops/DECISIONS.md` — החלטות שכבר סגורות (אל תדיון מחדש)
4. `ops/AGENT_INTRO_PROMPT.md` — איך לעבוד כאן

→ לאחר זה, AI זר יודע בדיוק איפה הוא.

### שלב 2 · Execute (קונבנציה קפדנית)
1. לכל שינוי — **commit נפרד** עם conventional message (`feat:`, `fix:`, `docs:`)
2. לכל endpoint חדש — גם ב-`routes/` וגם ב-`api/routes/` (double sync)
3. לכל עמוד חדש — להוסיף ל-`sitemap.xml` + `blog/index.html` (אם רלוונטי)
4. לעולם לא ל-commit: `.env`, tokens, סיסמאות

### שלב 3 · Handoff (3 דקות בסוף)
1. עדכן `ops/SESSION_STATUS.md` — מה עשיתי, מה בלוקר
2. אם משהו לא הושלם — `ops/TEAM_TASKS.md`
3. Push ל-master → Railway auto-deploy

---

## 🎯 בוט ייעודי לעדכוני מערכת

**הבחירה המומלצת:** `@MY_SUPER_ADMIN_bot` (כבר פעיל, שלח לך את הקבלה!).

### מה הוא יכול לעשות עבורך:
- 📢 התראה על כל commit חדש (GitHub webhook → bot message)
- 🚨 התראה על errors ב-API (Sentry webhook)
- 🧾 התראה על כל תשלום חדש שהתקבל (כמו שקרה היום)
- 📊 דוח יומי: כמה משתמשים חדשים, כמה קבלות, כמה errors
- 💬 אפשרות לשאול שאלות: `/status`, `/users`, `/revenue`

**איך להפעיל (40 דק' של קוד):**
1. ליצור `ops/notifications_bot.py` — מאזין ל-webhooks
2. רישום ב-GitHub: Settings → Webhooks → `https://slh-api.../api/hooks/github`
3. רישום ב-Sentry: alerts → webhook → `https://slh-api.../api/hooks/sentry`
4. רישום ב-Railway: project → deploy webhooks

**אני יכול להכין את זה בקריאה הבאה שלך.** אגיד את זה "משימה #16" ברשימה.

---

## 🔗 שושלת עבודה (ככה שכל אחד יכול להמשיך)

```
User → GitHub Issue / Bug Report
           │
           ▼
    Triage (agent-brief.html)
           │
           ▼
    AI agent picks task (from TEAM_TASKS.md)
           │
           ▼
    Branch: feature/XXX (automatic)
           │
           ▼
    Commit with conventional message
           │
           ▼
    Push → CI runs tests (GitHub Actions)
           │
           ▼
    PR to master → Railway auto-deploy
           │
           ▼
    Notification bot → @MY_SUPER_ADMIN_bot
           │
           ▼
    Osif reviews (5 דק') → merge
```

**מה שחסר כדי שזה יעבוד:**
- [ ] GitHub Actions workflow (אני אוסיף)
- [ ] `CONTRIBUTING.md` עם הוראות תרומה (אני אוסיף)
- [ ] תיעוד עבור כל AI agent (קיים — `agent-brief.html`)
- [ ] Permission model: מי יכול לעשות מה (אני אתכנן)

---

## 📅 Timeline מוצע עד Public Beta

| שבוע | מטרה |
|:----:|--------|
| **17.4-24.4** (עכשיו) | סגירת 5 הפריטים ה-🔴 + 10 משתמשים מוזמנים |
| **24.4-01.5** | ייצוב: 7 ימים בלי crash, monitoring פעיל |
| **01.5-15.5** | Public Beta: [slh-nft.com](https://slh-nft.com) פתוח לכולם |
| **15.5-01.6** | Feedback round #1: 50+ משתמשים |
| **01.6-15.6** | v1.0.0-beta.2 — תיקונים + AIC mint |
| **15.6-01.7** | Launch marketing: 10 blog posts, 3 videos |
| **01.7-15.7** | v1.0.0 GA — Certik-ready |

---

## 🛡 מה מגן על היציבות

1. **Idempotent DB operations** — כל insert עם ON CONFLICT, לא נופל פעמיים
2. **Dual-key admin rotation** — 24 שעות לעדכן בלי downtime (יש לך!)
3. **Frontend/backend decoupling** — GitHub Pages אף פעם לא נופל
4. **Public BSC RPCs** — 3 fallbacks (Binance, Ninicoin, Defibit)
5. **Redis + Postgres separation** — אם Redis נופל, Postgres ממשיך
6. **`.env` not in git** — סודות בטוחים

---

## 🎨 Track 7 · Creator Economy (נוסף 2026-04-17 ערב)

### הרעיון
כל תמונה = NFT עם **סיפור** + **מחיר** + קישור לקורס (אופציונלי). יוצר שתמונה שלו נמכרה — צובר XP לפי ROI.

### המימוש
| # | מה | זמן | תלות |
|---|-----|:---:|------|
| 7.1 | `/sell.html` — העלאת תמונות ציבורית (רב-תמונתי, תיאור, מחיר, קישור לקורס) | 90 דק' | POST /api/marketplace/list קיים |
| 7.2 | `/gallery.html` — גלריה ציבורית של כל ה-NFTs המאושרים | 60 דק' | GET /api/marketplace/items קיים |
| 7.3 | `/me/shop.html` — חנות אישית לכל משתמש (קטלוג + stats) | 90 דק' | `/api/marketplace/my-listings/{uid}` קיים |
| 7.4 | XP = ROI metric | 60 דק' | טבלה חדשה `user_roi_snapshot` |
| 7.5 | SLH Index widget | 30 דק' | view API + widget בדף ראשי |
| 7.6 | Image sales tracking + `nfty_sales` table | 45 דק' | extend nfty-bot |

**סה"כ:** ~6 שעות עבודה לכל ה-Creator Economy.

### XP Formula
```python
user_xp = total_current_value / total_fiat_invested  # ratio, not percentage
# xp > 1.0 = profit, xp < 1.0 = loss, xp = None = no activity yet
```

### SLH Index Formula
```python
slh_index = median(user_xp for user in active_users if user_xp is not None)
# Displayed: "SLH Index: 1.47 ↑ 2.3% today"
# Updated every hour via background job
```

### משווה ל-S&P 500
- S&P 500 = מדד ממוצע מניות — משקף בריאות כלכלית
- SLH Index = מדד ממוצע ROI משתמשים — משקף בריאות הקהילה
- >1.0 = הקהילה מרוויחה · <1.0 = בועה/בעיה · 2.0 = ממוצע הכפיל השקעה

---

## 📝 לקריאה הבאה

בקש ממני:
1. "תכין CHANGELOG.md + tag v0.9.0-alpha"
2. "תכין GitHub Actions workflow לבדיקות"
3. "תכין notifications_bot.py לבוט הייעודי"
4. "תכין CONTRIBUTING.md"

כל אחד מהם 15-40 דקות עבודה. אחרי 2-3 מאלה — אתה במצב מלא של Beta-ready.

---

**תודה על האמון 🙏 — אתה בונה משהו שאנשים יצטרכו בעוד 10 שנים.**
