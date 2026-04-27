# SLH System Reality — 2026-04-27

תיעוד מדויק של מצב המערכת בפועל, על בסיס **הוכחה מ-Railway HTTP logs** (לא ניחוש, לא חזון).

נכתב: 2026-04-27 בוקר, אחרי 5 שעות תיקונים שכשלו והתנגשות בין מסמכים למציאות.

---

## 1. ההוכחה הקשה (HTTP logs מ-Railway, 2026-04-26 → 27)

מתוך הצילומים שאתה שלחת ב-bookoth של 2026-04-27, מ-service `SLH.co.il` (deploy `5d40f976`):

```
[27/Apr/2026 00:22:45] code 404, message File not found
[27/Apr/2026 00:22:45] "GET /api/health HTTP/1.1" 404 -
[27/Apr/2026 00:22:45] "GET /api/system/status HTTP/1.1" 404 -
[27/Apr/2026 00:22:46] "GET /api/system/bots HTTP/1.1" 404 -
[27/Apr/2026 00:22:46] "GET /api/system/stats HTTP/1.1" 404 -
[27/Apr/2026 00:22:46] "GET /api/courses/ HTTP/1.1" 404 -
[27/Apr/2026 00:23:13] "GET /api/health HTTP/1.1" 404 -
[27/Apr/2026 00:23:14] "GET /api/therapists/public HTTP/1.1" 404 -
```

**ניתוח:**

1. **כל `/api/*` מחזיר 404** — אין FastAPI router שמטפל בנתיבים האלה.
2. **פורמט השגיאה** (`code 404, message File not found`) הוא הפורמט של Python `http.server` או `SimpleHTTPServer`. FastAPI יחזיר JSON: `{"detail":"Not Found"}`.
3. **המסקנה:** מה שרץ ב-`slhcoil-production.up.railway.app` הוא שרת קבצים סטטי, לא ה-FastAPI שלך.

ה-source ב-Railway: **`osifeu-prog/SLH.co.il` @ `main`**, deploy `fd0571e6...` (עם `/railway.json` משלו, Dockerfile משלו).

הקוד שלך (`D:\SLH_ECOSYSTEM\main.py`, FastAPI עם ~230 endpoints, 11,765 שורות) מעולם לא נדחף לריפו הזה. הוא נדחף ל-`osifeu-prog/slh-api` (remote `origin`), שאין שום service ב-Railway שמחובר אליו.

---

## 2. מפת הריפוז — מי דוחף לאן ומי קורא ממה

| ריפו GitHub | תיקייה מקומית | תוכן | מי קורא ממנו ב-production |
|---|---|---|---|
| `osifeu-prog/slh-api` | `D:\SLH_ECOSYSTEM` (remote `origin`) | FastAPI 230 endpoints, 25 בוטים, routes/, scripts/, ops/, **Dockerfile + railway.json תקינים** | **אף אחד** ❌ |
| `osifeu-prog/SLH.co.il` | `D:\SLH_ECOSYSTEM` (remote `slhcoil`, אבל אין branch מקומי שמסונכרן) | בוט Telegram פשוט + http.server סטטי | Railway service `SLH.co.il` ✅<br>Railway service `monitor.slh` ✅ |
| `osifeu-prog/osifeu-prog.github.io` | `D:\SLH_ECOSYSTEM\website` | 140+ דפי HTML | GitHub Pages (`slh-nft.com`) ✅ |

הקונפיגורציה ב-`D:\SLH_ECOSYSTEM\.git\config` (verified):
```ini
[remote "origin"]
    url = https://github.com/osifeu-prog/slh-api.git
[remote "slhcoil"]
    url = https://github.com/osifeu-prog/SLH.co.il.git
```

Branch מקומי: `master` → `origin/master` (push ל-`slh-api`, לא ל-Railway).

---

## 3. מפת Railway — מה רץ באמת

פרויקט: **`diligent-radiance` / `production`** (id: `97070988-27f9-4e0f-b76c-a75b5a7c9673`)

| Service | Source | Status | Domain |
|---|---|---|---|
| `Postgres` | Railway managed | Online | (פנימי) |
| `Redis` | `redis:8.2.1` (Docker Hub) | Online | (פנימי) |
| `SLH.co.il` | `osifeu-prog/SLH.co.il` @ `main` | Online | `slhcoil-production.up.railway.app` + `www.slh.co.il` |
| `monitor.slh` | `osifeu-prog/SLH.co.il` @ `main` | Online (with NetworkErrors) | `monitor.slh.co.il` |

**הערה חשובה:** שני ה-services המבוססי-קוד מחוברים לאותו ריפו `SLH.co.il`. אין שום service ב-Railway שמחובר ל-`slh-api` (איפה שכל ה-FastAPI שלך גר).

Variables קיימות ב-`SLH.co.il` service: `DATABASE_URL`, `DATABASE_PUBLIC_URL`, `REDIS_URL`, `REDIS_PUBLIC_URL`, `OPENAI_API_KEY`, `TELEGRAM_BOT_TOKEN`.

Variables **חסרות** (יידרשו ל-FastAPI כשנפרוס): `JWT_SECRET`, `ADMIN_API_KEYS`, `ENCRYPTION_KEY`, `ADMIN_BROADCAST_KEY`, `INITIAL_ADMIN_PASSWORD`, `INITIAL_TZVIKA_PASSWORD`, `ADMIN_USER_ID`, `ORCHESTRATOR_KEY`, `BOT_HEARTBEAT_KEY`.

---

## 4. מה כן עובד עכשיו

- ✅ `www.slh.co.il` — האתר עולה, 140+ דפי HTML מ-GitHub Pages
- ✅ `slhcoil-production.up.railway.app` — http.server סטטי + בוט Telegram (לא FastAPI)
- ✅ `monitor.slh.co.il` — בוט Telegram (עם שגיאות network רגעיות, polling אגרסיבי)
- ✅ Postgres + Redis ב-Railway זמינים
- ✅ דומיינים מנותבים נכון
- ✅ 25 בוטים מ-`docker-compose.yml` רצים מקומית על המחשב שלך (Docker Desktop confirmed: `slh-nifty-new`, `slh_ecosystem-device-registry`, `slh_ecosystem-ton-mnh-bot`, `slh_ecosystem-userinfo-bot`...)

## 5. מה לא עובד (וזה בסדר — זה גילוי, לא כשלון)

- ❌ FastAPI עם ~230 endpoints — קיים, מוכן, **לא ב-production**
- ❌ Endpoints כמו `/api/health`, `/api/courses`, `/api/system/status` — לא נגישים מבחוץ
- ❌ קוד Control Layer מאתמול (`routes/system_status.py`, scripts/slh-orchestrator.py) — נכתב, מחכה לדיפלוי
- ❌ הסקריפט `deploy-now.ps1` — דוחף ל-`origin` שאף Railway service לא מקשיב לו
- ❌ ה-CLAUDE.md הנוכחי טוען "API: FastAPI on Railway, ~230 endpoints" — זו שאיפה, לא מציאות

---

## 6. למה זה קרה

זה דפוס נפוץ בפרויקטים שגדלים מהר:

1. **התחלת בריפו אחד** (`SLH.co.il`) שהיה הבוט הפשוט ↔ אתר
2. **הרחבת מ-`SLH.co.il` רק את הפרונט** (44→140 דפים)
3. **בנית את ה-FastAPI ב-ריפו חדש** (`slh-api`) שהיה אמור להחליף את הבוט הפשוט
4. **בכל הזמן הזה Railway המשיך להריץ את `SLH.co.il`** כי אף אחד לא שינה את ה-Source
5. **המסמכים תיארו את החזון** ("FastAPI on Railway") במקום את המצב

זו לא בעיה רעה. זו **סגירת פער** שצריך לעשות בסשן ייעודי.

---

## 7. מה שהמסמכים הקיימים מתארים — ולא קיים בפועל

| מסמך | טוען | מציאות |
|---|---|---|
| `CLAUDE.md` | "API: FastAPI on Railway, ~230 endpoints" | FastAPI לא ב-Railway |
| `CLAUDE.md` | "Production URL: slhcoil-production.up.railway.app" | URL חי, אבל לא ה-FastAPI |
| `SESSION_HANDOFF_20260427_v2.md` | "5-step activation sequence" | מניח ש-FastAPI חי, וזה לא נכון |
| `SESSION_HANDOFF_20260427.md` | "verify with curl https://slhcoil-production.up.railway.app/api/health" | ה-curl יחזיר 404 |
| `routes/system_status.py` | router מוכן | קיים מקומית, לא נגיש כי FastAPI לא רץ |
| `command-center.html` | UI שמדבר עם `/api/system/*` | UI מוכן, אבל ה-API מחזיר 404 |

---

## 8. ההיפותזה על "monitor.slh"

ה-service `monitor.slh` ב-Railway רץ בוט Telegram (לא monitor של API). מהלוגים אנחנו רואים `python-telegram-bot` עושה `getUpdates` נגד `bot8724910039:AAH0CGRqGmutTCit...`. זה כפילות עם service `SLH.co.il` שגם הוא בוט. אולי מיותר. שווה לבדוק אחרי שהדיפלוי החדש יעלה.

---

## 9. הצעד הבא — לסגור את הפער (אופציה C)

ראה `VISION_NEXT_STEPS_2026-04-27.md`.

הבחירה שלך אחרי השינה: **C — service חדש ב-Railway שמחובר ל-`slh-api`**, רץ במקביל ל-`SLH.co.il`. בלי לשבור כלום.

---

**מסמך זה נכתב על בסיס:**
- צילומי מסך Railway dashboard ששלחת
- HTTP logs של `SLH.co.il` service (קריטי — ההוכחה הסופית)
- HTTP logs של `monitor.slh` service
- קריאת `D:\SLH_ECOSYSTEM\.git\config` ו-refs
- קריאת `D:\SLH_ECOSYSTEM\Dockerfile`, `railway.json`, `requirements.txt`, `main.py`
- קריאת `CLAUDE.md` ו-2 ה-handoffs מ-2026-04-27
- Docker Desktop screenshot (44 images, מאשר 25 בוטים מקומית)
