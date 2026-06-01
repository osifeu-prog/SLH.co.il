# slh-rebuild.ps1 — Full rebuild + restart for SLH ECOSYSTEM
# Created: 2026-04-10 | Author: Claude + Osif
#
# WHAT IT DOES:
#   1. Infrastructure first (postgres, redis) — wait for healthy
#   2. All bot services second
#   3. Shows final status table
#
# WHEN TO USE:
#   - After clean reboot of Windows
#   - After major code changes (use -Rebuild to force fresh images)
#   - After Docker Desktop update
#
# USAGE:
#   .\slh-rebuild.ps1             (up -d, no rebuild)
#   .\slh-rebuild.ps1 -Rebuild    (build --no-cache + up -d)

param(
    [switch]$Rebuild
)

$ErrorActionPreference = "Continue"
$ComposeFile = "D:\SLH_ECOSYSTEM\docker-compose.yml"

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  SLH ECOSYSTEM - Rebuild & Start" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# --- Phase 1: Optional rebuild ---
if ($Rebuild) {
    Write-Host "[1/4] Building fresh images (--no-cache)..." -ForegroundColor Cyan
    docker compose -f $ComposeFile build --no-cache
    Write-Host ""
}

# --- Phase 2: Infrastructure first ---
Write-Host "[2/4] Starting infrastructure (postgres, redis)..." -ForegroundColor Cyan
docker compose -f $ComposeFile up -d postgres redis
Write-Host "    Waiting 5 seconds for health checks..." -ForegroundColor Yellow
Start-Sleep 5

# Verify postgres is healthy
$pgHealth = docker inspect slh-postgres --format '{{.State.Health.Status}}' 2>$null
if ($pgHealth -ne "healthy") {
    Write-Host "    WARNING: slh-postgres health = $pgHealth" -ForegroundColor Yellow
    Write-Host "    Waiting another 10 seconds..." -ForegroundColor Yellow
    Start-Sleep 10
}
Write-Host "    Infrastructure ready." -ForegroundColor Green
Write-Host ""

# --- Phase 3: All bot services ---
Write-Host "[3/4] Starting all bot services..." -ForegroundColor Cyan
docker compose -f $ComposeFile up -d
Write-Host "    Waiting 10 seconds for bots to settle..." -ForegroundColor Yellow
Start-Sleep 10
Write-Host ""

# --- Phase 4: Status table ---
Write-Host "[4/4] Final status:" -ForegroundColor Cyan
docker compose -f $ComposeFile ps --format "table {{.Name}}\t{{.Status}}"
Write-Host ""

# Quick health check
$running = (docker ps --filter "name=slh-" -q | Measure-Object).Count
$total = (docker compose -f $ComposeFile config --services | Measure-Object).Count
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Running: $running containers" -ForegroundColor Green
Write-Host "  Defined: $total services in compose" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Smoke-test Railway API
Write-Host "Smoke testing Railway API..." -ForegroundColor Cyan
try {
    $health = Invoke-RestMethod -Uri "https://slh-api-production.up.railway.app/api/health" -TimeoutSec 5
    Write-Host "    Railway API: $($health.status) (DB: $($health.db))" -ForegroundColor Green
} catch {
    Write-Host "    Railway API: UNREACHABLE" -ForegroundColor Red
}
Write-Host ""
