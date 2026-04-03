param()

$ErrorActionPreference = "Stop"
Set-Location (Split-Path -Parent $PSScriptRoot)

Write-Host "=== RAILWAY LOG SHELL MODE ===" -ForegroundColor Cyan
Write-Host "You are about to open Railway shell." -ForegroundColor Yellow
Write-Host "Inside shell use Linux commands only." -ForegroundColor Yellow
Write-Host "Example: tail -n 120 /app/logs/worker.log" -ForegroundColor Yellow
Write-Host "Do NOT use \q here." -ForegroundColor Yellow
Write-Host "Exit shell with: exit" -ForegroundColor Yellow
Write-Host ""

railway ssh