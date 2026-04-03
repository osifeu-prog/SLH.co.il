param()

$ErrorActionPreference = "Stop"
Set-Location (Split-Path -Parent $PSScriptRoot)

Write-Host "=== COMMERCE DB ALIGN ===" -ForegroundColor Cyan
Write-Host "This opens Railway Postgres. Run the four official patch files in order." -ForegroundColor Yellow
Write-Host ""

railway connect