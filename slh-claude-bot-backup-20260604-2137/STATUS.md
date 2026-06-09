# finalize_day.ps1
Write-Host "🔧 Fixing logo to compact version..." -ForegroundColor Cyan
cd D:\slh-website\slh-claude-bot

# 1. Backup current working bot
Copy-Item bot.py bot_stable_last_working.py -Force
Write-Host "✅ Backup saved: bot_stable_last_working.py"

# 2. Replace logo in bot.py with compact version
 = Get-Content bot.py -Raw -Encoding UTF8
 = '(?s)logo = \(.*?╚════════════════════════════╝\)'
 = @'
    logo = (
        "╔═══════════════════════╗\n"
        "║  ✨ SLH SPARK AI v3.3 ✨ ║\n"
        "║   INTELLIGENT ENGINE  ║\n"
        "╚═══════════════════════╝"
    )
'@
 =  -replace , 
[System.IO.File]::WriteAllText("bot.py", , [System.Text.UTF8Encoding]::new(False))
Write-Host "✅ Logo updated (compact version)"

# 3. Create STATUS.md
@"
# SLH Spark AI  Status Report

**Date:** 2026-06-03 00:39
**Deployment:** Active on Railway (diligent-radiance / slh-AI-bot)

## ✅ Working features
- /start (compact logo)
- /register, /identity, /myidentity
- /tap, /tasks, /done
- /checkin, /points, /leaderboard
- /wallet, /deposit, /transfer
- /upgrade, /paid (admin)
- /referral, /invite
- /dashboard, /status
- /crypto, /donate, /guide
- /oracle, /peace
- /admin, /users, /broadcast, /morning, /doctor, /statusapi, /setreminder
- /backup, /crm, /stats, /events, /segments
- /profile, /myid
- /addcustomer, /customers, /addnote, /notes
- /vip

## 🧪 Last deployment
- Latest logs: railway logs --tail 50

## 🚀 Restart bot
Run \.\restart_bot.ps1\ or \ailway up --detach\

