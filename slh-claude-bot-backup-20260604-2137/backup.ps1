# backup.ps1  SLH Spark AI Auto-Backup
$date = Get-Date -Format "yyyyMMdd-HHmm"
New-Item -ItemType Directory -Force -Path backups | Out-Null

# 1. קוד הבוט
Copy-Item bot.py "backups\bot_backup_$date.py" -Force

# 2. גיבוי DB (באמצעות Railway CLI)
Write-Host "Dumping database..." -ForegroundColor Cyan
railway run --service slh-AI-bot "pg_dump \$DATABASE_URL" | Out-File "backups\db_dump_$date.sql" -Encoding utf8

# 3. משתני סביבה
railway variables list --service slh-AI-bot | Out-File "backups\env_snapshot_$date.txt" -Encoding utf8

# 4. מסמך ה‑Onboarding
Copy-Item docs\SLH_ONBOARDING.md "backups\SLH_ONBOARDING_$date.md" -Force

Write-Host "Backup completed: backups\bot_backup_$date.py" -ForegroundColor Green
Write-Host "DB dump, env snapshot, and onboarding doc also saved." -ForegroundColor Green
