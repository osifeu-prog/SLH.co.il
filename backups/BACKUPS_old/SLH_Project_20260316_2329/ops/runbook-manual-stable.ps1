param(
  [string]$BaseUrl = ""
)

$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)

$global:T0 = Get-Date

function StepTime([string]$name) {
  $dt = New-TimeSpan -Start $global:T0 -End (Get-Date)
  Write-Host ("[{0:mm\:ss}] {1}" -f $dt, $name) -ForegroundColor Cyan
}

function Show-Block([string[]]$lines) {
  Write-Host ""
  foreach ($line in $lines) {
    Write-Host $line -ForegroundColor Yellow
  }
  Write-Host ""
}

StepTime "RUNBOOK START"

Show-Block @(
  "Stable manual sequence for SLH_PROJECT_V2",
  "1) Run this script in the CONTROL window",
  "2) Open exactly one WORKER window",
  "3) Open exactly one WEBHOOK window",
  "4) Open exactly one TUNNEL window",
  "5) Use the REAL trycloudflare URL only",
  "6) Verify: irm <BASE_URL>/healthz",
  "7) Then set webhook",
  "8) Then test in Telegram: /start, About, Health"
)

StepTime "STOP REDIS"
docker compose -f .\docker-compose.redis.yml down | Out-Null

StepTime "CLEAN LOGS AND RUNTIME"
Remove-Item .\logs\*.log -Force -ErrorAction SilentlyContinue
Remove-Item .\runtime\*.pid -Force -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Force -Path .\logs | Out-Null
New-Item -ItemType Directory -Force -Path .\runtime | Out-Null

StepTime "START REDIS"
docker compose -f .\docker-compose.redis.yml up -d
Start-Sleep -Seconds 2
docker exec slh_redis redis-cli PING

StepTime "NEXT ACTIONS"
Show-Block @(
  "Open WORKER window and run:",
  "cd D:\SLH_PROJECT_V2",
  '$ErrorActionPreference = "Stop"',
  '[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)',
  'chcp 65001 > $null',
  '$Host.UI.RawUI.WindowTitle = "SLH_WORKER"',
  '.\venv\Scripts\python.exe -u .\worker.py'
)

Show-Block @(
  "Open WEBHOOK window and run:",
  "cd D:\SLH_PROJECT_V2",
  '$ErrorActionPreference = "Stop"',
  '[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)',
  'chcp 65001 > $null',
  '$Host.UI.RawUI.WindowTitle = "SLH_WEBHOOK"',
  '.\venv\Scripts\python.exe -u .\webhook_server.py'
)

Show-Block @(
  "Back in CONTROL window, verify local health:",
  'irm http://127.0.0.1:8080/healthz'
)

Show-Block @(
  "Open TUNNEL window and run:",
  "cd D:\SLH_PROJECT_V2",
  '$ErrorActionPreference = "Stop"',
  '$Host.UI.RawUI.WindowTitle = "SLH_TUNNEL"',
  'cloudflared tunnel --url http://127.0.0.1:8080'
)

if ($BaseUrl) {
  StepTime "CHECK PROVIDED TUNNEL URL"
  irm "$BaseUrl/healthz"

  StepTime "SET WEBHOOK"
  & ".\ops\set-webhook.ps1" -BaseUrl $BaseUrl

  StepTime "GET WEBHOOK INFO"
  & ".\ops\get-webhook-info.ps1"

  Show-Block @(
    "Now test in Telegram:",
    "/start",
    "About",
    "Health"
  )
} else {
  Show-Block @(
    "After tunnel is registered, copy the REAL URL and run:",
    '.\ops\runbook-manual-stable.ps1 -BaseUrl "https://REAL-URL.trycloudflare.com"'
  )
}

StepTime "RUNBOOK READY"