param()

$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)

Write-Host "Open tunnel manually now:" -ForegroundColor Cyan
Write-Host "cloudflared tunnel --url http://127.0.0.1:8080" -ForegroundColor Yellow
cloudflared tunnel --url http://127.0.0.1:8080