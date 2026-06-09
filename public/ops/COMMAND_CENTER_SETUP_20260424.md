# Command Center Setup — PowerShell Commands Bundle
**תאריך:** 2026-04-24
**עבור:** Osif Kaufman Ungar
**מטרה:** חיבור מלא של כל הרכיבים + הפעלת Guardian/Claude bot + בדיקות שהכל עובד.

> **LABEL LEGEND (לפי זיכרון `feedback_powershell_vs_browser_console`):**
> - 🖥️ **shell** = PowerShell / bash terminal (curl, git, docker, python)
> - 🌐 **console** = F12 Browser Console (localStorage, fetch, window)
> - 🤖 **telegram** = שליחת הודעה לבוט

---

## ▶️ חלק א: דחיפה של ops commit (שכבר נעשה commit מקומית)

### 🖥️ shell — Push selective commit ל-API repo
**תיאור:** ה-commit `c89f4a3` שלך (ops docs בלבד) יושב מקומית. יש עוד `1 commit ahead` (`c3fdb47`) שגם שלך. אפשר לדחוף את שניהם ביחד — הם לא מכילים את ה-uncommitted work של בוטים אחרים.

```powershell
# Verify what's about to push (should show 2 commits, both yours)
cd D:\SLH_ECOSYSTEM
git log --oneline origin/master..HEAD

# Expected output:
#   c89f4a3 docs(ops): Phase 2 Voice + Swarm blueprints + handoff
#   c3fdb47 feat(outreach): investor + community landing pages + bulk outreach generator

# Push both commits
git push origin master
```

**⚠️ אם תרצה לדחוף רק את ה-ops commit (בלי c3fdb47):**
```powershell
# Push only c89f4a3 (ops docs only)
cd D:\SLH_ECOSYSTEM
git push origin c89f4a3:master
```

**אם תתקל ב-rejection (origin עדכון לפניך):**
```powershell
git pull --rebase origin master
# resolve conflicts if any, then:
git push origin master
```

---

## ▶️ חלק ב: אימות שהאתר LIVE ועובד

### 🖥️ shell — Quick health check
```powershell
# Check all 5 key production URLs
$urls = @(
  "https://slh-nft.com/voice.html",
  "https://slh-nft.com/swarm.html",
  "https://slh-nft.com/network.html",
  "https://slh-nft.com/roadmap.html",
  "https://slh-nft.com/command-center.html"
)
foreach ($url in $urls) {
  $r = Invoke-WebRequest -Uri "$url?t=$(Get-Random)" -UseBasicParsing -Method Head
  Write-Host "$($r.StatusCode) → $url"
}

# Check API health
curl.exe -sS "https://slh-api-production.up.railway.app/api/health" | ConvertFrom-Json | Format-List

# Check shared.js has new Phase 2 section
$js = Invoke-WebRequest "https://slh-nft.com/js/shared.js?v=20260424a&nocache=$(Get-Random)"
if ($js.Content -match "Phase 2 Vision") {
  Write-Host "✅ shared.js updated" -ForegroundColor Green
} else {
  Write-Host "❌ shared.js OLD — check cache" -ForegroundColor Red
}
```

**Expected output:**
- 5 × `200 → https://slh-nft.com/...`
- API `v1.1.0` or latest
- `✅ shared.js updated`

---

## ▶️ חלק ג: הפעלת Bot Fleet (25 bots)

### 🖥️ shell — Start core services (postgres + redis first)
```powershell
cd D:\SLH_ECOSYSTEM
docker compose up -d postgres redis
# Wait 10 seconds for health checks
Start-Sleep -Seconds 10
docker compose ps postgres redis
```

### 🖥️ shell — Start Guardian (anti-fraud bot)
```powershell
cd D:\SLH_ECOSYSTEM
docker compose up -d guardian-bot
docker logs -f slh-guardian-bot --tail 20
# Ctrl+C to exit logs
```

### 🖥️ shell — Start Claude executor bot (@SLH_Claude_bot)
**חשוב:** זה ה-bot שתשלוט עליו מטלגרם. צריך ANTHROPIC_API_KEY ב-`slh-claude-bot/.env` (כבר מוגדר).

```powershell
cd D:\SLH_ECOSYSTEM
# Verify .env has ANTHROPIC_API_KEY (without printing value)
if ((Get-Content slh-claude-bot\.env) -match "^ANTHROPIC_API_KEY=sk-") {
  Write-Host "✅ ANTHROPIC_API_KEY set" -ForegroundColor Green
} else {
  Write-Host "❌ ANTHROPIC_API_KEY missing — add to slh-claude-bot/.env" -ForegroundColor Red
  break
}

# Start the Claude bot
docker compose up -d claude-bot
docker logs -f slh-claude-bot --tail 30
```

### 🖥️ shell — Start all 25 bots at once
**אופציה A (הזהיר): הפעל בקבוצות**
```powershell
cd D:\SLH_ECOSYSTEM
# Core infra first
docker compose up -d postgres redis
Start-Sleep -Seconds 10

# Executor + Guardian first (security)
docker compose up -d claude-bot guardian-bot
Start-Sleep -Seconds 5

# Rest of fleet
docker compose up -d
Start-Sleep -Seconds 20

# Check all running
docker compose ps --format "table {{.Service}}\t{{.State}}\t{{.Status}}"
```

**אופציה B (הכל בבת אחת — אם אתה אומץ):**
```powershell
cd D:\SLH_ECOSYSTEM
docker compose up -d
Start-Sleep -Seconds 30
docker compose ps
```

---

## ▶️ חלק ד: אימות שה-bots רצים

### 🖥️ shell — Full fleet status
```powershell
# Count running vs total
$running = (docker ps --format "{{.Names}}" | Select-String "^slh-" | Measure-Object).Count
$total = (docker ps -a --format "{{.Names}}" | Select-String "^slh-" | Measure-Object).Count
Write-Host "$running / $total bots running"

# See who's down
docker compose ps --services --filter "status=exited"
docker compose ps --services --filter "status=running"
```

### 🖥️ shell — Test specific bot healthchecks
```powershell
# Guardian bot logs
docker logs slh-guardian-bot --tail 15

# Claude bot logs
docker logs slh-claude-bot --tail 15

# Test API bot-to-bot comms
curl.exe -sS https://slh-api-production.up.railway.app/api/admin/ecosystem-scan
```

---

## ▶️ חלק ה: התחלת שליטה מטלגרם

### 🤖 telegram — Test Claude executor bot
1. פתח טלגרם
2. חפש `@SLH_Claude_bot`
3. לחץ `/start`
4. שלח הודעת test: `בדוק אילו בוטים רצים עכשיו`
5. הבוט אמור להריץ `docker ps` ולהחזיר רשימה.

**אם הבוט לא עונה:**
```powershell
# Check if container is alive
docker ps | Select-String claude-bot

# See logs
docker logs slh-claude-bot --tail 50

# Restart if needed
docker compose restart claude-bot
```

### 🤖 telegram — Test Guardian bot commands
```
/start     → welcome message
/scan      → scan current group
/score     → show ZUZ score
/help      → command list
```

---

## ▶️ חלק ו: Command Center — פתיחת multi-monitor

### 🌐 console (F12 Browser Console in command-center.html)
לאחר שה-site deployed:
1. פתח `https://slh-nft.com/command-center.html` בדפדפן
2. לחץ על preset — למשל "Overview" → 5 חלונות נפרדים נפתחים
3. גרור כל חלון לצג המתאים

**אם popups חסומים:**
- Chrome: לחץ על האייקון ליד ה-URL bar → Allow popups
- Firefox: Tools → Preferences → Privacy → Exceptions
- Edge: Settings → Cookies and site permissions → Pop-ups and redirects → Allow slh-nft.com

### 🌐 console — Save monitor layout (advanced)
```javascript
// In command-center console — save current window positions
const layout = [];
// For each window you opened:
// 1. Focus the window
// 2. In its console: { x: screenX, y: screenY, w: outerWidth, h: outerHeight }
// 3. Copy back to command-center and save:
localStorage.setItem('slh_monitor_layout', JSON.stringify(layout));
```

---

## ▶️ חלק ז: סיבוב טוקנים — 31 dirty tokens

### 🤖 telegram — רוטציה דרך BotFather
**עבור כל בוט:**
1. פתח `@BotFather`
2. שלח `/mybots`
3. בחר את הבוט
4. API Token → Revoke current token → אשר
5. קבל token חדש
6. שמור ב-`.env` (אל תפרסם בצ'אט!)
7. הפעל מחדש: `docker compose restart <bot-name>`

### 🖥️ shell — Update .env safely (אחרי קבלת token חדש)
```powershell
# DO NOT echo the token value. Edit .env in VSCode/Notepad++
notepad D:\SLH_ECOSYSTEM\.env
# Find the line: OLD_BOT_TOKEN=xxx:yyy
# Replace value with new token
# Save + close

# Restart the specific bot
cd D:\SLH_ECOSYSTEM
docker compose restart <bot-service-name>
```

**רשימת 25 services ב-docker-compose.yml:**
```
core-bot, guardian-bot, botshop, wallet, factory, fun, admin,
airdrop, campaign, game, ton-mnh, ton, ledger, osif-shop, nifti,
chance, nfty, academia-bot, claude-bot
```

---

## ▶️ חלק ח: Emergency Rollback (אם משהו נשבר)

### 🖥️ shell — Website rollback
```powershell
cd D:\SLH_ECOSYSTEM\website
# Check what was last pushed
git log --oneline -5

# Revert the Phase 2 Vision commit (ccd8281) safely
git revert ccd8281
git push origin main
```

### 🖥️ shell — Kill all bots immediately
```powershell
cd D:\SLH_ECOSYSTEM
docker compose down
# To also remove volumes (destructive!):
# docker compose down -v
```

### 🖥️ shell — Resume from scratch
```powershell
cd D:\SLH_ECOSYSTEM
docker compose down
docker compose up -d postgres redis
Start-Sleep -Seconds 10
docker compose up -d
```

---

## ✅ Final Verification Checklist

העבר את כל הסעיפים האלה אחרי הכל:

### Website (production)
- [ ] 🖥️ `curl -I https://slh-nft.com/voice.html` → 200
- [ ] 🖥️ `curl -I https://slh-nft.com/swarm.html` → 200
- [ ] 🖥️ `curl -I https://slh-nft.com/command-center.html` → 200
- [ ] 🌐 Open `/command-center.html` → 6 sections, 24 tiles visible
- [ ] 🌐 Click "Overview" preset → 5 popup windows open
- [ ] 🌐 Open `/network.html` → 61 nodes displayed, 2 new filter buttons (Voice/Swarm)

### API
- [ ] 🖥️ `curl https://slh-api-production.up.railway.app/api/health` → v1.1.0+
- [ ] 🖥️ `curl https://slh-api-production.up.railway.app/api/stats` → real numbers

### Bots
- [ ] 🖥️ `docker compose ps` → 20+ running
- [ ] 🖥️ `docker logs slh-claude-bot --tail 5` → "Bot started" or similar
- [ ] 🖥️ `docker logs slh-guardian-bot --tail 5` → no errors
- [ ] 🤖 Telegram: `@SLH_Claude_bot /start` → responds
- [ ] 🤖 Telegram: send test command → gets executed

### Ops docs
- [ ] 🖥️ `git log --oneline ops/ | head -5` shows new commits
- [ ] 🖥️ `ls ops/*20260424*` shows: SYSTEM_ALIGNMENT, COMMAND_CENTER_SETUP, SESSION_HANDOFF_VOICE_SWARM, SWARM_V1_BLUEPRINT, VOICE_STACK_COMPETITIVE

---

## 🚨 אם משהו לא עובד

שלח ל-Osif (@osifeu_prog) או פתח issue:
- מה ניסית (פקודה מדויקת)
- מה קרה (error message מדויק)
- מה צפית (expected behavior)

**לא לפתור תקלות ע"י:**
- `--no-verify` ב-git commit
- `docker compose down -v` (מוחק volumes + data!)
- `git push --force` ל-main/master
- Hardcoding של secrets ב-HTML

**להמשך פיתוח:** קרא את `ops/SYSTEM_ALIGNMENT_20260424.md` ועדכן את הסטטוס שלך לפני כל משימה.

---

**End of setup guide.**
