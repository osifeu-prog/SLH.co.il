# SLH Spark — Team Handoff Package · 2026-04-24

**מטרה:** חבילת דרופ-אוף מסודרת לחלוקה לצוות עובדים. כל אחד מקבל רק את הקובץ שלו.
**הקשר:** אחרי 8 לילות עבודה (17.4 → 22.4), הצטברו ~26 משימות פתוחות. Railway תקוע. Website חסר 3 דפים. עדיין אין deployment של 6 commits.

---

## 📋 מפת הקבצים

| # | קובץ | למי | זמן ביצוע | דחיפות |
|---|------|-----|-----------|---------|
| 0 | [MASTER_STATUS_REPORT.md](MASTER_STATUS_REPORT.md) | **Osif (קרא ראשון)** | 10 דק' קריאה | חובה |
| 1 | [DROP_OSIF_OWNER.md](DROP_OSIF_OWNER.md) | Osif בלבד — החלטות + גישות | 45 דק' | 🔴 חוסם הכל |
| 2 | [DROP_INFRA_DEVOPS.md](DROP_INFRA_DEVOPS.md) | Idan / IT (או חיצוני) | 3–4 שעות | 🔴 P0 |
| 3 | [DROP_CRM_BUSINESS.md](DROP_CRM_BUSINESS.md) | Eliezer (@P22PPPPPP, 8088324234) | 1–2 שעות | 🟡 P1 |
| 4 | [DROP_COMMUNITY_TELEGRAM.md](DROP_COMMUNITY_TELEGRAM.md) | Elazar (community lead) | 2–3 שעות | 🟡 P1 |
| 5 | [DROP_QA_TESTING.md](DROP_QA_TESTING.md) | Zohar / Yakir / אחיין (6466974138) | 1–2 שעות | 🟢 P2 |

---

## 🚦 סדר עבודה מומלץ

```
Osif קורא MASTER → מבצע DROP_OSIF → משחרר את Railway
         ↓
Infra/IT מריץ docker rebuild + firmware flash + secret rotation
         ↓
במקביל: CRM (Eliezer) + Community (Elazar) פועלים על משימות עצמאיות
         ↓
QA בודקים את הכל אחרי שה-deploys ירוקים
```

**עדיפות אבסולוטית ראשונה:** Osif משחרר את Railway (30 שניות במסך Railway). בלי זה — 6 commits + 2 features חדשות (CRM, control-layer) לא חיים באוויר.

---

## 🎯 תמונת מצב בלוק אחד

| תחום | סטטוס |
|------|-------|
| API Health | ✅ 200 (v1.1.0 ישן, אבל עובד) |
| Ambassador CRM | ❌ 404 — קוד דחוף אבל Railway תקוע |
| Mini App (/miniapp/*) | ❌ 404 — לא נדחף לאתר |
| Marketplace.html | ❌ 404 — קיים מקומי, לא נדחף |
| Website community | ✅ LIVE (שקרים הוסרו) |
| Pre-commit guard | ✅ פעיל מקומית |
| CRM Phase 0 code | ✅ כתוב, מוכן (5 endpoints) |
| ESP32 Firmware v3 | ✅ קוד מוכן, חסר flash פיזי |
| 130 משקיעים של Eliezer | ⏳ CSV חסר, API מוכן |

---

## 📎 קבצי מקור בקרוב (קיימים, לא חלק מהחבילה הזו)

- `ops/SESSION_FULL_CLOSURE_20260422.md` — מה קרה במפגש האחרון
- `ops/KNOWN_ISSUES.md` — 25 באגים מאומתים בקוד נוכחי
- `ops/OPS_RUNBOOK.md` — איך להפעיל הכל
- `ops/OPEN_TASKS_MASTER_20260421.md` — 26 משימות פתוחות
- `CLAUDE.md` — הוראות לסוכני AI

---

**נוצר:** 2026-04-24
**גרסה:** 1
**בעלים:** Osif Kaufman Ungar (@osifeu_prog, 224223270)
