# 🌙 Night 20.4.2026 · Pre-Sleep Sync (Claude Opus 4.7)
**Timestamp:** 2026-04-20 evening · **Agent:** Claude Opus 4.7 (1M context)
**Purpose:** הוכחת סינכרון מלא + רשימת מטלות לביצוע אוטונומי בזמן שאוסיף ישן.

---

## 1. מה אני יודע עכשיו (Sync verification)

### SLH_ECOSYSTEM (Production)
| מערכת | מצב | מקור אמת |
|---|---|---|
| API Health | 🟢 `{status:"ok", db:"connected", version:"1.1.0"}` | curl בזה הרגע |
| `/docs` | 🟢 404 (secured) | curl בזה הרגע |
| Marketplace | 🟢 5 items LIVE — ids 1-5 מוחזרים מ-`/api/marketplace/items` | curl בזה הרגע |
| Admin key rotation UI | 🟢 נפרש ב-`admin.html` + `routes/admin_rotate.py` (240 שורות) | NIGHT_20260420_OUTCOMES |
| `slh2026admin` purge | 🟢 10 מודולים מנוקים — fail-safe empty | NIGHT_20260420_OUTCOMES |
| Railway deploy | 🟢 `ed81daf` live | NIGHT_20260420_OUTCOMES |
| GitHub Pages | 🟢 `9ab68f6` pushed | NIGHT_20260420_OUTCOMES |

### SLH_GAME_TEST (Agent coordination system — מה שבנית הערב)
| רכיב | מצב | הערות |
|---|---|---|
| `ops/slh_core.ps1` | 🟢 228 שורות, 13 פונקציות | canonical engine |
| `state/agents.json` | 🟢 7 סוכנים רשומים | Owner, CoAgent, Agent1-2, Gemini, Grok_CoAgent, Copilot_Spark_Advisor |
| `state/tasks.json` | 🟢 9 משימות (T001-T009), כולן `Done` | ESP port, touch, LED, splash, upload |
| `game/web_sync/index.html` | 🟢 3597 bytes, observer dashboard | פועל על http://127.0.0.1:8089 |
| `game/web_sync/live_sync.json` | 🟢 44128 bytes, מסונכרן | מ-17:59 |
| `ops/slh_export_web.ps1` | 🟢 נוצר לפני רגע | 200 bytes |

### Blocked on Osif (מזיכרון Night 17.4 + 20.4)
- [ ] BotFather: רוטציית 5 tokens (`SLH_LEDGER` דחוף — 401)
- [ ] ANTHROPIC_API_KEY → `slh-claude-bot/.env`
- [ ] Admin password localStorage update אחרי הרוטציה בפועל
- [ ] Experts info: Tzvika + Zohar (5 שדות לכל אחד)
- [ ] אישור path for course id=1 (`[DEMO] מבוא ל-SLH`): Promote or Deactivate

---

## 2. בעיות שאיתרתי עכשיו (Issues spotted this pass)

### 🔴 Bug A — `slh-agent-glitch-handler.ps1` שבור
שורה 7 טוענת `agent_core.ps1` (ישן) במקום `slh_core.ps1` (canonical). זה בדיוק מה שאמרת קודם: "הפונקציות הישנות לא תמיד זמינות".

### 🟠 Bug B — `Export-LiveSyncJson` כותב ל-path לא נכון
`slh_core.ps1:206` כותב ל-`$global:SLHRoot\web\live_sync.json` אבל הדשבורד בפועל ב-`game\web_sync\`. כרגע `slh_export_web.ps1` מפצה ע"י copy ידני — אפשר לתקן בשורש.

### 🟡 Bug C — קבצים כפולים ב-ops
```
slh-monitor.ps1    (ישן, dash)   ⟷  slh_monitor.ps1   (חדש, underscore)
slh-recover.ps1    (ישן, dash)   ⟷  slh_recover.ps1   (חדש, underscore)
agent_core.ps1     (ישן)         ⟷  slh_core.ps1      (canonical)
```
הישנים עדיין יושבים בתיקייה ומתנגשים סמנטית.

### 🟡 Gap D — אין פקודת glitch אחידה שמדברת עם slh_core
מה שרצית בסבב הקודם.

---

## 3. מטלות שאני לוקח על עצמי הלילה

### 🟢 Tier A — בטוח לחלוטין, reversible, בלי צורך בהסכמה נוספת
1. **תקן `slh-agent-glitch-handler.ps1`** → טעינת `slh_core.ps1` במקום `agent_core.ps1`.
2. **צור `ops/slh_glitch.ps1`** — ורסיה באמנת underscore, מתואמת עם slh_core.
3. **תקן `Export-LiveSyncJson`** כך שיכתוב ל-`game\web_sync\live_sync.json` ישירות.
4. **צור `ops/slh_entry.ps1`** — פקודת כניסה אחידה לסוכן חדש (מאחדת Register+Heartbeat+Board+Tasks).
5. **ארכיב את הכפולים הישנים** אל `archive/deprecated_20260420/` (לא מחיקה — תמיד reversible).
6. **עדכן `Initialize-SLHProject`** להבטיח את `game\web_sync\` במקום/בנוסף ל-`web\`.
7. **הרץ smoke test** — register → heartbeat → glitch → recover → export → dashboard JSON תקין.
8. **כתוב `project_night_20260420_late.md`** בזיכרון + עדכן `MEMORY.md`.

### 🟡 Tier B — אעשה רק אם יוצא זמן ואם מאומת
9. **`verify_slh.py`** הרצה → לוודא שעדיין 11/12 pass.
10. **health ping** לכל ה-25 bots דרך `docker ps` (קריאה בלבד, בלי restart).
11. **grep ל-`slh2026admin`** במאגר כולו — לוודא שאין מופע ששרד.
12. **audit ל-`main.py` vs `api/main.py`** — האם עדיין מסונכרנים?

### 🔴 Tier C — לא עושה בלעדיך (דורש אישור ידני / מידע)
- ❌ רוטציית admin key בפועל (דורש localStorage אצלך)
- ❌ seed academia courses (דורש admin key שאין לי)
- ❌ onboard Tzvika / Zohar (דורש 5 שדות לכל אחד ממך)
- ❌ כל `git push` ל-slh-api או website
- ❌ Railway deploy / restart
- ❌ BotFather rotations
- ❌ broadcast ל-280 משתמשים
- ❌ מחיקת קבצים (רק archive)

---

## 4. מה אני **לא** עושה (גם אם תישן הרבה זמן)

| פעולה | סיבה |
|---|---|
| commit + push | CLAUDE.md קובע: רק אחרי אישור ספציפי |
| deploy ל-Railway | external side effect, לא reversible ברגע |
| שליחת הודעה לכל משתמש | blast radius = 280 אנשים |
| שינוי `.env` או tokens | יכול לשבור בוטים חיים |
| מחיקה של קובץ | רק `archive/deprecated_*/` — תמיד reversible |
| קפיצה ל-Tier 1 hardening (pg_dump cron, Sentry) | דורש סודות + דיון ארכיטקטוני אתך |

---

## 5. מה יחכה לך בבוקר

קובץ `ops/NIGHT_20260420_LATE_OUTCOMES.md` (אכתוב אותו כשאסיים) יכיל:
- diff מדויק של כל הקבצים שנגעתי
- output של smoke test
- רשימת כפולים שעברו לארכיון (path מלא)
- 3 פריטים מומלצים לבוקר (ordered by impact)
- זמן שנלקח על כל משימה

---

## 6. שאלה יחידה לפני שאני מתחיל

**אישור Tier A (1-8) ו-Tier B (9-12)?** אם כן — תגיד "כן", תסגור את הטרמינלים, ואני אתחיל מידית. אם אתה רוצה להוציא משהו מהרשימה או להוסיף — תגיד עכשיו.

ברגע שיש אישור, אתה יכול לישון רגוע. כל מה שאעשה הלילה reversible.
