# SLH Spark · Operator Quick Commands
**Purpose:** PowerShell one-liners you can copy-paste directly. Same commands work for human + agent operators.
**Platform:** Windows PowerShell 5+ (with `curl.exe` aliased to real curl). Git Bash works too for bash sections.

---

## 🟢 1. Health / state

```powershell
# Full state snapshot (color output):
cd D:\SLH_ECOSYSTEM; .\slh-start.ps1 -StatusOnly

# Manual health (copy-paste individually):
curl.exe https://slh-api-production.up.railway.app/api/health
docker ps --filter name=slh- --format "table {{.Names}}`t{{.Status}}"
git -C D:\SLH_ECOSYSTEM log --oneline -5
git -C D:\SLH_ECOSYSTEM\website log --oneline -5
```

---

## 🟢 2. Deploy state check (Railway-specific)

```powershell
$API = "https://slh-api-production.up.railway.app"
curl.exe -s "$API/api/health"
# Expected once Railway deploys latest: "version":"1.1.1" or higher

# Is the ambassador CRM endpoint live yet?
curl.exe -s -w "`nHTTP %{http_code}`n" `
  -H "X-Admin-Key: slh_admin_2026_rotated_04_20" `
  "$API/api/ambassador/contacts?ambassador_id=1"
# 200 or 403 = deployed · 404 = NOT deployed yet (Railway stuck)

# Is Tzvika now in founders?
curl.exe -s -H "X-Broadcast-Key: slh-broadcast-2026-change-me" "$API/api/ops/reality" | `
  python -c "import sys,json; d=json.load(sys.stdin); f=d['users'].get('founders',[]); print('founders:',len(f),'tzvika:',any(u['telegram_id']==1185887485 for u in f))"
```

---

## 🟢 3. Data integrity

```powershell
cd D:\SLH_ECOSYSTEM
# Full scan, print summary:
python scripts\audit_data_integrity.py

# High-severity only (blocking):
python scripts\audit_data_integrity.py --severity HIGH

# JSON for processing:
python scripts\audit_data_integrity.py --json > audit.json
```

Current high-severity should be 1: `website/js/slh-skeleton.js:37` `opts.count || 4` (legitimate library default, not phantom data).

---

## 🟢 4. Send Telegram broadcast (API)

```powershell
$KEY = "slh-broadcast-2026-change-me"
$API = "https://slh-api-production.up.railway.app"

# To ALL registered users (dry-run first, ALWAYS):
$body = @{
    target = "registered"
    message = "your message here"
    admin_key = $KEY
    dry_run = $true   # ← REMOVE after confirming recipient count
} | ConvertTo-Json

curl.exe -X POST -H "Content-Type: application/json" -d $body "$API/api/broadcast/send"

# To ONE user (custom):
$body = @{
    target = "custom"
    custom_ids = @(8088324234)   # single or array of Telegram IDs
    message = "היי אליעזר..."
    admin_key = $KEY
} | ConvertTo-Json

curl.exe -X POST -H "Content-Type: application/json" -d $body "$API/api/broadcast/send"
```

Response shape: `{"ok":true,"broadcast_id":<n>,"total_recipients":<n>,"success":<n>,"failed":<n>}`. `failed>0` usually = user hasn't /start'd @SLH_AIR_bot.

---

## 🟢 5. Query prod DB (via API, no direct DB access from here)

```powershell
$KEY = "slh-broadcast-2026-change-me"
$API = "https://slh-api-production.up.railway.app"

# Single source of truth admin dump:
curl.exe -s -H "X-Broadcast-Key: $KEY" "$API/api/ops/reality" | python -m json.tool | Select-Object -First 80

# Community posts:
curl.exe -s "$API/api/community/posts?limit=10" | python -m json.tool

# Community stats:
curl.exe -s "$API/api/community/stats"

# Admin devices list:
curl.exe -s -H "X-Admin-Key: slh_admin_2026_rotated_04_20" "$API/api/admin/devices/list"

# Events log:
curl.exe -s -H "X-Admin-Key: slh_admin_2026_rotated_04_20" "$API/api/admin/events?limit=20"
```

---

## 🟢 6. Docker lifecycle

```powershell
cd D:\SLH_ECOSYSTEM

# Check one bot's logs:
docker logs slh-ledger --tail 30

# Rebuild + restart one service:
docker compose build ledger-bot
docker compose up -d ledger-bot

# Restart all (careful — disrupts active users):
docker compose restart

# Everything down:
docker compose down

# Full reset (data PRESERVED in named volumes):
docker compose down; docker compose up -d --build
```

---

## 🟢 7. Git operations (both repos)

```powershell
# API repo (D:\SLH_ECOSYSTEM):
cd D:\SLH_ECOSYSTEM
git status --short
git diff --stat
git log --oneline origin/master -5

# Website repo (separate!):
cd D:\SLH_ECOSYSTEM\website
git status --short
git log --oneline origin/main -5

# Commit with correct author (global config is wrong):
$env:GIT_AUTHOR_NAME="Osif Kaufman Ungar"
$env:GIT_AUTHOR_EMAIL="osif.erez.ungar@gmail.com"
$env:GIT_COMMITTER_NAME="Osif Kaufman Ungar"
$env:GIT_COMMITTER_EMAIL="osif.erez.ungar@gmail.com"
git add <files>
git commit -m "type(scope): ..."
git push origin master   # or main for website

# Verify author on last commit:
git log -1 --format='%h | %an <%ae> | %s'
```

Bypass pre-commit guard for legitimate large commits:
```powershell
$env:GUARD_CONFIRMED="1"
git commit -m "feat(bulk): ..."
Remove-Item env:GUARD_CONFIRMED   # clean up
```

---

## 🟢 8. Analytics funnel — manual query (until dashboard is built)

```powershell
$API = "https://slh-api-production.up.railway.app"
# Raw events (if endpoint deployed):
curl.exe -s -H "X-Admin-Key: slh_admin_2026_rotated_04_20" "$API/api/admin/events?limit=50"

# From within browser console (F12) on any page:
# SLH_Analytics.getStats();
```

Tracking convention for all funnel pages (already wired):
- `?uid=<tg_id>&src=<tg|wa|fb|direct>&campaign=<segment>`
- Events: `<page>_view`, `<page>_cta_<name>`

---

## 🟢 9. Send outreach batch (personal messages — Osif only)

Osif workflow for `ops/OUTREACH_BATCH_<date>.md`:
1. Open the markdown file + Telegram Desktop side by side
2. For each user: `Ctrl+K` in Telegram → paste `@handle` → open chat
3. Copy the Hebrew message block from markdown (triple-backtick-fenced)
4. Paste in Telegram → Send
5. Next user

Not automatable from this side: bot DMs had 0/6 engagement; personal-from-Osif had 1/1 reply (Yaara).

---

## 🟢 10. Emergency commands

```powershell
# API down — check Railway status:
# https://railway.app/project/slh-api → Deployments
# (No programmatic Railway access from here)

# Admin endpoint returns 403:
# Check env: should have ADMIN_API_KEYS set on Railway
# Verify key works: curl with both header names
curl.exe -H "X-Admin-Key: slh_admin_2026_rotated_04_20" "$API/api/admin/devices/list"

# Leaked a secret:
# 1. Rotate it on Railway dashboard (Variables tab)
# 2. Update .env locally: docker compose up -d <services>
# 3. Log in ops/INCIDENTS.md

# Drift — big diff unexpected:
cd D:\SLH_ECOSYSTEM
git stash push -m "possibly-good"
git fetch origin
git log --oneline HEAD origin/master -5
git rev-list --left-right --count HEAD...origin/master   # must be 0 0 if clean
# If drift: git checkout <clean-commit> -- path/to/file.py
```

---

## 🟢 11. Generate next outreach batch

```powershell
# Edit the USERS list in scripts/bulk_personalized_messages.py, then:
cd D:\SLH_ECOSYSTEM
python scripts\bulk_personalized_messages.py
# Output: ops/OUTREACH_BATCH_<YYYYMMDD>.md
```

---

## 🟢 12. One-shot "is everything OK?"

```powershell
cd D:\SLH_ECOSYSTEM
.\slh-start.ps1 -StatusOnly
python scripts\audit_data_integrity.py --severity HIGH
curl.exe -s https://slh-nft.com/ -o nul -w "website: %{http_code}`n"
curl.exe -s https://slh-api-production.up.railway.app/api/health
```

If all green → proceed with planned work. If any red → see `ops/OPS_RUNBOOK.md` §1-6.
