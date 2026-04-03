param()

$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)

$envPath = Join-Path (Get-Location) ".env"
if (-not (Test-Path $envPath)) { throw ".env not found" }

$envText = Get-Content $envPath -Raw
$BOT_TOKEN = [regex]::Match($envText, '(?m)^\s*BOT_TOKEN\s*=\s*(.+?)\s*$').Groups[1].Value.Trim()

if (-not $BOT_TOKEN) { throw "BOT_TOKEN not found in .env" }

$url = "https://api.telegram.org/bot$BOT_TOKEN/deleteWebhook?drop_pending_updates=true"

Write-Host "Deleting webhook and dropping pending updates..." -ForegroundColor Cyan
$r = Invoke-RestMethod $url -Method Post

$r | Format-List
Write-Host ""
Write-Host "CLEAR_PENDING_UPDATES_DONE" -ForegroundColor Green
Write-Host "Next step: set webhook again with .\ops\set-webhook.ps1 -BaseUrl <REAL_URL>" -ForegroundColor Yellow