# slh-db-sync.ps1 — Sync local Docker Postgres → Railway Postgres
# Created: 2026-04-10 | Author: Claude + Osif
#
# WHY:
#   Local bots write to local Docker Postgres (slh_main on slh-postgres container).
#   Railway API reads from Railway Postgres (junction.proxy.rlwy.net).
#   They are not connected. This script bridges the gap.
#
# WHAT IT SYNCS:
#   - token_balances (SLH, ZVK for all users)
#   - users → web_users (if needed, more complex mapping)
#
# WHAT IT DOES NOT SYNC:
#   - referrals (already managed by Railway API)
#   - staking positions (managed by Railway API)
#   - community posts (Railway-only feature)
#
# USAGE:
#   .\slh-db-sync.ps1             (dry-run — shows what would be synced)
#   .\slh-db-sync.ps1 -Force      (actually runs)
#
# SCHEDULE:
#   Consider running via Task Scheduler every 15 minutes:
#   schtasks /Create /TN "SLH DB Sync" /SC MINUTE /MO 15 /TR "powershell -File D:\SLH_ECOSYSTEM\ops\slh-db-sync.ps1 -Force"

param(
    [switch]$Force
)

$ErrorActionPreference = "Stop"
$EnvFile = "D:\SLH_ECOSYSTEM\.env"

# --- Read RAILWAY_DATABASE_URL from .env ---
$railwayUrl = $null
Get-Content $EnvFile | ForEach-Object {
    if ($_ -match '^RAILWAY_DATABASE_URL=(.+)$') {
        $railwayUrl = $Matches[1].Trim()
    }
}
if (-not $railwayUrl) {
    Write-Host "ERROR: RAILWAY_DATABASE_URL not found in .env" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  SLH DB Sync: Local → Railway" -ForegroundColor Cyan
if (-not $Force) {
    Write-Host "  [DRY RUN] — use -Force to execute" -ForegroundColor Yellow
}
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# --- Step 1: Count rows in both DBs ---
Write-Host "[1/4] Checking row counts..." -ForegroundColor Cyan

$localCount = docker exec slh-postgres psql -U postgres -d slh_main -t -c "SELECT COUNT(*) FROM token_balances;" | ForEach-Object { $_.Trim() }
Write-Host "    Local (Docker):  $localCount token_balances rows" -ForegroundColor Green

# For Railway count - use a temp psql container
$tempPsql = docker run --rm -i postgres:15-alpine psql "$railwayUrl" -t -c "SELECT COUNT(*) FROM token_balances;" 2>&1 | Select-Object -Last 1
$railwayCount = $tempPsql.Trim()
Write-Host "    Railway (cloud): $railwayCount token_balances rows" -ForegroundColor Green
Write-Host ""

# --- Step 2: Extract local data ---
Write-Host "[2/4] Extracting local token_balances..." -ForegroundColor Cyan
$csvData = docker exec slh-postgres psql -U postgres -d slh_main -c "COPY (SELECT user_id, token, balance FROM token_balances ORDER BY user_id, token) TO STDOUT WITH CSV;"
$rowCount = ($csvData -split "`n" | Where-Object { $_.Trim() }).Count
Write-Host "    Extracted $rowCount rows" -ForegroundColor Green
Write-Host ""

# --- Step 3: Build INSERT statements ---
Write-Host "[3/4] Building sync SQL..." -ForegroundColor Cyan
$sqlStatements = @("BEGIN;")
foreach ($line in ($csvData -split "`n")) {
    if (-not $line.Trim()) { continue }
    $parts = $line -split ','
    if ($parts.Count -ge 3) {
        $uid = $parts[0].Trim()
        $token = $parts[1].Trim().Replace("'", "''")
        $balance = $parts[2].Trim()
        $sqlStatements += "INSERT INTO token_balances (user_id, token, balance) VALUES ($uid, '$token', $balance) ON CONFLICT (user_id, token) DO UPDATE SET balance = EXCLUDED.balance, updated_at = CURRENT_TIMESTAMP;"
    }
}
$sqlStatements += "COMMIT;"
$sqlScript = $sqlStatements -join "`n"

Write-Host "    Built $($sqlStatements.Count - 2) INSERT statements" -ForegroundColor Green
Write-Host ""

# --- Step 4: Execute (if -Force) ---
if ($Force) {
    Write-Host "[4/4] Executing sync to Railway..." -ForegroundColor Cyan
    $sqlScript | docker run --rm -i postgres:15-alpine psql "$railwayUrl" 2>&1 | Select-String -Pattern "INSERT|UPDATE|ERROR|COMMIT" | ForEach-Object { Write-Host "    $_" }

    # Verify
    $newCount = docker run --rm -i postgres:15-alpine psql "$railwayUrl" -t -c "SELECT COUNT(*) FROM token_balances;" 2>&1 | Select-Object -Last 1
    Write-Host "    Railway now has: $($newCount.Trim()) rows" -ForegroundColor Green
} else {
    Write-Host "[4/4] [DRY RUN] Would sync $($sqlStatements.Count - 2) rows" -ForegroundColor Yellow
    Write-Host "    Re-run with -Force to execute" -ForegroundColor Yellow
}
Write-Host ""

Write-Host "========================================" -ForegroundColor Cyan
if ($Force) {
    Write-Host "  Sync complete." -ForegroundColor Green
    Write-Host "  Verify: curl https://slh-api-production.up.railway.app/api/wallet/224223270/balances" -ForegroundColor Cyan
}
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
