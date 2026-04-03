param(
  [string]$BaseUrl = "",
  [switch]$NoReset
)

$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)

$global:T0 = Get-Date

function StepTime([string]$name) {
  $dt = New-TimeSpan -Start $global:T0 -End (Get-Date)
  Write-Host ("[{0:mm\:ss}] {1}" -f $dt, $name) -ForegroundColor Cyan
}

function Section([string]$name) {
  Write-Host ""
  Write-Host ("=== " + $name + " ===") -ForegroundColor Magenta
}

function Show-Block([string[]]$lines) {
  Write-Host ""
  foreach ($line in $lines) {
    Write-Host $line -ForegroundColor Yellow
  }
  Write-Host ""
}

function Test-LocalHealth {
  try {
    $r = Invoke-RestMethod "http://127.0.0.1:8080/healthz" -TimeoutSec 5
    return [bool]$r.ok
  } catch {
    return $false
  }
}

function Test-BaseHealth([string]$Url) {
  try {
    $r = Invoke-RestMethod "$Url/healthz" -TimeoutSec 10
    return [bool]$r.ok
  } catch {
    return $false
  }
}

function Test-Port8080Listen {
  $listen = Get-NetTCPConnection -State Listen -LocalPort 8080 -ErrorAction SilentlyContinue
  return ($null -ne $listen)
}

function Show-QuickStatus {
  Section "QUICK STATUS"

  $redisUp = $false
  try {
    $pong = docker exec slh_redis redis-cli PING 2>$null
    if ($pong -match "PONG") { $redisUp = $true }
  } catch {}

  $localHealth = Test-LocalHealth
  $listen8080  = Test-Port8080Listen
  $cf          = Get-Process cloudflared -ErrorAction SilentlyContinue
  $py          = Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
    Where-Object {
      $_.Name -match '^python(\.exe)?$|^pythonw(\.exe)?$' -and
      ($_.CommandLine -like "*worker.py*" -or $_.CommandLine -like "*webhook_server.py*")
    }

  [pscustomobject]@{
    redis_up = $redisUp
    port_8080_listen = $listen8080
    local_healthz_ok = $localHealth
    cloudflared_running = [bool]$cf
    python_worker_or_webhook_count = @($py).Count
  } | Format-Table -AutoSize
}

function Show-WindowCommands {
  Section "WINDOW COMMANDS"

  Show-Block @(
    "WORKER window:",
    "cd D:\SLH_PROJECT_V2",
    '$ErrorActionPreference = "Stop"',
    '[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)',
    'chcp 65001 > $null',
    '$Host.UI.RawUI.WindowTitle = "SLH_WORKER"',
    '.\venv\Scripts\python.exe -u .\worker.py'
  )

  Show-Block @(
    "WEBHOOK window:",
    "cd D:\SLH_PROJECT_V2",
    '$ErrorActionPreference = "Stop"',
    '[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)',
    'chcp 65001 > $null',
    '$Host.UI.RawUI.WindowTitle = "SLH_WEBHOOK"',
    '.\venv\Scripts\python.exe -u .\webhook_server.py'
  )

  Show-Block @(
    "TUNNEL window:",
    "cd D:\SLH_PROJECT_V2",
    '$ErrorActionPreference = "Stop"',
    '$Host.UI.RawUI.WindowTitle = "SLH_TUNNEL"',
    'cloudflared tunnel --url http://127.0.0.1:8080'
  )
}

StepTime "ADMIN CONSOLE START"

Section "RULES"
Show-Block @(
  "CONTROL window = orchestration only",
  "Do not run worker.py in CONTROL",
  "Do not run webhook_server.py in CONTROL",
  "Keep exactly one WORKER window",
  "Keep exactly one WEBHOOK window",
  "Keep exactly one TUNNEL window",
  "Never use example.trycloudflare.com",
  "Only use the real URL shown by cloudflared"
)

if (-not $NoReset) {
  Section "RESET REDIS / LOGS / RUNTIME"
  StepTime "REDIS DOWN"
  docker compose -f .\docker-compose.redis.yml down | Out-Null

  StepTime "CLEAN LOGS AND RUNTIME"
  Remove-Item .\logs\*.log -Force -ErrorAction SilentlyContinue
  Remove-Item .\runtime\*.pid -Force -ErrorAction SilentlyContinue
  New-Item -ItemType Directory -Force -Path .\logs | Out-Null
  New-Item -ItemType Directory -Force -Path .\runtime | Out-Null

  StepTime "REDIS UP"
  docker compose -f .\docker-compose.redis.yml up -d
  Start-Sleep -Seconds 2
  docker exec slh_redis redis-cli PING
}

Show-QuickStatus
Show-WindowCommands

Section "STEP 1"
Show-Block @(
  "Open WORKER window and start worker.py",
  "Wait until you see: worker started"
)

Section "STEP 2"
Show-Block @(
  "Open WEBHOOK window and start webhook_server.py",
  "Wait until you see: Uvicorn running on http://127.0.0.1:8080"
)

Section "STEP 3"
StepTime "CHECK LOCAL HEALTH"
if (Test-LocalHealth) {
  Write-Host "LOCAL_HEALTH_OK" -ForegroundColor Green
  Invoke-RestMethod "http://127.0.0.1:8080/healthz" | Format-Table -AutoSize
} else {
  Write-Host "LOCAL_HEALTH_NOT_READY" -ForegroundColor Yellow
  Show-Block @(
    "When WEBHOOK is ready, run again:",
    '.\run-admin.bat',
    "or:",
    '.\ops\admin-console.ps1 -NoReset'
  )
  exit 0
}

Section "STEP 4"
Show-Block @(
  "Open TUNNEL window and run cloudflared",
  "Wait for two things in the TUNNEL window:",
  "1) a real https://...trycloudflare.com URL",
  "2) Registered tunnel connection"
)

if (-not $BaseUrl) {
  Show-Block @(
    "After you have the REAL URL, run this exact command in CONTROL:",
    '.\run-admin.bat -BaseUrl "https://REAL-URL.trycloudflare.com"'
  )
  StepTime "ADMIN CONSOLE WAITING FOR BASE URL"
  exit 0
}

Section "STEP 5"
StepTime "CHECK PROVIDED TUNNEL URL"
if (Test-BaseHealth $BaseUrl) {
  Write-Host "TUNNEL_HEALTH_OK" -ForegroundColor Green
  Invoke-RestMethod "$BaseUrl/healthz" | Format-Table -AutoSize
} else {
  Write-Host "TUNNEL_HEALTH_NOT_READY" -ForegroundColor Yellow
  Show-Block @(
    "Wait a bit longer and rerun:",
    '.\run-admin.bat -BaseUrl "' + $BaseUrl + '"'
  )
  exit 1
}

Section "STEP 6"
StepTime "SET WEBHOOK"
& ".\ops\set-webhook.ps1" -BaseUrl $BaseUrl

Section "STEP 7"
StepTime "GET WEBHOOK INFO"
& ".\ops\get-webhook-info.ps1"

Section "STEP 8"
Show-Block @(
  "Now test in Telegram:",
  "/start",
  "About",
  "Health"
)

Section "SUCCESS CRITERIA"
Show-Block @(
  "WEBHOOK window should show:",
  "POST /tg/webhook HTTP/1.1 200 OK",
  "ENQUEUED update ...",
  "",
  "WORKER window should show:",
  "HANDLER: /start ...",
  "HANDLER: About btn",
  "HANDLER: Health btn"
)

StepTime "ADMIN CONSOLE READY"