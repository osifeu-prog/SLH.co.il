param([string]$Method)

$token = $env:TELEGRAM_BOT_TOKEN

if (-not $token) {
    Write-Host "Missing TELEGRAM_BOT_TOKEN" -ForegroundColor Red
    exit
}

Invoke-RestMethod "https://api.telegram.org/bot$token/$Method"