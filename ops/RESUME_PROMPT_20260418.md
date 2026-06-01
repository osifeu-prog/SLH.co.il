# 🚀 SLH · Resume Prompt · 2026-04-18

**Copy-paste this into a new Claude Code session to continue exactly where we left off.**

---

אתה Claude Code בפרויקט SLH Spark של Osif Kaufman Ungar (@osifeu_prog, Telegram ID: 224223270). מפתח סולו דובר עברית בונה אקוסיסטם קריפטו בישראל.

**תאריך:** 2026-04-18. שעה: המשך הסשן הקודם שסגרנו עם handoff מלא ב-`ops/SESSION_HANDOFF_20260418_FINAL.md`.

---

## 📜 קרא ראשון לפני כל פעולה

1. `ops/SESSION_HANDOFF_20260418_FINAL.md` — כל מה שהושג בסשן האחרון + מה פתוח.
2. `CLAUDE.md` — חוקי עבודה (Railway sync, Hebrew UI, never mock, etc.)
3. `agent-tracker.html` בלייב — סטטוסים של 6 הסוכנים.

---

## ✅ מה בוצע ומשודר:

### Frontend (GitHub Pages)
- `/tour.html` · 8-station onboarding
- `/agent-tracker.html` · 6-agent dashboard
- `/blog/` · 5 פוסטים: neurology, crypto-yoga, verified-experts, ecosystem-map, anti-facebook
- `/css/slh-design-system.css` · tokens + 5 themes + nav + skeleton classes
- `/js/slh-nav.js` · unified nav (role/theme/lang/RTL/mobile)
- `/js/slh-skeleton.js` · loading states
- `/pay.html` · QR תוקן (EIP-681 ל-BNB, deeplink ל-TON)

### Backend (Railway)
- `routes/payments_auto.py` · tolerance 0.00002 BNB (תיקון עמלת Binance)
- `routes/payments_monitor.py` · סקלט ל-auto-monitor (לא מחובר ל-main.py)
- `scripts/e2e-smoke-test.ps1` · smoke test של 13 endpoints

---

## 🛑 מה פתוח — בקשות מהמשתמש:

### חסמים שדורשים input
1. **CYD מסך שחור** — Osif צריך להריץ את בלוק PowerShell של סוכן ESP ב-`C:\Users\USER\Desktop\SLH\ESP32-2432S028\` (לא D:), לדווח האם colorTest (אדום→ירוק→כחול) עובד.
2. **N8N** — צריך `N8N_PASSWORD=<choice>` + "מאשר docker compose".
3. **@G4meb0t_bot_bot** — צריך BotFather token.
4. **Payment retry** — אחרי שRailway מסיים deploy, Osif צריך לנסות אמת שוב עם TX `0x2a9d5da99172b7e6c758ea07457d419be891df68b539b9966f092ec0f17a262a`.

### משימות הבאות (לפי עדיפות)
1. **חבר payments_monitor ל-main.py** — 4 שורות: import + include_router + set_pool בstartup + `start_monitor()`.
2. **הוסף register intent** ב-pay.html step 3 (לפני הצגת QR) — מאפשר auto-flow מלא.
3. **Content W.2** — 30 פוסטים לרשתות חברתיות.
4. **UI/UX U.3** (typography audit) + **U.4** (responsive audit).
5. **E2E test ב-production** — הרץ `scripts/e2e-smoke-test.ps1`.
6. **ESP E.2** — device registration endpoint (כשהמסך עובד).
7. **Deploy @G4meb0t_bot_bot** (כשיש token).
8. **n8n install** (כשהסיסמה מגיעה).

---

## 🔑 גבולות קריטיים

- **לעולם לא** להחליף tokens/secrets בhardcode בתוך HTML
- **לעולם לא** לחשוף את קבוצת ההכרויות `+nKgRnWEkHSIxYWM0` לציבור או לקטינים (אחיין בן 13 = ID 6466974138)
- **לעולם לא** לשנות את docker-compose.yml בלי אישור מפורש של Osif
- **תמיד** לסנכרן `api/main.py` ו-`main.py` (Railway מבנה מ-root)
- **תמיד** עברית ב-UI, אנגלית בקוד/commits
- **תמיד** real data, אף פעם mock ב-production (שים `[DEMO]` tag אם צריך placeholder)

---

## 🧭 סגנון עבודה

- Osif אוהב פעולה ישירה — "כן לכל ההצעות" = המשך עם הכל
- עברית בכל התשובות למשתמש
- תשובות קצרות, ממוקדות, ב-action items
- כלי multi-agent: 6 סוכנים פעילים במקביל — השתמש ב-`agent-tracker.html` לסנכרון

---

## 📈 סטטוס בקצרה

| Track | % | פועם |
|-------|---|------|
| 1 Auth | 85% | verified tester IDs |
| 2 Community | 75% | RSS live |
| 3 Tokens | 80% | 6 tokens defined |
| 4 Payments | 78% | QR + tolerance fixed |
| 5 Engagement | 72% | sudoku + dating live |
| 6 Experts/ESP | 55% | ESP still in E.1 |
| **Avg** | **74%** | up from 67% |

---

## 💳 TX פתוח של Osif
- Hash: `0x2a9d5da99172b7e6c758ea07457d419be891df68b539b9966f092ec0f17a262a`
- From: `0xeb2d2f1b8c558a40207669291fda468e50c8a0bb` (Binance hot)
- To: Genesis `0xd061de73b06d5e91bfa46b35efb7b08b16903da4` ✅
- Amount: 0.000490 BNB (Binance ניכה 0.00001 מ-0.0005 שנשלח)
- Status: TX valid on-chain, pending retry after Railway deploys tolerance fix

---

**פקודת פתיחה למשתמש:** "קיבלתי את ה-handoff. איפה רוצה להתחיל — להמשיך CYD, לחבר monitor, או משהו אחר?"
