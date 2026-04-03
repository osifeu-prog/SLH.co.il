param()

$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)

$root = (Get-Location).Path
$venvPython = Join-Path $root "venv\Scripts\python.exe"
if (-not (Test-Path $venvPython)) { throw "venv python not found: $venvPython" }

$logsDir = Join-Path $root "logs"
$runtimeDir = Join-Path $root "runtime"
New-Item -ItemType Directory -Force -Path $logsDir | Out-Null
New-Item -ItemType Directory -Force -Path $runtimeDir | Out-Null

$workerOut = Join-Path $logsDir "worker.console.out.log"
$workerErr = Join-Path $logsDir "worker.console.err.log"
$webhookOut = Join-Path $logsDir "webhook.console.out.log"
$webhookErr = Join-Path $logsDir "webhook.console.err.log"
$tunnelOut = Join-Path $logsDir "tunnel.console.out.log"
$tunnelErr = Join-Path $logsDir "tunnel.console.err.log"

$workerPidFile = Join-Path $runtimeDir "worker.pid"
$webhookPidFile = Join-Path $runtimeDir "webhook.pid"
$tunnelPidFile = Join-Path $runtimeDir "tunnel.pid"

function Save-PidFile([string]$PathValue, [int]$ProcIdValue) {
  Set-Content -Path $PathValue -Value $ProcIdValue -Encoding utf8
}

Write-Host "`n=== STOP OLD STACK ===" -ForegroundColor Cyan
& ".\ops\stop-stack.ps1"

Write-Host "`n=== RESET LOGS ===" -ForegroundColor Cyan
Remove-Item $workerOut,$workerErr,$webhookOut,$webhookErr,$tunnelOut,$tunnelErr -Force -ErrorAction SilentlyContinue

Write-Host "`n=== START REDIS ===" -ForegroundColor Cyan
docker compose -f .\docker-compose.redis.yml up -d
Start-Sleep -Seconds 2
docker exec slh_redis redis-cli PING

Write-Host "`n=== START WORKER (background) ===" -ForegroundColor Cyan
$workerProc = Start-Process -FilePath $venvPython `
  -ArgumentList "-u",".\worker.py" `
  -WorkingDirectory $root `
  -RedirectStandardOutput $workerOut `
  -RedirectStandardError $workerErr `
  -WindowStyle Hidden `
  -PassThru
Save-PidFile -PathValue $workerPidFile -ProcIdValue $workerProc.Id

Start-Sleep -Seconds 2

Write-Host "`n=== START WEBHOOK (background) ===" -ForegroundColor Cyan
$webhookProc = Start-Process -FilePath $venvPython `
  -ArgumentList "-u",".\webhook_server.py" `
  -WorkingDirectory $root `
  -RedirectStandardOutput $webhookOut `
  -RedirectStandardError $webhookErr `
  -WindowStyle Hidden `
  -PassThru
Save-PidFile -PathValue $webhookPidFile -ProcIdValue $webhookProc.Id

Write-Host "`n=== WAIT LOCAL HEALTH ===" -ForegroundColor Cyan
$localOk = $false
for ($n = 0; $n -lt 20; $n++) {
  Start-Sleep -Seconds 1
  try {
    $h = Invoke-RestMethod "http://127.0.0.1:8080/healthz" -TimeoutSec 3
    if ($h.ok -eq $true) {
      $localOk = $true
      break
    }
  } catch {}
}
if (-not $localOk) {
  Write-Host "`nWEBHOOK STDERR:" -ForegroundColor Yellow
  if (Test-Path $webhookErr) { Get-Content $webhookErr -Tail 80 }
  throw "webhook local health did not become ready"
}

Write-Host "`n=== START TUNNEL (background) ===" -ForegroundColor Cyan
$tunnelProc = Start-Process -FilePath "cloudflared.exe" `
  -ArgumentList "tunnel","--url","http://127.0.0.1:8080" `
  -WorkingDirectory $root `
  -RedirectStandardOutput $tunnelOut `
  -RedirectStandardError $tunnelErr `
  -WindowStyle Hidden `
  -PassThru
Save-PidFile -PathValue $tunnelPidFile -ProcIdValue $tunnelProc.Id

Write-Host "`n=== WAIT TUNNEL URL + REGISTERED ===" -ForegroundColor Cyan
$baseUrl = $null
$registered = $false

for ($n = 0; $n -lt 90; $n++) {
  Start-Sleep -Seconds 1

  $txtOut = ""
  $txtErr = ""

  if (Test-Path $tunnelOut) {
    $tmpOut = Get-Content $tunnelOut -Raw -ErrorAction SilentlyContinue
    if ($null -ne $tmpOut) { $txtOut = [string]$tmpOut }
  }

  if (Test-Path $tunnelErr) {
    $tmpErr = Get-Content $tunnelErr -Raw -ErrorAction SilentlyContinue
    if ($null -ne $tmpErr) { $txtErr = [string]$tmpErr }
  }

  $txt = $txtOut + "`n" + $txtErr

  if (-not [string]::IsNullOrWhiteSpace($txt)) {
    if (-not $baseUrl) {
      $m = [regex]::Match($txt, 'https://[-a-z0-9]+\.trycloudflare\.com')
      if ($m.Success) { $baseUrl = $m.Value }
    }

    if ($txt -match 'Registered tunnel connection') {
      $registered = $true
      if ($baseUrl) { break }
    }
  }
}

if (-not $baseUrl) {
  Write-Host "`nTUNNEL STDOUT:" -ForegroundColor Yellow
  if (Test-Path $tunnelOut) { Get-Content $tunnelOut -Tail 120 }
  Write-Host "`nTUNNEL STDERR:" -ForegroundColor Yellow
  if (Test-Path $tunnelErr) { Get-Content $tunnelErr -Tail 120 }
  throw "Tunnel URL not found in tunnel logs"
}

if (-not $registered) {
  Write-Host "`nTUNNEL STDOUT:" -ForegroundColor Yellow
  if (Test-Path $tunnelOut) { Get-Content $tunnelOut -Tail 120 }
  Write-Host "`nTUNNEL STDERR:" -ForegroundColor Yellow
  if (Test-Path $tunnelErr) { Get-Content $tunnelErr -Tail 120 }
  throw "Tunnel did not reach registered state in time"
}

Write-Host "BASE_URL = $baseUrl" -ForegroundColor Green

Write-Host "`n=== WAIT PUBLIC HEALTH ===" -ForegroundColor Cyan
$publicOk = $false
for ($n = 0; $n -lt 24; $n++) {
  Start-Sleep -Seconds 5
  try {
    $h2 = Invoke-RestMethod "$baseUrl/healthz" -TimeoutSec 10
    if ($h2.ok -eq $true) {
      $publicOk = $true
      break
    }
  } catch {}
}
if (-not $publicOk) { throw "Tunnel public health did not become ready: $baseUrl" }

Write-Host "`n=== SET WEBHOOK ===" -ForegroundColor Cyan
& ".\ops\set-webhook.ps1" -BaseUrl $baseUrl

Write-Host "`n=== WEBHOOK INFO ===" -ForegroundColor Cyan
& ".\ops\get-webhook-info.ps1"

Write-Host "`nSTACK_START_OK" -ForegroundColor Green
Write-Host "Use second console for live logs:" -ForegroundColor Yellow
Write-Host ".\ops\tail-stack.ps1" -ForegroundColor Yellow