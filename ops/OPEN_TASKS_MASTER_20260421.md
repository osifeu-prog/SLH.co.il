# OPEN TASKS MASTER — 2026-04-21 (סוף יום)

מקור: איחוד 4 דוחות סשן + זיכרון ארוך טווח + Explore על `44.txt` + `דוח יום ג.txt`.

---

## 🔴 BLOCKERS — דורש פעולה שלך (10-15 דק')

| # | פעולה | למה חוסם | איפה | זמן |
|---|-------|----------|------|-----|
| 1 | **Railway env batch** — עדכן `GUARDIAN_BOT_TOKEN=8521882513:AAG...`, הוסף `LEDGER_WORKERS_CHAT_ID`, `SLH_ADMIN_KEY`, `ADMIN_API_KEYS` | פותח admin 403, מחבר Guardian→workers, פותר את mismatch ה-auth ש-frontend נתקל בו | Railway dashboard → slh-api → Variables | 5 |
| 2 | **Guardian restart** | env החדשים ייקלטו | `docker compose restart guardian-bot` ב-`D:\telegram-guardian-DOCKER-COMPOSE-ENTERPRISE` | 2 |
| 3 | **localStorage paste** ב-`chain-status.html` | Dashboard לא נטען אדמין-כרטיסים | F12 → Console → `localStorage.setItem('slh_admin_password','QVUvE_3Nv4YmJM0SPf512YeNBlj3kDt2XI2ix1sBfF3R8b5FfpI-kw')` → F5 | 1 |
| 4 | **ledger-bot TOKEN fix** | Container ב-restart loop (RestartCount=169) — `TokenValidationError: TOKEN=None` בזמן שיש `BOT_TOKEN` | יישר compose/env: הוסף `TOKEN=${BOT_TOKEN}` או תקן את הקוד לקרוא `BOT_TOKEN` | 5 |

---

## 🟡 ידני חובה — גישה שלך (30 דק' סה"כ)

| # | פעולה | הקשר |
|---|-------|------|
| 5 | `docker compose up -d --build` על 9 קונטיינרים דרך `ops/PHASE_0B_REBUILD_BOTS.ps1` (DryRun נתמך) | Phase 0B deploy |
| 6 | `curl /api/admin/link-phone-tg` עם admin key לחיבור `0584203384` → TG `224223270` | קישור טלפון של משתמש קיים |
| 7 | SQL review של תשלומים תקועים למשתמש `8789977826` (שאילתה ב-`OSIF_CHECKLIST`) — החזר ₪147 או שדרג ל-VIP ב-+₪353 | payment bug 21.4 (fix כבר נדחף, זה cleanup) |
| 8 | **Flash firmware v3** — `cd D:\SLH_ECOSYSTEM\ops\firmware\slh-device-v3 && pio run -t upload` | ESP32 hardware pairing |

---

## 🟢 עבודת קוד אוטונומית זמינה — סדר מוצע

| # | משימה | סוג | תלות |
|---|-------|-----|------|
| 9  | **`/api/performance` endpoint** ב-Railway — קורא `performance_report.csv` | backend | קוד מוכן בדוח, ~15 דק' |
| 10 | **`performance.html`** העלאה לאתר + כרטיסייה ב-`chain-status.html` | frontend | HTML מוכן בדוח |
| 11 | **`/performance` בטלגרם** ב-`@Grdian_bot` | bot | תלוי ב-#9 |
| 12 | **Events tab ב-`admin.html`** (במקום new tab) | frontend UX | קיים `chain-status.html` |
| 13 | **`/api/events/public`** — feed ציבורי ללא payload | backend | ring buffer קיים |
| 14 | **`blockchain.html` real data** — BSCScan + TONScan fetch | frontend | API keys נדרשים |
| 15 | **Mobile responsive audit** — dashboard/wallet/community/chain-status | CSS | 4 עמודים |
| 16 | **Phase 0B bot migration** — 22 בוטים → `shared_db_core` | backend refactor | **גדול, לא לפני אישור** |
| 17 | **Task Scheduler** ל-`daily_backtest.py` כל 6 שעות | ops | Windows Scheduler |
| 18 | **Telegram push alerts** לאותות trading חדשים | bot | תלוי ב-#9 |

---

## 🔵 החלטה אסטרטגית שלך — לא לבצע עד אישור

| # | נושא | למה ממתין |
|---|------|-----------|
| 19 | **Phase 2 Identity Proxy** | ארכיטקטורה גדולה, בחירת גישה |
| 20 | **Phase 3 Ledger unification** | איחוד בין מספר ledgers |
| 21 | **Webhook migration** | שינוי topology |
| 22 | **BSC DEX integration** (PancakeSwap, Web3) | paper trading קודם, הון קטן אחר כך |
| 23 | **Mobile app MVP** (React Native / Flutter) | 2-3 שבועות פיתוח |
| 24 | **Improve trading strategy** (RSI, whale activity, volume anomaly) | אחרי calc_pnl.py עם נתוני 24h |
| 25 | **Run GUARDIAN_AUDIT_AGENT_PROMPT** ב-session נפרד | `D:\SLH_ECOSYSTEM\ops\GUARDIAN_AUDIT_AGENT_PROMPT_20260421.md` — audit/refactor proposal |
| 26 | **Legal entity** (מ-Roadmap 13+) | הבלוקר הגדול ביותר למסחר אמיתי |

---

## 🕐 תלוי זמן — לא דחוף עד מחר

- **הרץ `python calc_pnl.py`** על `backtest_YYYYMMDD.csv` אחרי 24h מאיסוף — יקבע Win Rate אמיתי
- **הרץ `python professional_analysis.py`** — Sharpe / Sortino / Max DD / Calmar / CAGR
- **אם Sharpe > 1 + Win Rate > 45% + Max DD < 20%** → עבור ל-#9/#10/#11. אחרת — כיוונן פרמטרים.

---

## סטטיסטיקה

- **סה"כ משימות פתוחות:** 26
- **שלך (blockers):** 4 (15 דק')
- **שלך (ידני):** 4 (30 דק')
- **קוד אוטונומי זמין:** 10
- **החלטה אסטרטגית:** 8

**מה שכבר נעשה היום:** 16+ commits, Phase 0B 16/16, payment bug fixed, reality dashboard, referral cap, device chain, event stream, Guardian token rotated locally. (ראה `SESSION_FULL_CLOSURE_20260421.md` + `SESSION_HANDOFF_20260421_LATE.md`).
