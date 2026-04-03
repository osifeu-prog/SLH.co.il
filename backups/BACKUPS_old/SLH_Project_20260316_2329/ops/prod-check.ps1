param()

$ErrorActionPreference="Stop"

$envText=Get-Content .\.env -Raw
$botToken=([regex]::Match($envText,'(?m)^BOT_TOKEN=(.+)$')).Groups[1].Value.Trim()
$webhookUrl=([regex]::Match($envText,'(?m)^WEBHOOK_URL=(.+)$')).Groups[1].Value.Trim()
$base=$webhookUrl -replace "/tg/webhook$",""

Write-Host ""
Write-Host "Telegram webhook info" -ForegroundColor Cyan

irm "https://api.telegram.org/bot$botToken/getWebhookInfo" | ConvertTo-Json -Depth 8

Write-Host ""
Write-Host "Railway health" -ForegroundColor Cyan

irm "$base/health"

Write-Host ""
Write-Host "Railway healthz" -ForegroundColor Cyan

irm "$base/healthz"
