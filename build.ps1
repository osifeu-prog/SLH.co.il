# SLH ECOSYSTEM - Build Script
# Copies shared libraries to all bot contexts before building

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

Write-Host ">>> Syncing shared libraries to all bots..." -ForegroundColor Cyan

# Sync shared lib to all bot directories
$targets = @(
    "D:\telegram-guardian-DOCKER-COMPOSE-ENTERPRISE\shared",
    "D:\SLH_PROJECT_V2\shared",
    "$PSScriptRoot\botshop\shared",
    "$PSScriptRoot\wallet\shared",
    "$PSScriptRoot\factory\shared",
    "$PSScriptRoot\fun\shared",
    "$PSScriptRoot\admin-bot\shared"
)

foreach ($t in $targets) {
    if (-not (Test-Path $t)) { New-Item -ItemType Directory -Force -Path $t | Out-Null }
    Copy-Item -Path "$PSScriptRoot\shared\slh_payments\*" -Destination "$t\slh_payments\" -Recurse -Force -ErrorAction SilentlyContinue
    Copy-Item -Path "$PSScriptRoot\shared\group_config.json" -Destination $t -Force -ErrorAction SilentlyContinue
}

Write-Host ">>> Building all images..." -ForegroundColor Cyan
docker compose build

Write-Host ">>> Restarting..." -ForegroundColor Cyan
docker compose up -d

Write-Host ">>> Done!" -ForegroundColor Green
docker ps --format "table {{.Names}}`t{{.Status}}"
