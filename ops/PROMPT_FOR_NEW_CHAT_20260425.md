# Prompt for New Chat — Copy-paste this into a fresh Claude/AI session

────────────────────────────────────────────────────────────────────────
COPY EVERYTHING BELOW THIS LINE INTO THE NEW CHAT
────────────────────────────────────────────────────────────────────────

אני אוסיף — Telegram ID 224223270, @osifeu_prog. אני בעלים יחיד של פרויקט SLH Spark — אקוסיסטם השקעות קריפטו בישראל. הפרויקט יושב ב-`D:\SLH_ECOSYSTEM\`. שני repos: `github.com/osifeu-prog/slh-api` (Railway) ו-`github.com/osifeu-prog/osifeu-prog.github.io` (GitHub Pages → slh-nft.com). API ב-`slh-api-production.up.railway.app`.

**הסשן הקודם רץ ~14 שעות והשאיר handoff מלא.** קרא לפני שאתה עושה משהו:
1. `D:\SLH_ECOSYSTEM\ops\SESSION_HANDOFF_20260425_FULL.md` — סיכום מלא של מה נעשה ומה נפתח
2. `D:\SLH_ECOSYSTEM\ops\SYSTEM_ALIGNMENT_20260424.md` — coordination בין סוכנים מקבילים
3. `D:\SLH_ECOSYSTEM\ops\KNOWN_ISSUES.md` — 27 פריטים מאומתים, 4 נסגרו אתמול
4. `D:\SLH_ECOSYSTEM\ops\OPS_RUNBOOK.md` — איך להריץ + לפרוס את המערכת

## מצב נוכחי (verified live ב-2026-04-25 12:00)

✅ **עובד:** `/api/health`, `/api/miniapp/health` (Gateway loaded), `/api/swarm/stats`, `/api/marketplace/items` (5 פריטים), `/api/events/public`. כל עמודי ה-Mini App + master dashboard `/my.html` + control centers — 200 OK.

🔴 **חוסם 1 — קריטי:** `@SLH_Claude_bot` בלולאת קריסה (RestartCount=13). הטוקן ב-`D:\SLH_ECOSYSTEM\slh-claude-bot\.env` מחזיר 401 Unauthorized מ-Telegram. נדרש: BotFather → /mybots → SLH_Claude → API Token → revoke + new → paste ל-.env → `docker compose up -d --build slh-claude-bot`.

🔴 **חוסם 2 — חומרה:** ה-ESP החדש שאני חיברתי מציג רק רצועה כחולה במקום ה-SLH OS. ניסיתי ILI9341 + ILI9341_2 drivers, וניסיתי setRotation 0/1/3 — אף אחד לא תיקן. הסיבה הסבירה: זה CYD variant אחר ממה שתיקנתי לבד לפני שבוע (אולי ST7789 / ST7796 במקום ILI9341). חסום עד שאני אשלח תמונה של גב הלוח עם ה-IC chip markings.

🟡 **חוסמים 3-5 (אני מבצע):** Railway env vars: `TELEGRAM_BOT_TOKEN` + `SMS_PROVIDER=inforu` + creds. BotFather: Mini App URL ל-`@WEWORK_teamviwer_bot` → `https://slh-nft.com/miniapp/dashboard.html`.

## מה נשגר בסשן הקודם (commits)

**slh-api** (Railway):
- `afc2354` SMS provider + Telegram Mini App gateway
- `50a4555` gateway audit schema fix
- `5abade2` PH2-4 admin endpoints security (header auth)
- `f77f35c` Swarm Phase-1 API — 8 endpoints
- `e0d0da9` claude-bot /swarm command
- `add3592` claude-bot clean /start + /control + /ps fallback

**website** (GitHub Pages):
- `9feb3bc` Mini Apps (dashboard/wallet/device + initData shim)
- `080d647` marketplace.html with real API data
- `fc2f4cb` `/my.html` master dashboard (single bookmark for all status)
- `07665f4` Swarm Mini App + my.html section

## איך לעבוד איתי (חוקים)

- **תגיב בעברית.** הקוד והcommits באנגלית. UI בעברית.
- **פעולה ישירה.** אל תסביר 3 פסקאות לפני שאתה עושה. "כן לכל ההצעות" = תתחיל לבצע.
- **never paste secrets** — לא בצ'אט, לא ב-commits. אם אני מדביק secret בטעות, תעצור ותבקש סיבוב.
- **Railway = ROOT main.py.** תמיד `cp api/main.py main.py` לפני push.
- **No fake data.** אם API לא מחזיר ערך, תציג `--` או `[DEMO]`. אסור להמציא מספרים.
- **Hebrew UI לא promises 65% APY** — זה regulated בישראל. תמיד "dynamic yield revenue-share".
- **GUARD_CONFIRMED=1 git commit** אם הcommit מעל 300 שורות (יש pre-commit hook).

## הצעד הראשון שלך — לא לעשות כלום עד ש:

1. תקרא את `ops/SESSION_HANDOFF_20260425_FULL.md` במלואו.
2. תרוץ `curl https://slh-api-production.up.railway.app/api/miniapp/health` ותאשר שעדיין `gateway_loaded:true`.
3. תשאל אותי: **(א) האם פתרתי את טוקן הבוט?** **(ב) האם יש לי תמונה של גב לוח ה-ESP?**
4. בהתאם לתשובות שלי, התחל לעבוד לפי סדר עדיפויות שמופיע ב-handoff (sect "WHEN STARTING THE NEXT SESSION").

## אם אני שואל "המשך" בלי הקשר

המשמעות: התקדם אוטונומית. הפעולות הבאות במקום בלי לחכות:
1. אם ההמלצה הבאה ב-handoff כתובה → תבצע אותה ישירות (כמו /api/team + team.html שעדיין לא נבנו)
2. אם אתה מזהה bug שאתה בטוח בו → תתקן + commit + push
3. אם אתה לא בטוח / יש שינוי גדול / נוגע בכסף → תעצור ותשאל
4. אחרי 3-4 פעולות אוטונומיות → תפיק סיכום קצר עם איזון "מה עשיתי / מה הלאה / איזה אישור צריך ממך"

## מה תוכל לעשות במידה ואני סוגר את הסשן באמצע

1. תפיק `ops/SESSION_HANDOFF_<date>_<topic>.md` עם מה נעשה + מה הופסק + איך להמשיך
2. תעדכן את `ops/SYSTEM_ALIGNMENT_20260424.md` תחת "Active Agents" עם הclaim שלך
3. אל תזרוק שינויים בעבודה — או commit + push, או `git stash push -m "<description>"` לסקירה הבאה
4. אם השארת קוד שלא נדחף, תכתוב את זה במפורש בסיום

────────────────────────────────────────────────────────────────────────
END OF PROMPT
────────────────────────────────────────────────────────────────────────
