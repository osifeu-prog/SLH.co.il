# Alignment Prompt — For Guardian ESP Preorder Agent
**Copy-paste this to the other agent that was building `/guardian.html` preorder flow.**
**Created:** 2026-04-24 by Claude Opus 4.7 (1M context)
**Authority:** Osif Kaufman Ungar (@osifeu_prog) — confirmed.

---

## 📋 Copy-paste block starts here ↓

```
🛑 STOP — קריאה חובה לפני שתמשיך.

אני עובד על אותו פרויקט SLH Spark, סשן מקביל, ויש חפיפה בעבודה שלנו. אוסיף ביקש יישור קו לפני שנמשיך.

## מה כבר נשלח לפרודקשן הלילה (24.4.2026, commit ccd8281 on osifeu-prog/osifeu-prog.github.io)

1. **`/swarm.html`** — כבר קיים ומכיל:
   - Phase 2 Vision page עם disclaimer ברור "לא זמין מסחרית"
   - Waitlist form שהיא גם עבור Kosher Wallet (ESP32 device pre-sale ₪888)
   - 3-layer architecture (ESP32 → Phone Relay → Anchor)
   - Links ל-/kosher-wallet.html הקיים
   - Integration מלאה עם /network.html + /roadmap.html

2. **`/voice.html`** — דף vision ל-SLH Voice (IVR).

3. **`/command-center.html`** — מרכז שליטה חדש עם:
   - Multi-monitor popup launcher
   - Section "Phase 2 Vision" שכבר כולל Swarm + Kosher Wallet
   - Section "Bot Fleet Control" עם links ל-broadcast-composer, admin-tokens, bot-registry

4. **`ops/SWARM_V1_BLUEPRINT_20260424.md`** — Blueprint טכני מלא עם:
   - ESP32 C++ code stubs (ESP-NOW, ECDSA signing)
   - FastAPI Python code stubs (`routes/swarm.py` עם 7 endpoints)
   - DB schema (swarm_devices, swarm_events, swarm_commands tables)
   - 4-phase roadmap (POC → Kosher Wallet → Production HW → DePIN)

5. **`ops/VOICE_STACK_COMPETITIVE_20260424.md`** — ניתוח תחרותי מלא vs ימות המשיח.

6. **`ops/SYSTEM_ALIGNMENT_20260424.md`** — מסמך יישור קו בין כל הסוכנים (זה המסמך הזה!).

---

## ⚠️ חפיפה ישירה עם מה שאתה בונה

| מה שאתה הודעת שתבנה | מה שכבר קיים | המלצה |
|---|---|---|
| `CREATE TABLE orders` ב-Railway | (לא קיים) — אבל Blueprint יש ב-SWARM_V1 | חכה ל-POC של hardware. **אסור לפתוח pre-orders על vaporware.** |
| `POST /api/preorder` | (לא קיים) | המתן לאחרי POC. |
| `/guardian.html` landing page | `/swarm.html` + `/kosher-wallet.html` קיימים | **אל תיצור `/guardian.html` חדש — זה duplicate!** |
| `/preorder` wizard ב-`@SLH_macro_bot` | `@SLH_macro_bot` הוא פרויקט נפרד (D:\SLH.co.il) | הוסף ל-`@SLH_AIR_bot` הראשי, לא ל-macro. |
| "99 units available" | 0 יחידות מיוצרות עד כה | **לא לפרסם מספרי מלאי לא אמיתיים.** זה נוגד feedback_work_rules ו-Reality Reset 21.4. |
| Mission Control "Orders" tab | `/mission-control.html` קיים | הוסף tab רק אחרי שיש orders אמיתיים. |

---

## ✅ מה מותר לך לעשות עכשיו (approved path)

### Option A: לעצור לחלוטין
ליצור pre-orders על חומרה שלא קיימת זה:
- Legal risk (vaporware claims)
- Brand damage (אנשים ישלמו ₪888 ויחכו לנצח)
- Technical debt (refund flow שלא בנית)

**המלצה:** עצור לגמרי. תסגור את הסשן.

### Option B: להצטרף ל-waitlist flow הקיים
במקום להתחיל מאפס:
1. פתח `website/swarm.html` ותראה את ה-waitlist form שכבר עובד
2. אם יש לך שיפורים — ערוך את הדף הקיים (לא יוצר חדש)
3. השיפורים יכולים לכלול:
   - Telegram integration ל-`@SLH_AIR_bot` (לא macro) כש-user נרשם
   - Email confirmation (לא תשלום)
   - Admin view של leads ב-`/admin.html`
4. הוסף שורה ב-`ops/SYSTEM_ALIGNMENT_20260424.md` תחת "Active Agents" עם הטענה שלך

### Option C: לבנות את ה-POC האמיתי (אחרי Osif מאשר)
אם אוסיף מאשר Phase 1 POC:
1. קרא את `ops/SWARM_V1_BLUEPRINT_20260424.md` במלואו
2. התחל עם:
   - `api/routes/swarm.py` (7 endpoints)
   - 3 DB tables
   - Firmware basic על ESP32 אחד
3. **לא לקיים תשלום עד שה-POC עובד end-to-end**
4. **לא לפרסם באתר כ-"LIVE"** עד שיש hardware

---

## 🗺️ מה אוסיף רוצה (בסדר חשיבות)

1. **תשתית עובדת** ולא vaporware — Reality Reset 21.4 מנהל את העבודה
2. **Unified control center** — המקום היחיד לניהול (לא 5 admin pages שונים)
3. **Agent coordination** — כל סוכן מעדכן `SYSTEM_ALIGNMENT` לפני ואחרי עבודה
4. **Kosher Wallet כמוצר מוביל ל-Swarm** — אבל רק אחרי POC, לא pre-orders בלבד

---

## 📝 מה אתה צריך לעשות עכשיו

1. **קרא:** `ops/SYSTEM_ALIGNMENT_20260424.md` (המסמך המלא)
2. **קרא:** `ops/SWARM_V1_BLUEPRINT_20260424.md`
3. **קרא:** `ops/VOICE_STACK_COMPETITIVE_20260424.md`
4. **החלט:** Option A / B / C
5. **עדכן:** הוסף סעיף ב-`SYSTEM_ALIGNMENT` תחת "Active Agents" — שמך, מה אתה עושה, ETA, blockers
6. **הודע:** לאוסיף על ההחלטה שלך

---

## 🤝 How to coordinate with me (Claude Opus 4.7)

- **שם סוכן:** Claude Opus 4.7 (1M context) — Main Session
- **סטטוס:** Session closed
- **Last commits:** `ccd8281` (website), `c89f4a3` (ops local)
- **Next trigger:** Osif's decision on Phase 1 POC

אין צורך לתאם איתי ישירות — רק לעדכן את `SYSTEM_ALIGNMENT` כדי שכל סוכן יראה. אני יקרא בסשן הבא שלי.

---

## 🔒 Secrets policy

**אל תעתיק טוקנים/סיסמאות/API keys בצ'אט או ב-commits.** ה-rule הוא `feedback_never_paste_secrets`:
- אם אתה רואה ב-chat/code — תעצור ותודיע ל-Osif
- אם אתה צריך ערך מ-`.env` — בקש מה-operator, לא תדפיס
- אם כבר נחשף — רשום ב-alignment doc + בקש rotation

Thanks. Waiting for your alignment response in `ops/SYSTEM_ALIGNMENT_20260424.md`.
```

## 📋 Copy-paste block ends here ↑

---

## Instructions for Osif (you)

### How to use this prompt

**If you want to STOP the other agent:**
1. Copy the block above
2. Paste to the other agent (Telegram / chat / wherever it's running)
3. It will read the alignment doc and either:
   - Stop
   - Coordinate (update SYSTEM_ALIGNMENT)
   - Ask clarifying questions

**If you want the other agent to JOIN the flow:**
1. Same — copy and paste
2. Specifically tell it "בחר Option B" (integrate with existing waitlist)
3. Ask it to update `SYSTEM_ALIGNMENT_20260424.md` with its claim

**If the other agent REFUSES to align:**
- Stop using it
- That's red flag for future work — it's not respecting the coordination protocol

---

## What I did to prepare this

1. Analyzed the other agent's declared plan (from your message)
2. Mapped every planned component vs what already exists
3. Flagged overlap + vaporware risk
4. Provided 3 options (A/B/C) with clear recommendations
5. Embedded references to the docs they need to read

**Source docs:**
- `ops/SYSTEM_ALIGNMENT_20260424.md`
- `ops/SWARM_V1_BLUEPRINT_20260424.md`
- `ops/VOICE_STACK_COMPETITIVE_20260424.md`
- `website/swarm.html` (live)
- `website/kosher-wallet.html` (live)

---

**End of alignment prompt.**
