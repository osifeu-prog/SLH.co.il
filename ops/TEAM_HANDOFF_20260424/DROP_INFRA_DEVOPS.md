# DROP OFF · Infrastructure / DevOps · 2026-04-24

**קהל יעד:** Idan / IT (או כל מפתח עם גישה ל-Docker + Railway + ESP32 hardware)
**זמן ביצוע כולל:** 3–4 שעות
**דרישות מקדימות:**
- גישת SSH / RDP לתחנת Osif ב-D:\ (או עותק מקומי של D:\SLH_ECOSYSTEM)
- Railway dashboard access (שלח אליו Team invite אם חסר)
- USB + ESP32 device לחיבור ל-COM5
- PlatformIO installed (`pip install platformio`)

---

## 🎯 מטרה כללית

אחרי ש-Osif שחרר את Railway (DROP_OSIF #1), צריך:
1. Rebuild של 9 docker bots עם Phase 0B code
2. תיקון ledger-bot שנופל ב-restart loop
3. Flash של ESP32 firmware v3 למכשיר פיזי
4. הגדרת Task Scheduler ל-daily_backtest
5. וידוא BSCSCAN_API_KEY ב-Railway

---

## 🔴 1. Phase 0B Docker Rebuild — 9 bots (30 דק')

**הקשר:** 9 בוטים עברו migration ל-`shared_db_core` (fail-fast pool). הקוד committed אבל containers רצים מ-image ישן.

**הבוטים שצריך rebuild:**
- academia-bot, airdrop-bot, admin-bot, expertnet-bot, guardian-bot,
  ledger-bot, nfty-bot, osif-shop, social-bot

**פעולה:**
```powershell
cd D:\SLH_ECOSYSTEM

# אופציה A — dry run תחילה (מומלץ)
powershell -File ops\PHASE_0B_REBUILD_BOTS.ps1 -DryRun

# אופציה B — rebuild כולל
powershell -File ops\PHASE_0B_REBUILD_BOTS.ps1

# אופציה C — idle (manually)
docker compose up -d --build academia-bot airdrop-bot admin-bot expertnet-bot guardian-bot nfty-bot osif-shop social-bot
# ledger-bot נבדל — ראה סעיף 2
```

**וידוא:**
```powershell
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.RestartCount}}" | Select-String -NotMatch "Restarting"
# אסור לראות "Restarting" או RestartCount > 5
```

**אם container קורס:**
```powershell
docker logs <service-name> --tail 50
# חפש ImportError של shared_db_core או DB connection refused
```

---

## 🔴 2. ledger-bot Crash Loop — תיקון TOKEN (5 דק')

**הבעיה (אומתה ב-KNOWN_ISSUES K-8):**
- `docker-compose.yml` מעביר `TOKEN=${BOT_TOKEN}`
- service ב-`ledger-bot` קורא `LEDGER_BOT_TOKEN`
- תוצאה: `TokenValidationError: TOKEN=None`, RestartCount=169

**פתרון 1 (מומלץ — מהיר):** עדכן compose:
```yaml
# D:\SLH_ECOSYSTEM\docker-compose.yml
# חפש את ledger-bot service
ledger-bot:
  environment:
    - TOKEN=${LEDGER_BOT_TOKEN}  # שנה מ-${BOT_TOKEN}
    - LEDGER_BOT_TOKEN=${LEDGER_BOT_TOKEN}  # הוסף למען תאימות
    # ... שאר env vars
```

**פתרון 2 (יותר נכון — תקן בקוד):**
```python
# ledger-bot/main.py
import os
TOKEN = os.getenv("LEDGER_BOT_TOKEN") or os.getenv("BOT_TOKEN") or os.getenv("TOKEN")
```

**אחרי התיקון:**
```powershell
cd D:\SLH_ECOSYSTEM
docker compose up -d --build ledger-bot
docker logs ledger-bot --tail 20 --follow
# צפוי: "Bot started. Polling..." ולא TokenValidationError
```

---

## 🔴 3. ESP32 Firmware v3 Flash (15 דק')

**הקשר:** firmware v3 מוכן לקומפילציה ב-`D:\SLH_ECOSYSTEM\device-registry\esp32-cyd-work\firmware\slh-device-v3\`. כל הקוד מוכן — חסר רק ה-flash הפיזי.

**Prerequisites:**
- ESP32-CYD device מחובר ב-USB (COM5 בד"כ)
- PlatformIO CLI (`pio --version`)

**פעולה:**
```powershell
cd D:\SLH_ECOSYSTEM\device-registry\esp32-cyd-work\firmware\slh-device-v3

# compile
pio run

# flash
pio run -t upload --upload-port COM5

# verify serial
pio device monitor -p COM5 -b 115200
```

**אם COM5 busy:**
```powershell
# kill any stuck pio.exe
powershell -File D:\SLH_ECOSYSTEM\ops\slh-start.ps1 -Stop
# או מ-Task Manager → End pio.exe
```

**בדיקת success:**
ב-serial monitor צפוי לראות:
```
SLH Device v3 starting...
Connected to WiFi: <SSID>
Registered device_id: <hex>
Ready for QR pairing
```

**הערה:** לאחר flash, המכשיר צריך להירשם אוטומטית דרך `POST /api/device/register`. בדוק ב-Railway logs או:
```bash
curl -H "X-Admin-Key: <KEY>" https://slh-api-production.up.railway.app/api/admin/devices/list
```

---

## 🟡 4. Task Scheduler ל-daily_backtest (10 דק')

**הקשר:** `daily_backtest.py` מייצר CSV שמזין את `/api/performance`. כרגע מחזיר `available: false` כי ה-CSV לא קיים ב-Railway container.

**אופציה A — Railway Cron (מומלץ):**
1. Railway dashboard → slh-api project → `+ New` → `Cron Schedule`
2. הגדר:
   - Schedule: `0 */6 * * *` (כל 6 שעות)
   - Command: `python daily_backtest.py && python calc_pnl.py`
3. Deploy

**אופציה B — Windows Task Scheduler (מקומי):**
1. `taskschd.msc` → Create Task
2. Trigger: Daily, every 6 hours
3. Action: Start program
   - Program: `python`
   - Arguments: `D:\SLH_ECOSYSTEM\daily_backtest.py`
   - Start in: `D:\SLH_ECOSYSTEM`
4. Export CSV וב-end של script:
   ```python
   import requests
   requests.post('https://slh-api-production.up.railway.app/api/ops/upload-csv',
                 headers={'X-Admin-Key': ADMIN_KEY},
                 files={'csv': open('performance_report.csv', 'rb')})
   ```

**וידוא:**
```bash
curl https://slh-api-production.up.railway.app/api/performance
# צפוי: available: true, rows: [...]
```

---

## 🟡 5. BSCSCAN_API_KEY ב-Railway (2 דק')

**הקשר:** `/network.html` + `/blockchain.html` מציגים `0 holders, 0 transactions` כי אין API key.

**פעולה:**
1. קבל API key מ-Osif (אחרי rotation ב-DROP_OSIF #4 פריט 4)
2. Railway → slh-api → Variables → `+ New Variable`
3. Name: `BSCSCAN_API_KEY`
4. Value: `<key>`
5. Save — יפעיל restart

**וידוא:**
```bash
curl "https://slh-api-production.up.railway.app/api/blockchain/stats"
# צפוי: holders > 0, tx_count > 0
```

---

## 🟢 6. אוטומציית CI/CD (אופציונלי — 1 שעה)

**קיים:** pre-commit hook מקומי.
**חסר:** commit-msg hook (בעיית timing), pre-push py_compile check.

**הפעלה (מקומית, לכל מי שעובד על הרפו):**
```powershell
cd D:\SLH_ECOSYSTEM
git config core.hooksPath .githooks
# .githooks/pre-commit כבר קיים
```

**הוספת pre-push syntax check (מומלץ):**
```bash
# .githooks/pre-push
#!/bin/bash
python -m py_compile main.py api/main.py || {
  echo "❌ syntax errors in main.py — refusing push"
  exit 1
}
```

---

## 🟢 7. Task Scheduler ל-onboarding pipeline (אופציונלי)

אחרי ש-CRM LIVE (DROP_CRM_BUSINESS), תוסיף cron:
```
0 9 * * * python scripts/ambassador_nudge.py  # שליחת תזכורות למי שלא הגיב
```

---

## 📊 Monitoring בסיסי

**Railway logs (live):**
```
https://railway.app/project/slh-api → Deployments → latest → View Logs
```

**Docker local:**
```powershell
docker stats  # CPU/RAM per container
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.RestartCount}}"
```

**Health matrix (רץ מ-terminal):**
```powershell
powershell -File D:\SLH_ECOSYSTEM\ops\slh-start.ps1 -Verify
# מדפיס טבלה של כל ה-services עם green/red status
```

**אם משהו נופל:**
1. `docker logs <name> --tail 100`
2. `railway logs --service slh-api`
3. דוח ל-Osif דרך Telegram @osifeu_prog

---

## 📋 Checklist סיום

- [ ] 9 bots rebuilt with Phase 0B code, 0 restarting
- [ ] ledger-bot RestartCount = 0, polling OK
- [ ] ESP32 v3 flashed, serial monitor shows "Ready"
- [ ] `/api/performance` returns `available: true`
- [ ] `BSCSCAN_API_KEY` set on Railway
- [ ] (optional) Task Scheduler for daily_backtest configured
- [ ] `slh-start.ps1 -Verify` exits 0

**זמן כולל משוער:** 60-90 דק' (לא כולל אם נתקלים בבאג בוט)

---

**דיווח ל-Osif:**
- ב-Telegram: @osifeu_prog
- או בדוא"ל: osif.erez.ungar@gmail.com
- שלח צילום מסך של `docker ps` + `slh-start.ps1 -Verify` output
