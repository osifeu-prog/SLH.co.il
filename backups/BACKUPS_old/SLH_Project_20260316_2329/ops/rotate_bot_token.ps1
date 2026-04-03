param(
  [Parameter(Mandatory=$true)]
  [string]$NewBotToken,

  [Parameter(Mandatory=$true)]
  [string]$ExpectedBotUsername
)

$ErrorActionPreference = "Stop"
$ROOT = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location (Split-Path -Parent $ROOT)

function Info([string]$m) { Write-Host $m -ForegroundColor Cyan }
function Good([string]$m) { Write-Host $m -ForegroundColor Green }
function Warn([string]$m) { Write-Host $m -ForegroundColor Yellow }

$envPath = ".\.env"
if (-not (Test-Path $envPath)) { throw ".env not found" }

$txt = Get-Content $envPath -Raw

if ($txt -match '(?m)^BOT_TOKEN=') {
  $txt = [regex]::Replace($txt, '(?m)^BOT_TOKEN=.*$', "BOT_TOKEN=$NewBotToken")
} else {
  $txt = $txt.TrimEnd() + "`nBOT_TOKEN=$NewBotToken`n"
}

if ($txt -match '(?m)^BOT_USERNAME=') {
  $txt = [regex]::Replace($txt, '(?m)^BOT_USERNAME=.*$', "BOT_USERNAME=$ExpectedBotUsername")
} else {
  $txt = $txt.TrimEnd() + "`nBOT_USERNAME=$ExpectedBotUsername`n"
}

$enc = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllText((Resolve-Path $envPath), ($txt -replace "`r`n","`n"), $enc)
Good "Updated .env BOT_TOKEN and BOT_USERNAME"

$envText = Get-Content $envPath -Raw
$botToken = ([regex]::Match($envText,'(?m)^BOT_TOKEN=(.+)$')).Groups[1].Value.Trim()
$botUsername = ([regex]::Match($envText,'(?m)^BOT_USERNAME=(.+)$')).Groups[1].Value.Trim()
$webhookUrl = ([regex]::Match($envText,'(?m)^WEBHOOK_URL=(.+)$')).Groups[1].Value.Trim()
$webhookSecret = ([regex]::Match($envText,'(?m)^WEBHOOK_SECRET=(.+)$')).Groups[1].Value.Trim()
$adminId = ([regex]::Match($envText,'(?m)^ADMIN_USER_ID=(.+)$')).Groups[1].Value.Trim()

if (-not $botToken) { throw "BOT_TOKEN missing after write" }
if (-not $botUsername) { throw "BOT_USERNAME missing after write" }
if (-not $webhookUrl) { throw "WEBHOOK_URL missing after write" }

Info "Stopping project python"
Get-Process python -ErrorAction SilentlyContinue |
  Where-Object { $_.Path -like "*SLH_PROJECT_V2*" } |
  Stop-Process -Force -ErrorAction SilentlyContinue

Start-Sleep -Seconds 1

Info "Starting webhook server"
Start-Process powershell.exe -ArgumentList @(
  '-NoExit',
  '-Command',
  '& { Set-Location ''D:\SLH_PROJECT_V2''; $global:ErrorActionPreference = ''Stop''; .\venv\Scripts\python.exe .\webhook_server.py }'
)

Start-Sleep -Seconds 3

Info "Checking local health"
$health = Invoke-RestMethod -Method Get -Uri "http://127.0.0.1:8080/healthz"
if (-not $health.ok) { throw "healthz not OK" }
Good "healthz OK"

Info "Starting worker"
Start-Process powershell.exe -ArgumentList @(
  '-NoExit',
  '-Command',
  '& { Set-Location ''D:\SLH_PROJECT_V2''; $global:ErrorActionPreference = ''Stop''; .\venv\Scripts\python.exe .\worker.py }'
)

Start-Sleep -Seconds 2

Info "Checking Telegram getMe"
$me = Invoke-RestMethod -Uri ("https://api.telegram.org/bot{0}/getMe" -f $botToken)
$apiUsername = $me.result.username
if ($apiUsername -ne $botUsername) {
  throw "BOT_USERNAME mismatch: env=$botUsername api=$apiUsername"
}
Good "getMe username match OK: $apiUsername"

Info "Refreshing webhook"
Invoke-RestMethod -Uri ("https://api.telegram.org/bot{0}/deleteWebhook?drop_pending_updates=true" -f $botToken) | Out-Null

$body = @{ url = $webhookUrl }
if ($webhookSecret) { $body["secret_token"] = $webhookSecret }

$setWh = Invoke-RestMethod -Method Post -Uri ("https://api.telegram.org/bot{0}/setWebhook" -f $botToken) -Body $body
if (-not $setWh.ok) { throw "setWebhook failed" }

$wh = Invoke-RestMethod -Uri ("https://api.telegram.org/bot{0}/getWebhookInfo" -f $botToken)
if ($wh.result.url -ne $webhookUrl) {
  throw "Webhook mismatch: env=$webhookUrl api=$($wh.result.url)"
}
Good "Webhook match OK"

if ($adminId) {
  Info "Sending smoke test message"
  $msg = Invoke-RestMethod -Method Post -Uri ("https://api.telegram.org/bot{0}/sendMessage" -f $botToken) -Body @{
    chat_id = $adminId
    text    = "SLH rotate_bot_token.ps1 smoke test OK"
  }
  if (-not $msg.ok) { throw "Smoke test sendMessage failed" }
  Good "Smoke test message sent"
}
else {
  Warn "ADMIN_USER_ID missing; skipped smoke test sendMessage"
}

Good "BOT TOKEN ROTATION COMPLETED SUCCESSFULLY"