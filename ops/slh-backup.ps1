# slh-backup.ps1 — Full backup of SLH ECOSYSTEM
# Created: 2026-04-10 | Author: Claude + Osif
# Supersedes slh-backup.bat with more thorough backup
#
# WHAT IT BACKS UP:
#   1. All 6 PostgreSQL databases (pg_dump + pg_dumpall)
#   2. .env file
#   3. docker-compose.yml
#   4. Git HEAD hashes for all 3 repos (ecosystem, website, api)
#   5. List of running containers
#   6. List of installed images
#
# WHERE:
#   D:\SLH_BACKUPS\FULL_yyyyMMdd_HHmmss\
#
# USAGE:
#   .\slh-backup.ps1             (creates new backup)

$ErrorActionPreference = "Continue"
$ts = Get-Date -Format "yyyyMMdd_HHmmss"
$backup = "D:\SLH_BACKUPS\FULL_$ts"

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  SLH ECOSYSTEM - Full Backup" -ForegroundColor Cyan
Write-Host "  Destination: $backup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

New-Item -ItemType Directory -Path $backup -Force | Out-Null

# --- Phase 1: PostgreSQL dumps ---
Write-Host "[1/5] Backing up PostgreSQL..." -ForegroundColor Cyan

# Full dumpall (all DBs + roles + globals)
docker exec slh-postgres pg_dumpall -U postgres | Out-File -Encoding UTF8 "$backup\all_databases.sql"
$size = (Get-Item "$backup\all_databases.sql").Length / 1KB
Write-Host "    all_databases.sql: $([math]::Round($size, 1)) KB" -ForegroundColor Green

# Individual DB dumps (for easier selective restore)
$dbs = @("slh_main", "slh_botshop", "slh_wallet", "slh_factory", "slh_guardian")
foreach ($db in $dbs) {
    docker exec slh-postgres pg_dump -U postgres -d $db | Out-File -Encoding UTF8 "$backup\$db.sql"
    $size = (Get-Item "$backup\$db.sql").Length / 1KB
    Write-Host "    $db.sql: $([math]::Round($size, 1)) KB" -ForegroundColor Green
}
Write-Host ""

# --- Phase 2: Config files ---
Write-Host "[2/5] Backing up config files..." -ForegroundColor Cyan
Copy-Item "D:\SLH_ECOSYSTEM\.env" "$backup\env.backup" -ErrorAction SilentlyContinue
Copy-Item "D:\SLH_ECOSYSTEM\docker-compose.yml" "$backup\docker-compose.yml.backup" -ErrorAction SilentlyContinue
Write-Host "    .env + docker-compose.yml" -ForegroundColor Green
Write-Host ""

# --- Phase 3: Git state ---
Write-Host "[3/5] Recording git state..." -ForegroundColor Cyan
Push-Location "D:\SLH_ECOSYSTEM"
git log -1 --format="%H %s" 2>$null | Out-File -Encoding UTF8 "$backup\ecosystem_head.txt"
Pop-Location
Push-Location "D:\SLH_ECOSYSTEM\website"
git log -1 --format="%H %s" 2>$null | Out-File -Encoding UTF8 "$backup\website_head.txt"
Pop-Location
Push-Location "D:\SLH_ECOSYSTEM\api"
git log -1 --format="%H %s" 2>$null | Out-File -Encoding UTF8 "$backup\api_head.txt"
Pop-Location
Write-Host "    3 git heads recorded" -ForegroundColor Green
Write-Host ""

# --- Phase 4: Docker state ---
Write-Host "[4/5] Recording docker state..." -ForegroundColor Cyan
docker ps -a --format "{{.Names}} {{.Status}}" | Out-File -Encoding UTF8 "$backup\containers.txt"
docker images --format "{{.Repository}}:{{.Tag}} {{.Size}}" | Sort-Object | Out-File -Encoding UTF8 "$backup\images.txt"
Write-Host "    containers.txt + images.txt" -ForegroundColor Green
Write-Host ""

# --- Phase 5: Summary ---
$totalSize = (Get-ChildItem $backup -Recurse -File | Measure-Object -Property Length -Sum).Sum / 1KB
Write-Host "[5/5] Backup complete." -ForegroundColor Green
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Total size: $([math]::Round($totalSize, 1)) KB" -ForegroundColor Green
Write-Host "  Path: $backup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
