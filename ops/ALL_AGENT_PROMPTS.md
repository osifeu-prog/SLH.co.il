# 🤖 SLH · All Agent Prompts · אינדקס מרכזי
> **רשימת כל הפרומפטים לסוכנים.** העתק את הקישור הרלוונטי ושלח לכל סוכן שאתה רוצה להכניס לעבודה.

---

## 📋 5 פרומפטים · איזה לבחור?

| # | פרומפט | למי | מתי | זמן משימה |
|---|--------|-----|-----|------|
| 1 | **MASTER_EXECUTOR** | Senior executor agent · כל מערכת | למי שבונה פיצ'רים כולל-מערכת | 2-8 שעות לפיצ'ר |
| 2 | **LEDGER_GUARDIAN_ESP** | Infrastructure agent · מחשב שני | בוטים + DevOps + ESP32 | 4-8 שעות |
| 3 | **ESP_QUICKSTART** | Quickstart · PowerShell exact | התחלה מהירה למחשב חדש | 30 דק' setup |
| 4 | **SYSTEM_SCAN** · *חדש* | Auditor agent · סריקה + דיווח | בדיקת בריאות מערכת | 1-2 שעות |
| 5 | **TASK_SUDOKU** | Task-specific · engagement | הוספת Sudoku כמשחק | 5 שעות |

---

## 🔗 קישורים להעתקה ישירה

### פרומפט 1 · Master Executor (הכי מקיף)
**העתק לסוכן:** ChatGPT, Claude.ai, Gemini, Cursor, Copilot Agent

```
https://raw.githubusercontent.com/osifeu-prog/slh-api/master/ops/MASTER_EXECUTOR_AGENT_PROMPT.md
```

או תגיד לסוכן:
> "פתח את הקישור הזה, הדבק את התוכן כ‑system prompt שלך, ואז תגיד 'מוכן'."

**כיסוי:** identity, 4 system layers, tech stack, 10+ integrations, Railway env vars, authorization matrix, execution mode, output format, emergency overrides, 5 tracks.

---

### פרומפט 2 · Ledger + Guardian + ESP (לסוכן על מחשב שני)
**העתק לסוכן:** מי שמתחיל לעבוד על הבוטים מ‑D:\ על מחשב משני

```
https://raw.githubusercontent.com/osifeu-prog/slh-api/master/ops/LEDGER_GUARDIAN_ESP_AGENT_PROMPT.md
```

**כיסוי:** 3 סבסיסטמים קריטיים · Ledger bot · Guardian bot · ESP device-registry · משימות מוכנות לכל אחד.

---

### פרומפט 3 · ESP QuickStart (PowerShell מדויק)
**העתק לסוכן:** כשהוא צריך לדעת *בדיוק* מה להדביק

```
https://raw.githubusercontent.com/osifeu-prog/slh-api/master/ops/ESP_QUICKSTART.md
```

**כיסוי:** git clone commands · docker compose · Twilio integration · 3 tasks ready-to-pick.

---

### פרומפט 4 · System Scan · **חדש**
**העתק לסוכן:** advisor/auditor שסורק את המערכת ומחזיר דוח מסודר

```
https://raw.githubusercontent.com/osifeu-prog/slh-api/master/ops/SYSTEM_SCAN_AGENT_PROMPT.md
```

**כיסוי:** סריקת 178 endpoints · 70 pages · 6 tokens · 25 bots · בדיקת בריאות · zero-commits mode (advisor only).

---

### פרומפט 5 · Task Sudoku
**העתק לסוכן:** למי שרוצה משימה עצמאית של 5 שעות

```
https://raw.githubusercontent.com/osifeu-prog/slh-api/master/ops/TASK_SUDOKU_AGENT.md
```

**כיסוי:** סודוקו עם 3 רמות · AIC/REP rewards · leaderboard · DB schema · integration.

---

## 📣 הודעה מוכנה לשליחה לקבוצת עבודה / לכל סוכן

```
שלום 👋

אתה מצטרף לצוות SLH Spark. עבודתך תהיה מתועדת, מאובטחת, ומתוגמלת ב-AIC.

שלב 1 — הדבק את הפרומפט הבא כ-system prompt (copy מה-link):
[הדבק אחד מ-5 הקישורים למעלה]

שלב 2 — אחרי שהסוכן חוזר "מוכן":
- Master: "קח משימה #N מ-agent-brief"
- Ledger/Guardian/ESP: "התחל משימה Z.X מ-ESP_QUICKSTART"
- System Scan: "תסרוק הכל, תחזור עם דוח"
- Sudoku: "התחל MVP"

שלב 3 — הסוכן מדווח ב-end-of-session:
- Commits shipped
- Verification done
- Next recommended

🎯 Focus: ENTER → IDENTIFY → ACT → PAY → VALUE → RETURN

📍 Status: https://slh-nft.com/project-map.html
🎛 Control: https://slh-nft.com/mission-control.html
🏦 Tokens: https://slh-nft.com/admin-tokens.html
```

---

## 🧭 Decision tree · איזה פרומפט לכל מצב

```
סוכן חדש שאף פעם לא ראה SLH?
  ├── הוא יכול להריץ קוד? (Claude Code / Cursor)
  │   └── כן → Prompt #1 (Master Executor)
  │   └── לא (רק chat) → Prompt #4 (System Scan) · advisor mode
  │
  ├── הוא על מחשב שני ועובד על הבוטים?
  │   └── כן → Prompt #3 (ESP QuickStart) + Prompt #2 (Ledger/Guardian/ESP)
  │
  └── אתה רוצה לתת לו משימה קטנה עצמאית?
      └── Prompt #5 (Sudoku) או תיצור task-brief חדש בדומה
```

---

## 📊 Status tracking של כל הסוכנים

המקום המרכזי: `ops/AGENT_REGISTRY.json`
עמוד חזותי: [slh-nft.com/mission-control.html](https://slh-nft.com/mission-control.html) → Agents section
מפת משימות: [slh-nft.com/project-map.html](https://slh-nft.com/project-map.html)

---

## 🔐 אבטחה · לפני שאתה שולח פרומפט לסוכן

1. ✅ וודא שזה לא מחליף את השיחה הראשית שלי/שלך
2. ✅ הסבר לסוכן שהוא advisor **או** executor — לא שניהם
3. ❌ אל תשלח לסוכן שלא אמוּת את .env/secrets
4. ❌ אל תאפשר לסוכן Production Railway UI
5. ❌ אל תחשוף את קבוצת ההכרויות (`nKgRnWEkHSIxYWM0`) לסוכנים — זה פרטי

---

**Updated: 2026-04-17 · 18 commits shipped today · 178 endpoints live.**
