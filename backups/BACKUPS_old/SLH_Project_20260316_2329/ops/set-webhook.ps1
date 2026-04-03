param(
    [Parameter(Mandatory=$true)]
    [string]$BaseUrl
)

$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)

$envMap = @{}
Get-Content .\.env | ForEach-Object {
    if ($_ -match '^\s*#' -or $_ -match '^\s*$') { return }
    if ($_ -match '^\s*([^=]+?)\s*=\s*(.*)\s*$') {
        $envMap[$matches[1]] = $matches[2]
    }
}

$BOT_TOKEN = $envMap["BOT_TOKEN"]
$WEBHOOK_SECRET = $envMap["WEBHOOK_SECRET"]

if (-not $BOT_TOKEN) { throw "BOT_TOKEN missing in .env" }
if (-not $WEBHOOK_SECRET) { throw "WEBHOOK_SECRET missing in .env" }

$BaseUrl = $BaseUrl.Trim().TrimEnd("/")
$WebhookUrl = "$BaseUrl/tg/webhook"

Write-Host "Setting webhook to: $WebhookUrl" -ForegroundColor Cyan

$r = Invoke-RestMethod "https://api.telegram.org/bot$BOT_TOKEN/setWebhook" `
  -Method Post `
  -ContentType "application/json" `
  -Body (@{
    url = $WebhookUrl
    secret_token = $WEBHOOK_SECRET
    allowed_updates = @("message","callback_query")
    drop_pending_updates = $false
  } | ConvertTo-Json)

$r | Format-List

if ($r.ok -ne $true) {
    throw "setWebhook failed"
}

Write-Host "SET_WEBHOOK_OK" -ForegroundColor Green