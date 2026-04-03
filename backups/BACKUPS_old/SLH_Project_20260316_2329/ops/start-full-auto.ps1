param()

$ErrorActionPreference = "Stop"
$ROOT = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location (Split-Path -Parent $ROOT)

function Info([string]$m) { Write-Host $m -ForegroundColor Cyan }
function Good([string]$m) { Write-Host $m -ForegroundColor Green }

$envPath = ".\.env"
if (-not (Test-Path $envPath)) { throw ".env not found" }

$envText = Get-Content $envPath -Raw
$botToken = ([regex]::Match($envText,'(?m)^BOT_TOKEN=(.+)$')).Groups[1].Value.Trim()
$webhookSecret = ([regex]::Match($envText,'(?m)^WEBHOOK_SECRET=(.+)$')).Groups[1].Value.Trim()
$webhookUrl = "https://slhprojectv2-production.up.railway.app/tg/webhook"

if (-not $botToken) { throw "BOT_TOKEN missing in .env" }

if ($envText -match '(?m)^WEBHOOK_URL=') {
  $envText = [regex]::Replace($envText, '(?m)^WEBHOOK_URL=.*$', "WEBHOOK_URL=$webhookUrl")
} else {
  $envText = $envText.TrimEnd() + "`nWEBHOOK_URL=$webhookUrl`n"
}
$enc = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllText((Resolve-Path $envPath), ($envText -replace "`r`n","`n"), $enc)

Info "Stopping project python"
Get-Process python -ErrorAction SilentlyContinue |
  Where-Object { $_.Path -like "*SLH_PROJECT_V2*" } |
  Stop-Process -Force -ErrorAction SilentlyContinue

Start-Sleep -Seconds 1

Info "Ensuring Redis is up"
docker compose -f docker-compose.redis.yml up -d | Out-Null

Info "Starting webhook server"
Start-Process powershell.exe -ArgumentList @(
  '-NoExit',
  '-Command',
  '& { Set-Location ''D:\SLH_PROJECT_V2''; $global:ErrorActionPreference = ''Stop''; .\venv\Scripts\python.exe .\webhook_server.py }'
) | Out-Null

Start-Sleep -Seconds 4

Info "Checking local health"
$health = Invoke-RestMethod -Method Get -Uri "http://127.0.0.1:8080/healthz"
if (-not $health.ok) { throw "Local healthz failed after starting webhook server" }
Good "Webhook server healthz OK"

Info "Starting worker"
Start-Process powershell.exe -ArgumentList @(
  '-NoExit',
  '-Command',
  '& { Set-Location ''D:\SLH_PROJECT_V2''; $global:ErrorActionPreference = ''Stop''; .\venv\Scripts\python.exe .\worker.py }'
) | Out-Null

Start-Sleep -Seconds 2

Info "Refreshing webhook in Telegram -> Railway"
Invoke-RestMethod -Uri ("https://api.telegram.org/bot{0}/deleteWebhook?drop_pending_updates=true" -f $botToken) | Out-Null

$body = @{ url = $webhookUrl }
if ($webhookSecret) { $body["secret_token"] = $webhookSecret }

$resp = Invoke-RestMethod -Method Post -Uri ("https://api.telegram.org/bot{0}/setWebhook" -f $botToken) -Body $body
if (-not $resp.ok) { throw "setWebhook failed" }

$wh = Invoke-RestMethod -Uri ("https://api.telegram.org/bot{0}/getWebhookInfo" -f $botToken)
if ($wh.result.url -ne $webhookUrl) {
  throw "Webhook mismatch after setWebhook. env=$webhookUrl api=$($wh.result.url)"
}

Good "Webhook registered successfully"
Good "START FULL AUTO COMPLETED (Railway-only mode)"
"FINAL_WEBHOOK_URL=$webhookUrl"