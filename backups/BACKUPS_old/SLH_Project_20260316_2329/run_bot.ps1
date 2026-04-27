$date = Get-Date -Format "yyyy-MM-dd_HH-mm"
Write-Host "--- Starting Backup ---" -ForegroundColor Cyan

# 1. Export DB to CSV
psql -U postgres -d slh_db -c "\copy users TO 'D:\SLH_PROJECT_V2\users_backup.csv' WITH CSV HEADER"

# 2. Create ZIP Backup
Get-ChildItem -Path "D:\SLH_PROJECT_V2\*" -Exclude "*.zip", "venv" | Compress-Archive -DestinationPath "D:\SLH_BACKUP_AUTO_$date.zip" -Force

Write-Host "--- Backup Complete! Starting Bot ---" -ForegroundColor Green

# 3. Run using the VENV we just created
.\venv\Scripts\python.exe main.py