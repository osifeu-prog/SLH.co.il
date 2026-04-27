# Vision & Next Steps — 2026-04-27

תוכנית פעולה מסודרת לאופציה C (service חדש ב-Railway), על בסיס המציאות המאומתת ב-`SYSTEM_REALITY_2026-04-27.md`.

החלטה: **C — service חדש בשם `slh-fastapi`, מחובר ל-`osifeu-prog/slh-api`, רץ במקביל ל-`SLH.co.il` הקיים, בלי לשבור כלום.**

---

## עקרונות

1. **לא לגעת במה שעובד** — `SLH.co.il` ו-`monitor.slh` ימשיכו לרוץ כרגיל. רק נוסיף service שלישי לקוד.
2. **כל צעד מאומת לפני המשך** — בכל שלב יש curl/test שמוכיח שזה עובד.
3. **rollback קל** — אם משהו נשבר, פשוט deletes את ה-service החדש; ה-`SLH.co.il` ימשיך כרגיל.
4. **שקיפות מול Osif** — כל פעולה ידנית ברורה, מתועדת, ובלי הפתעות.

---

## חלוקת תפקידים

| שלב | מי עושה |
|---|---|
| הכנות בקוד (ודיאות, תיקונים, commits) | **Claude** (קריאה/כתיבה לקבצים) |
| Push ל-GitHub (`git push origin master`) | **Osif** (Claude אין לו credentials) |
| יצירת Service חדש ב-Railway dashboard | **Osif** (Claude אין לו גישה) |
| הוספת Variables ב-Railway | **Osif** (Claude לא יכנס ל-dashboard) |
| בדיקות `curl` חיצוניות | **Osif** (sandbox של Claude חסום) |
| ניתוח התוצאות, תיקונים, deploy בעיות | **Claude** |
| תיעוד וסיום | **Claude** |

---

## שלב 1 — הכנות מקומיות (Claude עושה לבד, בלי שאתה מתערב)

זה החלק שאני יכול לעשות עכשיו, לפני שאתה לוחץ על שום דבר:

1. **לוודא ש-`api/main.py` ו-`main.py` (root) זהים** — Railway קורא מ-root, אבל הקוד המעוגן הוא ב-api/.
2. **לוודא ש-`Dockerfile` יבנה נכון** — לקרוא, לוודא ש-`COPY . .` מביא את `routes/`, `api/`, וכל ה-deps.
3. **לוודא ש-`railway.json` תקין** — מצביע ל-`Dockerfile`, healthcheck `/api/health`. ✅ אומת.
4. **לוודא ש-`requirements.txt` שלם** — fastapi, uvicorn, asyncpg, jwt, etc. ✅ אומת.
5. **להריץ analysis סטטי** — לבדוק שאין import errors, שכל הroutes מתחברים נכון.
6. **לכתוב קובץ `.env.railway-template`** — תבנית ברורה של כל המשתנים שיהיה צריך להוסיף.
7. **לעדכן את `CLAUDE.md`** — להסיר את הטענה השגויה "FastAPI on Railway" עד שזה באמת קורה.

**משך זמן:** 10-15 דקות עבודה שלי.

---

## שלב 2 — Commit + Push (Osif מבצע)

אחרי ששלב 1 נגמר, אתן לך קומנדה אחת להריץ. משהו כמו:

```powershell
cd D:\SLH_ECOSYSTEM

# בדיקה — לראות מה השתנה
git status

# Commit כל מה ששינינו
git add CLAUDE.md ops/SYSTEM_REALITY_2026-04-27.md ops/VISION_NEXT_STEPS_2026-04-27.md ops/.env.railway-template
git commit -m "docs: corrected system reality + Option C plan + Railway env template

- SYSTEM_REALITY documents the actual state (FastAPI not deployed yet)
- VISION_NEXT_STEPS lays out Option C: new Railway service for FastAPI
- CLAUDE.md updated to reflect reality (was aspirational)
- .env.railway-template lists all env vars needed for new service"

# Push ל-origin (slh-api repo, איפה ש-FastAPI חי)
git push origin master
```

**משך זמן:** 30 שניות שלך.

**אימות:** `git ls-remote origin master` יחזיר את ה-SHA החדש.

---

## שלב 3 — יצירת Service חדש ב-Railway (Osif מבצע, ~5 דקות)

זה החלק היחיד שדורש ממך לעבוד ב-Railway dashboard. אדריך אותך מסך-אחר-מסך:

1. כנס ל-Railway: https://railway.com/project/97070988-27f9-4e0f-b76c-a75b5a7c9673/production
2. בפרויקט `diligent-radiance/production` לחץ **"+ New"** (פינה ימנית עליונה).
3. בחר **"GitHub Repo"**.
4. בחר **`osifeu-prog/slh-api`**.
5. בחר branch **`master`**.
6. שם ה-service: **`slh-fastapi`** (כדי שלא יתבלבל עם `SLH.co.il`).
7. **אל תיתן לו לעשות deploy מיד** — לחץ Cancel/Skip על ה-modal של env vars אם יש כזה.

**אימות:** ה-service החדש מופיע ב-dashboard, בסטטוס "Failed" או "Building" (זה בסדר — הוא ייכשל בלי env vars; נתקן בשלב הבא).

---

## שלב 4 — הוספת Environment Variables (Osif מבצע, ~5 דקות)

ב-service `slh-fastapi`, לך ל-`Variables` והוסף:

### חובה (FastAPI לא יעלה בלעדיהם)

```
DATABASE_URL=<העתק מ-service Postgres → Connect → Postgres Connection URL>
REDIS_URL=<העתק מ-service Redis → Connect → Redis Connection URL>
PORT=8000
PYTHONUNBUFFERED=1
```

### Auth (יצירה מקומית, אחר כך הוספה)

```powershell
# הרץ אצלך לוקלית, העתק את הפלט ל-Railway:
python -c "import secrets; print('JWT_SECRET=' + secrets.token_hex(32))"
python -c "import secrets; print('ENCRYPTION_KEY=' + secrets.token_hex(32))"
python -c "import secrets; print('ADMIN_BROADCAST_KEY=' + secrets.token_urlsafe(32))"
python -c "import secrets; print('ADMIN_API_KEYS=' + secrets.token_urlsafe(24))"
python -c "import secrets; print('ORCHESTRATOR_KEY=' + secrets.token_urlsafe(32))"
python -c "import secrets; print('BOT_HEARTBEAT_KEY=' + secrets.token_urlsafe(32))"
```

### יוזריזם

```
INITIAL_ADMIN_PASSWORD=<סיסמה חזקה לכניסת Osif הראשונה>
INITIAL_TZVIKA_PASSWORD=<סיסמה חזקה לכניסת Tzvika הראשונה>
ADMIN_USER_ID=224223270
```

### חיצוניים (מ-`.env` המקומי שלך)

```
OPENAI_API_KEY=<העתק מ-D:\SLH_ECOSYSTEM\.env>
TELEGRAM_BOT_TOKEN=<אותו token שכבר ב-SLH.co.il service>
EXCHANGE_API_KEY=<אם יש לוגיקה Binance ב-FastAPI>
EXCHANGE_SECRET=<אם יש לוגיקה Binance ב-FastAPI>
```

**הערה חשובה:** אל תכתוב לי כאן בצ'אט את ה-tokens האמיתיים. שמור אותם ב-`.env` המקומי, אני אקרא אותם משם בעתיד אם אצטרך.

**אימות:** ב-Railway → Variables תראה את כל ה-keys (הערכים מוסתרים, זה תקין).

אחרי שמירת ה-vars, Railway אוטומטית יעשה deploy חדש.

---

## שלב 5 — אימות שה-FastAPI חי (5 דקות)

חכה ~2-3 דקות שה-deploy יסתיים. ב-Railway → ה-service החדש → Deployments → תראה Status: **Active** (ירוק).

הרץ אצלך:

```powershell
# Health endpoint - מבחן בסיסי
curl https://slh-fastapi-production.up.railway.app/api/health

# Expected: {"status":"healthy","timestamp":"...","version":"1.x.x"}

# Endpoint מורכב יותר - מבחן ש-DB מחובר
curl https://slh-fastapi-production.up.railway.app/api/system/status

# Expected: JSON עם api_up: true, db_up: true
```

**אם יש 404:** ה-deploy נכשל. לך ל-Deployments → Build Logs ושלח לי screenshot.

**אם יש 500:** שגיאת runtime. שלח לי Deploy Logs.

**אם יש JSON תקין:** 🎉 ה-FastAPI חי.

ה-URL החדש יהיה משהו בסגנון `https://slh-fastapi-production.up.railway.app`. ה-URL הישן `slhcoil-production.up.railway.app` ימשיך לעבוד כרגיל (עם הבוט הפשוט).

---

## שלב 6 — חיבור הפרונט (אחרי שהשרת חי)

ברגע שה-FastAPI עונה תקין, נצטרך לעדכן 2 מקומות:

1. `D:\SLH_ECOSYSTEM\website\js\shared.js` — איפה שמוגדר `API_BASE`. נשנה אותו ל-URL החדש.
2. `D:\SLH_ECOSYSTEM\.env` — נוסיף `SLH_API_BASE=https://slh-fastapi-production.up.railway.app` כדי ש-orchestrator ידע איפה לחפש.

לא נוגעים ב-`SLH.co.il` הישן — הוא ימשיך לרוץ. יום אחד נחליט מה לעשות איתו (אולי delete, אולי להמיר ל-monitoring service).

---

## שלב 7 — הפעלת Control Layer (העבודה מאתמול)

עכשיו, כשה-FastAPI חי, ה-`routes/system_status.py` יתחיל לענות על `/api/system/*`.

נריץ את ה-orchestrator לפי `SESSION_HANDOFF_20260427_v2.md` שלבים 4-5 (היחידים שיהיו רלוונטיים אחרי שה-FastAPI חי).

**משך זמן:** ~10 דקות.

---

## שלב 8 — תיעוד סיום

`Claude` יכתוב:

- `ops/SESSION_HANDOFF_20260427_v3_OPTION_C_DEPLOYED.md` — מה נעשה בסשן הזה
- עדכון `CLAUDE.md` עם ה-URL החדש ועם המציאות המעודכנת (FastAPI דווקא **כן** רץ ב-production עכשיו, מ-service חדש)
- עדכון `ops/SYSTEM_REALITY_2026-04-27.md` כ-historical (לתעד שזה היה המצב לפני התיקון)

---

## סיכום זמנים

| שלב | מי | משך |
|---|---|---|
| 1. הכנות מקומיות | Claude | 10-15 דק' |
| 2. Commit + Push | Osif | 30 שנ' |
| 3. יצירת service | Osif | 5 דק' |
| 4. Env vars | Osif | 5 דק' |
| 5. אימות `curl` | Osif | 2 דק' |
| 6. חיבור פרונט | Claude | 10 דק' |
| 7. Control Layer | Osif + Claude | 10 דק' |
| 8. תיעוד | Claude | 5 דק' |
| **סך הכל** | | **~50 דקות** |

---

## הסיכון

- **גבוה: 0** — אנחנו לא נוגעים ב-`SLH.co.il` הקיים בכלל. אם הכל נכשל, פשוט מוחקים את ה-service החדש ולא קורה כלום ל-production הקיים.
- **בינוני: 1** — אם ה-FastAPI יעלה אבל DB schema יהיה לא תואם, נצטרך migration. הסיכוי קטן כי `Postgres` כבר משרת בוטים שכותבים לאותם tables.
- **נמוך: 2** — Env vars שגויים → 500 errors → תיקון מהיר.

ה-rollback בכל מצב הוא: למחוק את service `slh-fastapi`. שום דבר אחר לא משתנה.

---

## שאלות שצריך תשובה ממך לפני שמתחילים

1. **האם להמשיך עכשיו או למחר?** (אני מוכן עכשיו אם אתה מוכן.)
2. **האם הסיסמאות הקיימות ב-.env המקומי שלך לעבודה בפועל (`OPENAI_API_KEY` וכו') בתוקף?** (כדי שלא נצטרך לחפש אותן).
3. **האם יש לך גישה ל-Railway dashboard עכשיו, או שאתה רוצה ש"שלב 3" ו"שלב 4" יחכו?**
