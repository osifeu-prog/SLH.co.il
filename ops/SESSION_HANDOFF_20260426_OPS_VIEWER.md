# Session Handoff — Ops Docs Viewer Fix

**Date:** 2026-04-26
**Session focus:** `website/ops-viewer.html` — broken auto-links + hardcoded doc list
**Outcome:** ערוך מקומית, מאומת, **לא commit-ed עדיין** (deploy ידיים של Osif)

---

## 1. ההקשר — מה הניע את העבודה

ה-screenshot שהדבקת בתחילת הסשן הראה את `ops-viewer.html` מרנדר את `HANDOFF_PROMPT_FOR_NEW_SESSION.md` עם קישורים שבורים — `[bot.py](http://bot.py)`, `[CONTROL.md](http://CONTROL.md)`, `[20260424.md](http://20260424.md)`, `[ב-bot.py](http://ב-bot.py)`, `[slh-nft.com](http://slh-nft.com)` (פרוטוקול שגוי). שני בעיות נוספות זוהו תוך כדי:

1. ה-"Quick Jump — Key Docs" קבוע ב-HTML (10 פריטים) — מסמכים חדשים ב-`ops/` לא מופיעים בתפריט.
2. autolinks אמיתיים מקבלים פרוטוקול `http://` במקום `https://`.

---

## 2. ההחלטה (AskUserQuestion → "כל ההצעות")

תוקנו שלושה דברים בערוך אחד:

- **Surgical autolink cleanup** (לא לכבות `gfm: true` כי אז tables ו-task lists ייפלו).
- **Auto-discover ops/*.md** מ-GitHub Contents API של ה-website repo (slh-api repo פרטי).
- **http→https upgrade** ל-autolinks ששרדו.

---

## 3. שינויים — `D:\SLH_ECOSYSTEM\website\ops-viewer.html`

| בלוק | מיקום | מה |
|---|---|---|
| CSS | בתוך `<style>` ליד הסטיילים של `.doc-list` | `.all-docs` (details/summary disclosure עם רוטציה ▸→▾), `.muted` (טקסט עזר) |
| Markup | החלפת `<nav class="doc-list">` (~lines 261-275) | כותרת `Quick Jump — Key Docs` → `Featured`. הוספת `<details class="all-docs">` עם `<ul id="doc-links-auto">` |
| JS active selector | בתוך `loadDoc()` | הסלקטור מתעדכן: `#doc-links a[data-doc], #doc-links-auto a[data-doc]` |
| JS cleanup pass | אחרי הפוסט-פרוססור הקיים של relative `.md` | מסיר `<a>` עם TLD-סיומת-קובץ (`py md js ts jsx tsx css scss html json yaml yml toml sh ps1 bat env txt log sql xml lock go rs java rb php`) או דומיין לא-ASCII (קידומת עברית כמו `ב-bot.py`); שורדים: upgrade `http://` → `https://` |
| JS loadDocIndex() | פונקציה חדשה לפני `loadDoc(getQueryParam('file'))` | `fetch('https://api.github.com/repos/osifeu-prog/osifeu-prog.github.io/contents/ops')` → סינון `.md` → dedupe מ-Featured → sort יורד (newest filenames first) → render עם 📄 prefix. fallback שקט עם הודעה "unavailable" אם API נכשל |

---

## 4. אימות מקומי (port 8899, `python -m http.server`)

| בדיקה | תוצאה |
|---|---|
| broken auto-links ב-5 מסמכי ops אמיתיים | **0** (CONTROL, MASTER_FINAL_HANDOFF, SYSTEM_ALIGNMENT, SESSION_CLOSURE, COMMAND_CENTER_SETUP, STATUS_REPORT) |
| broken auto-links בקלט סינתטי "רע" | **0** (`bot.py`, `CONTROL.md`, `ב-bot.py`, `20260424.md` — כולם עברו דרך הפילטר) |
| `<a href="http://...">` ששרד | **0** — הכל עבר ל-`https://` |
| https אמיתיים שלא נפגעו | ✅ 7 ב-MASTER, 6 ב-STATUS, 3 ב-CLOSURE, 2 ב-CONTROL |
| GFM tables + inline code + task-lists | ✅ (snapshot מאשר rendering נכון) |
| Featured list (10 פריטים) | ✅ ללא שינוי |
| Auto-discovered list | ✅ 10 פריטים, ממויינים מהחדש לישן: TELEGRAM_CONTROL_GUIDE → STATUS_REPORT → SPEC_3BOT_ROTATION → SESSION_SUMMARY → PAGE_INVENTORY → MASTER_PROMPT → HANDOFF_PROMPT_FOR_NEW_SESSION → FINAL_STATE → CUSTOMER_PROSPECTUS → CONTROL |
| Click navigation על auto-link | ✅ URL מתעדכן, content נטען, active-highlight עובר ל-auto-list |
| Console errors | אפס |

---

## 5. תובנה — ה-bug המקורי כנראה לא היה ב-marked

בדיקת marked v12 תחת `gfm: true` לא משחזרת את `bot.py` → `[bot.py](http://bot.py)`. ה-URL tokenizer של marked דורש `http://`/`https://`/`www.` prefix כדי לבצע autolink — `bot.py` בלבד לא מספיק. הסיכוי הסביר: ה-chat client (Claude.ai/דומה) הוסיף את הקישורים השבורים בעת הצגת הטקסט שהדבקת לאותה הודעה.

**עדיין שווה לתקן** כי:
- הגנה דפנסיבית מפני תוספי autolink אגרסיביים יותר בעתיד.
- ה-`http://` → `https://` upgrade שימושי בפועל (כל בעלי ה-bare URLs עוברים ל-https).
- הרשימה הדינמית היא win לעצמה — לא צריך לערוך HTML כל פעם שמוסיפים ops doc.

---

## 6. שלבי deploy — לעשות ידנית

```powershell
cd D:\SLH_ECOSYSTEM\website
git diff ops-viewer.html              # סקירה אחרונה
git add ops-viewer.html
git commit -m "ops-viewer: strip bogus auto-links + auto-discover docs from /ops"
git push origin main
```

GitHub Pages יפרוס תוך דקה-שתיים. אימות אחרי deploy:

1. https://slh-nft.com/ops-viewer.html?file=CONTROL.md → אין `href="http://`
2. פרוש "All ops/*.md (auto-discovered)" → אמורים להופיע ~10 פריטים
3. לחיצה על פריט אוטומטי → טעינה תקינה + active highlight

---

## 7. קבצים

| קובץ | מצב |
|---|---|
| `D:\SLH_ECOSYSTEM\website\ops-viewer.html` | ✏️ ערוך, **לא commit-ed** |
| `D:\SLH_ECOSYSTEM\ops\SESSION_HANDOFF_20260426_OPS_VIEWER.md` | 📄 הקובץ הזה |
| `C:\Users\Giga Store\.claude\plans\ops-docs-viewer-twinkly-thimble.md` | 📋 plan מאושר (Plan Mode artifact) |

---

## 8. מה שלא נגעתי בו (פתוחים מהסשנים הקודמים — קונטקסט בלבד)

- 🔴 **Token rotation @SLH_Claude_bot** (P0 — BotFather → Revoke → עדכן `.env` → `docker compose up -d --force-recreate claude-bot`)
- 🔴 **Railway redeploy slh-api** (תקוע מ-097eafe curly-quote SyntaxError)
- 🟡 **30 bot tokens נוספים** דורשים rotation
- 🟡 **Multi-domain CNAME ל-`slh.co.il`** (קובץ `D:\SLH_ECOSYSTEM\website\CNAME` כרגע על `slh-nft.com`)
- 🟡 **`/git` בבוט timeout 15s** (commit קיים — דרוש `docker compose build claude-bot && up -d --force-recreate`)

---

## 9. צ'קליסט לסשן הבא

- [ ] `cd D:\SLH_ECOSYSTEM\website && git status` — אמור להראות `ops-viewer.html` modified
- [ ] commit + push → אימות על https://slh-nft.com
- [ ] (אם רוצים) להעתיק את `SESSION_HANDOFF_20260426_OPS_VIEWER.md` גם ל-`website/ops/` (לפי flow המראה) או לתת לסקריפט המראה לעשות בעת ה-commit הבא ל-slh-api repo

---

**מי עבד:** Claude (Sonnet 4.5)
**הוראות שמירת context:** ה-plan + handoff מספיקים לפיק-אפ. אם הסשן הבא נכנס לעריכה נוספת של `ops-viewer.html`, לקרוא קודם את הקובץ (3 בלוקים חדשים) — לא להניח שהוא במצב הקודם.
