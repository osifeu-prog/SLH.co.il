# SLH ECOSYSTEM - Startup Script
param(
    [ValidateSet("all","core","guardian","botshop","wallet","factory","fun","infra")]
    [string]$Service = "all"
)

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

Write-Host @"
 ====================================
   SLH ECOSYSTEM - Docker Launcher
 ====================================
"@ -ForegroundColor Cyan

# Check Docker
try {
    docker info 2>&1 | Out-Null
} catch {
    Write-Host "ERROR: Docker is not running. Start Docker Desktop first!" -ForegroundColor Red
    exit 1
}

# Check .env
if (-not (Test-Path ".env")) {
    if (Test-Path ".env.example") {
        Write-Host "No .env found. Creating from .env.example..." -ForegroundColor Yellow
        Copy-Item ".env.example" ".env"
        Write-Host "EDIT .env with your bot tokens before starting!" -ForegroundColor Red
        exit 1
    }
}

switch ($Service) {
    "infra"    { docker compose up -d postgres redis }
    "core"     { docker compose up -d postgres redis core-bot }
    "guardian"  { docker compose up -d postgres redis guardian-bot }
    "botshop"  { docker compose up -d postgres botshop }
    "wallet"   { docker compose up -d postgres wallet-bot }
    "factory"  { docker compose up -d postgres factory-bot }
    "fun"      { docker compose up -d fun-bot }
    "all"      { docker compose up -d }
}

Write-Host ""
Write-Host "Status:" -ForegroundColor Green
docker compose ps
