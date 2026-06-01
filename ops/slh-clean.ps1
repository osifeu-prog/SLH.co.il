# slh-clean.ps1 — Safe cleanup script for SLH ECOSYSTEM
# Created: 2026-04-10 | Author: Claude + Osif
#
# WHAT IT DOES:
#   1. Stops running SLH containers gracefully via docker compose
#   2. Removes EXITED containers (not running ones)
#   3. Prunes DANGLING images only (NOT -a which would remove tagged ones)
#   4. Does NOT touch volumes (DB data preserved)
#   5. Does NOT touch networks (might break running containers)
#
# WHAT IT INTENTIONALLY DOES NOT DO:
#   - No `docker system prune -a` (would remove images for bots not currently running)
#   - No `docker volume prune` (would wipe PostgreSQL data)
#   - No `docker network prune` (would break slh-* networks)
#
# USAGE:
#   .\slh-clean.ps1             (dry-run — shows what would happen)
#   .\slh-clean.ps1 -Force      (actually runs)
#   .\slh-clean.ps1 -Force -StopAll  (stops running containers too)

param(
    [switch]$Force,
    [switch]$StopAll
)

$ErrorActionPreference = "Continue"
$ComposeFile = "D:\SLH_ECOSYSTEM\docker-compose.yml"

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  SLH ECOSYSTEM - Safe Cleanup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# --- Phase 0: Dry-run warning ---
if (-not $Force) {
    Write-Host "[DRY RUN] No changes will be made. Use -Force to execute." -ForegroundColor Yellow
    Write-Host ""
}

# --- Phase 1: Pre-cleanup snapshot ---
Write-Host "[1/5] Pre-cleanup snapshot..." -ForegroundColor Cyan
$runningCount = (docker ps --filter "name=slh-" -q | Measure-Object).Count
$exitedCount = (docker ps -a --filter "name=slh-" --filter "status=exited" -q | Measure-Object).Count
Write-Host "    Running SLH containers: $runningCount"
Write-Host "    Exited SLH containers:  $exitedCount"
Write-Host ""

# --- Phase 2: Stop running (only if -StopAll) ---
if ($StopAll) {
    Write-Host "[2/5] Stopping running containers via docker compose..." -ForegroundColor Cyan
    if ($Force) {
        docker compose -f $ComposeFile stop
        Write-Host "    Stopped." -ForegroundColor Green
    } else {
        Write-Host "    [DRY] Would run: docker compose stop" -ForegroundColor Yellow
    }
} else {
    Write-Host "[2/5] Leaving running containers alone (use -StopAll to stop them)" -ForegroundColor Yellow
}
Write-Host ""

# --- Phase 3: Remove exited containers ---
Write-Host "[3/5] Removing exited SLH containers..." -ForegroundColor Cyan
$exited = docker ps -a --filter "name=slh-" --filter "status=exited" -q
if ($exited) {
    if ($Force) {
        docker rm $exited | Out-Null
        Write-Host "    Removed $exitedCount container(s)." -ForegroundColor Green
    } else {
        docker ps -a --filter "name=slh-" --filter "status=exited" --format "    [DRY] Would remove: {{.Names}} ({{.Status}})" | Write-Host -ForegroundColor Yellow
    }
} else {
    Write-Host "    None to remove." -ForegroundColor Green
}
Write-Host ""

# --- Phase 4: Prune DANGLING images only ---
Write-Host "[4/5] Pruning dangling images (tagged images preserved)..." -ForegroundColor Cyan
if ($Force) {
    $result = docker image prune -f 2>&1
    Write-Host "    $result" -ForegroundColor Green
} else {
    Write-Host "    [DRY] Would run: docker image prune -f" -ForegroundColor Yellow
}
Write-Host ""

# --- Phase 5: Safety confirmation ---
Write-Host "[5/5] Safety check — these are PRESERVED:" -ForegroundColor Cyan
Write-Host "    - Named volumes (PostgreSQL data, Redis data)" -ForegroundColor Green
Write-Host "    - Tagged images (slh_ecosystem-*)" -ForegroundColor Green
Write-Host "    - Networks (slh-net, slh_ecosystem_default)" -ForegroundColor Green
Write-Host "    - .env file" -ForegroundColor Green
Write-Host ""

Write-Host "========================================" -ForegroundColor Cyan
if ($Force) {
    Write-Host "  Cleanup complete." -ForegroundColor Green
    Write-Host "  Run slh-rebuild.ps1 to restart services." -ForegroundColor Cyan
} else {
    Write-Host "  DRY RUN ONLY. Re-run with -Force to execute." -ForegroundColor Yellow
}
Write-Host "========================================" -ForegroundColor Cyan
