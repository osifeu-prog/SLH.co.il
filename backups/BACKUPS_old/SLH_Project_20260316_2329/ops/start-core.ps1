param()

$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)

$root = (Get-Location).Path
$runtimeDir = Join-Path $root "runtime"
$logsDir = Join-Path $root "logs"

New-Item -ItemType Directory -Force -Path $runtimeDir | Out-Null
New-Item -ItemType Directory -Force -Path $logsDir | Out-Null

$workerLog  = Join-Path $logsDir "worker.console.log"
$webhookLog = Join-Path $logsDir "webhook.console.log"

Write-Host "`n=== STOP OLD PROCESSES ===" -ForegroundColor Cyan
& ".\ops\stop-core.ps1"

Start-Sleep -Seconds 2

Write-Host "`n=== START REDIS ===" -ForegroundColor Cyan
docker compose -f .\docker-compose.redis.yml up -d
Start-Sleep -Seconds 2
docker exec slh_redis redis-cli PING

Write-Host "`n=== RESET LOG FILES ===" -ForegroundColor Cyan
if (Test-Path $workerLog)  { Remove-Item $workerLog  -Force }
if (Test-Path $webhookLog) { Remove-Item $webhookLog -Force }

Write-Host "`n=== START WORKER WINDOW ===" -ForegroundColor Cyan
Start-Process powershell.exe -ArgumentList @(
  "-NoExit",
  "-ExecutionPolicy","Bypass",
  "-File",".\ops\run-worker.ps1"
) | Out-Null

$workerReady = $false
for ($i = 0; $i -lt 20; $i++) {
  Start-Sleep -Seconds 1
  if (Test-Path $workerLog) {
    $txt = Get-Content $workerLog -Raw -ErrorAction SilentlyContinue
    if ($txt -match "worker started") {
      $workerReady = $true
      break
    }
  }
}

if (-not $workerReady) {
  Write-Host "WARNING: worker readiness text not detected yet." -ForegroundColor Yellow
}

Write-Host "`n=== START WEBHOOK WINDOW ===" -ForegroundColor Cyan
Start-Process powershell.exe -ArgumentList @(
  "-NoExit",
  "-ExecutionPolicy","Bypass",
  "-File",".\ops\run-webhook.ps1"
) | Out-Null

$webhookReady = $false
for ($i = 0; $i -lt 20; $i++) {
  Start-Sleep -Seconds 1
  try {
    $h = Invoke-RestMethod "http://127.0.0.1:8080/healthz" -TimeoutSec 3
    if ($h.ok -eq $true) {
      $webhookReady = $true
      break
    }
  } catch {}
}

if (-not $webhookReady) {
  throw "webhook did not become ready on 127.0.0.1:8080"
}

Write-Host "`n=== HEALTH ===" -ForegroundColor Cyan
Invoke-RestMethod "http://127.0.0.1:8080/healthz" | Format-Table -AutoSize

Write-Host ""
Write-Host "CORE_START_OK" -ForegroundColor Green
Write-Host "Next manual step: run cloudflared tunnel --url http://127.0.0.1:8080" -ForegroundColor Yellow