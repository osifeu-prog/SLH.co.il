# 📟 ESP · Device Registry · Quick Start
> **לסוכן שעובד על הלדג'ר + Guardian + ESP מהמחשב השני.** ענה כאן במקום פקודות גנריות.

---

## 🎯 מה אתה צריך לדעת בשורה אחת

**⚠️ UPDATED 2026-04-20:** ה-micro-service המקומי על port 8090 **הוסר** (היה צעצוע in-memory שהטעה). ה-endpoints היחידים שפעילים הם ב-Railway API:

- `POST /api/device/register` — שלב 1 (phone + device_id → 6-digit code)
- `POST /api/device/verify` — שלב 2 (code → signing_token)
- `GET  /api/device/claim/{device_id}` — device-side polling לאחר web pair
- `POST /api/esp/heartbeat` — heartbeat עם Bearer token
- `GET/POST /api/esp/commands/{device_id}` — remote command queue
- `POST /api/admin/link-phone-tg` — קישור טלפון ל-TG id (admin)

ה-UI לקישור נמצא ב-`https://slh-nft.com/device-pair.html` — משתמש בכל ה-endpoints מעל.
ה-Dashboard ב-`https://slh-nft.com/chain-status.html`.
ה-firmware ב-`ops/firmware/slh-device-v3/` עם `FLASH_INSTRUCTIONS.md`.

---

## 📂 הקבצים (עכשיו ב‑git)

```
D:\SLH_ECOSYSTEM\device-registry\
├── main.py          — FastAPI על port 8090 (register/verify)
├── Dockerfile       — python:3.11-slim
└── requirements.txt — fastapi + uvicorn
```

```
D:\SLH_ECOSYSTEM\shared\
├── bot_template.py   — 241 שורות, משותף לכל הבוטים
├── bot_filters.py    — cross-bot collision filter
├── register_api.py   — client module ל-/api/device/*
├── community_api.py
└── slh_payments/     — referrals, promotions, ledger
```

```
D:\SLH_ECOSYSTEM\ops\
├── LEDGER_GUARDIAN_ESP_AGENT_PROMPT.md   — הפרומפט המלא שלך
├── MASTER_EXECUTOR_AGENT_PROMPT.md       — הפרומפט הכולל
├── SESSION_STATUS.md                     — מצב חי
├── LIVE_ROADMAP.md                       — כל ה-tracks
├── DECISIONS.md
└── AIC_TOKEN_DESIGN.md
```

---

## 🚀 PowerShell · הפקודות שאתה צריך (מדויק)

### שלב 1: שכפל הכל
```powershell
# שני הrepos — API + Website
git clone https://github.com/osifeu-prog/slh-api.git D:\SLH_ECOSYSTEM
cd D:\SLH_ECOSYSTEM
git clone https://github.com/osifeu-prog/osifeu-prog.github.io.git website
```

### שלב 2: .env
```powershell
# אוסיף ישלח לך ידנית. אל תעתיק מה-server.
# הקובץ חייב לשבת ב:
# D:\SLH_ECOSYSTEM\.env
```

### שלב 3: הרצת ה-API המרכזי מקומית
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -c "import ast; ast.parse(open('main.py', encoding='utf-8-sig').read()); print('OK')"
uvicorn main:app --reload --port 8000
# ואז: curl http://localhost:8000/api/health
```

### שלב 4: הרצת device-registry (ESP service)
```powershell
# אופציה A - Docker (מומלץ)
cd D:\SLH_ECOSYSTEM
docker compose up -d device-registry
docker compose logs -f device-registry

# אופציה B - Python ישיר
cd D:\SLH_ECOSYSTEM\device-registry
pip install -r requirements.txt
uvicorn main:app --reload --port 8090
# ואז: curl http://localhost:8090/docs
```

### שלב 5: בדיקה end-to-end
```powershell
# Register a test device
curl -X POST http://localhost:8090/register -H "Content-Type: application/json" `
  -d '{"serial":"ESP_TEST_001","phone":"+972501234567"}'
# מחזיר: {"status":"code_sent","code":"423918"}

# Verify with that code
curl -X POST http://localhost:8090/verify -H "Content-Type: application/json" `
  -d '{"serial":"ESP_TEST_001","code":"423918"}'
# מחזיר: {"status":"verified","token":"TOKEN_ESP_TEST_001_1729176000"}
```

### שלב 6: הרצת הבוטים (Ledger + Guardian)
```powershell
cd D:\SLH_ECOSYSTEM
docker compose up -d ledger-bot guardian-bot
docker compose logs -f ledger-bot
# אתה צריך לראות: "Start polling"
```

---

## 🎯 3 משימות מוכנות להרמה

### משימה 1 · Ledger bot · `/mybalance` command
**File:** `shared/bot_template.py` (already has `/status` — add `/mybalance`)

**מה לעשות:**
1. הוסף handler חדש:
   ```python
   @dp.message(Command("mybalance"))
   async def balance_cmd(m: types.Message):
       uid = m.from_user.id
       async with aiohttp.ClientSession() as s:
           async with s.get(f"https://slh-api-production.up.railway.app/api/user/{uid}") as r:
               d = await r.json()
       u = d.get("user", {})
       b = d.get("balances", {})
       text = (
           f"💰 היתרה שלך:\n"
           f"SLH: {b.get('SLH', 0):.4f}\n"
           f"ZVK: {b.get('ZVK', 0):.2f}\n"
           f"Premium: {'✅' if d.get('premium') else '❌'}"
       )
       await m.answer(text)
   ```
2. בדיקה: שלח `/mybalance` לבוט
3. Commit: `feat(ledger-bot): /mybalance command`

### משימה 2 · Guardian bot · ZUZ alert to workers group
**File:** `guardian/` (קיים) + env var `GUARDIAN_WORKERS_CHAT_ID`

**מה לעשות:**
1. הוסף cron שרץ כל דקה וקורא ל-`/api/guardian/stats`
2. אם `zuz_spike_today > 5` → שלח הודעה לקבוצת העובדים (לא הכרויות!)
3. שמור `last_zuz_count` ב-Redis כדי לא לספם

### משימה 3 · ESP device-registry · Twilio SMS
**File:** `device-registry/main.py`

**מה לעשות:**
1. הוסף env var `TWILIO_*` (אוסיף יספק)
2. במקום `print(code)` שלח SMS אמיתי:
   ```python
   from twilio.rest import Client
   client = Client(os.getenv("TWILIO_ACCOUNT_SID"), os.getenv("TWILIO_AUTH_TOKEN"))
   client.messages.create(
       body=f"SLH code: {code}",
       from_=os.getenv("TWILIO_FROM_NUMBER"),
       to=req.phone,
   )
   ```
3. Commit: `feat(device-registry): real SMS via Twilio`

---

## ❌ מה NOT לעשות

- ❌ אל תיגע ב-Railway env vars (Osif עושה את זה)
- ❌ אל תקמפט ל-master בלי PR (צור branch: `feature/<task-name>`)
- ❌ אל תמחק users/deposits/community_posts — production data
- ❌ אל תחשוף את קבוצת ההכרויות (t.me/+nKgRnWEkHSIxYWM0) בפרומפטים
- ❌ אל תצ'ק-אין עם הקטין (ID 6466974138) ל-adult flows

---

## 📞 דיווח חזרה

כשאתה מסיים משימה:
1. עדכן `ops/SESSION_STATUS.md`: `✅ Task X done by <you>`
2. Commit + push לbranch שלך
3. צור PR לmaster
4. שלח הודעה לאוסיף בטלגרם:
   ```
   📋 Agent <your-name> done:
   - Task: <name>
   - Commit: <hash>
   - Verified: <how>
   - Blockers: <any>
   ```

---

## 🆘 תקוע?

1. פתח [slh-nft.com/mission-control.html](https://slh-nft.com/mission-control.html) — מצב חי של המערכת
2. קרא [MASTER_EXECUTOR_AGENT_PROMPT.md](https://github.com/osifeu-prog/slh-api/blob/master/ops/MASTER_EXECUTOR_AGENT_PROMPT.md) — הפרומפט הכולל
3. פנה לאוסיף בטלגרם: `@osifeu_prog`

---

**Ready. Pick Task 1, 2, or 3 and announce: "Starting Task N".**
