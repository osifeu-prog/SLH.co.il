param()

$ErrorActionPreference = "Stop"
Set-Location (Split-Path -Parent $PSScriptRoot)

Write-Host "=== RAILWAY POSTGRES MODE ===" -ForegroundColor Cyan
Write-Host "You are about to open psql." -ForegroundColor Yellow
Write-Host "Inside psql use SQL only." -ForegroundColor Yellow
Write-Host "Exit psql with: \q" -ForegroundColor Yellow
Write-Host ""

railway connect