# Phase 0B rebuild helper
# Rebuilds and restarts all bots touched by the Phase 0B migration so the new
# fail-fast pool code actually loads into running containers.
#
# Usage (elevated PowerShell, from D:\SLH_ECOSYSTEM):
#   .\ops\PHASE_0B_REBUILD_BOTS.ps1
# Or one-liner:
#   powershell -ExecutionPolicy Bypass -File .\ops\PHASE_0B_REBUILD_BOTS.ps1
#
# Rollback if something misbehaves:
#   docker compose restart <service_name>   — just restart, don't rebuild
#   docker compose logs -f <service_name>   — inspect

param(
    [switch]$DryRun = $false,
    [switch]$SkipPull = $false,
    [switch]$NoCache = $false
)

$ErrorActionPreference = "Continue"

$services = @(
    # Entry points — had their own shared_db_core.py copied in
    "academia-bot",
    "nfty-bot",
    "osif-shop",
    "expertnet-bot",

    # Services that use the slh_payments canonical (resynced)
    "wallet",
    "factory",
    "fun",
    "botshop",
    "admin-bot",

    # API itself — picks up routes/academia_ugc.py column fix + admin/events
    "slh-api"   # may not be a local docker service; Railway auto-deploys this on push
)

Write-Host "Phase 0B bot rebuild helper" -ForegroundColor Cyan
Write-Host "Services: $($services -join ', ')" -ForegroundColor Cyan
Write-Host ""

Set-Location "D:\SLH_ECOSYSTEM"

if (-not $SkipPull) {
    Write-Host "--- git pull ---" -ForegroundColor Yellow
    if ($DryRun) {
        Write-Host "[DRY] git pull"
    } else {
        git pull origin master
    }
    Write-Host ""
}

Write-Host "--- docker compose ps (before) ---" -ForegroundColor Yellow
docker compose ps
Write-Host ""

$buildFlag = if ($NoCache) { "--no-cache" } else { "" }

foreach ($s in $services) {
    if ($s -eq "slh-api") { continue }  # handled by Railway, not local compose

    Write-Host "=== $s ===" -ForegroundColor Green
    if ($DryRun) {
        Write-Host "[DRY] docker compose up -d --build $buildFlag $s"
        continue
    }
    docker compose up -d --build $buildFlag $s 2>&1 | Tail -Last 10
    Start-Sleep -Seconds 2
    docker compose ps --filter "name=$s"
    Write-Host ""
}

Write-Host "--- final health check ---" -ForegroundColor Yellow
Write-Host "Running containers:"
docker compose ps

Write-Host ""
Write-Host "Testing Railway API:" -NoNewline
try {
    $r = Invoke-RestMethod -Uri "https://slh-api-production.up.railway.app/api/health" -TimeoutSec 5
    Write-Host " $($r.status) ($($r.db))" -ForegroundColor Green
} catch {
    Write-Host " FAILED: $_" -ForegroundColor Red
}

Write-Host ""
Write-Host "Done. Inspect failing services with:" -ForegroundColor Cyan
Write-Host "  docker compose logs -f <service>" -ForegroundColor Gray
Write-Host ""
Write-Host "If a bot fails to start due to DB connection:" -ForegroundColor Yellow
Write-Host "  docker compose logs <service> | Select-String 'CRITICAL'" -ForegroundColor Gray
Write-Host "  The new shared_db_core fails fast on DB down — good, that means the" -ForegroundColor Gray
Write-Host "  migration is active. Check DATABASE_URL env is set correctly." -ForegroundColor Gray
