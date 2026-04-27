$ROOT="D:\SLH_PROJECT_V2"
$TS=Get-Date -Format yyyyMMdd_HHmmss

$BACKUP="$ROOT\backups\backup_$TS"
New-Item -ItemType Directory -Path $BACKUP -Force | Out-Null

Write-Host "Backing up database..."

psql -U postgres -d slh_db -c "\copy users to '$BACKUP\users.csv' csv header"
psql -U postgres -d slh_db -c "\copy tasks to '$BACKUP\tasks.csv' csv header"
psql -U postgres -d slh_db -c "\copy sell_orders to '$BACKUP\sell_orders.csv' csv header"
psql -U postgres -d slh_db -c "\copy withdrawals to '$BACKUP\withdrawals.csv' csv header"

Write-Host "Database backup complete."

Write-Host "Backing up code..."

$ZIP="$BACKUP\project_$TS.zip"

Get-ChildItem $ROOT -Exclude backups,state,logs,venv | Compress-Archive -DestinationPath $ZIP -Force

Write-Host "Backup created: $BACKUP"
