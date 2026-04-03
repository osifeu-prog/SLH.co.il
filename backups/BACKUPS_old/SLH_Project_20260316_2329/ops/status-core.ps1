param()
$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)

$root = (Get-Location).Path
$runtimeDir = Join-Path $root "runtime"

function Read-PidFile([string]$name) {
  $filePath = Join-Path $runtimeDir "$name.pid"
  if (Test-Path $filePath) {
    $raw = (Get-Content $filePath -Raw -ErrorAction SilentlyContinue).Trim()
    if ($raw -match '^\d+$') { return [int]$raw }
  }
  return $null
}

function Get-AliveProcess([int]$procId) {
  if (-not $procId) { return $null }
  return Get-Process -Id $procId -ErrorAction SilentlyContinue
}

Write-Host "`n=== PROJECT ===" -ForegroundColor Cyan
Write-Host "Root: $root"

Write-Host "`n=== STACK PID FILES ===" -ForegroundColor Cyan
$workerProcId = Read-PidFile "worker"
$webhookProcId = Read-PidFile "webhook"
$tunnelProcId = Read-PidFile "tunnel"

[pscustomobject]@{
  worker_pid    = $workerProcId
  worker_alive  = [bool](Get-AliveProcess $workerProcId)
  webhook_pid   = $webhookProcId
  webhook_alive = [bool](Get-AliveProcess $webhookProcId)
  tunnel_pid    = $tunnelProcId
  tunnel_alive  = [bool](Get-AliveProcess $tunnelProcId)
} | Format-List

Write-Host "`n=== PROJECT PYTHON PROCESSES ===" -ForegroundColor Cyan
Get-CimInstance Win32_Process |
  Where-Object {
    $_.Name -match '^python(\.exe)?$' -and
    $_.CommandLine -match 'SLH_PROJECT_V2' -and
    (
      $_.CommandLine -match 'worker\.py' -or
      $_.CommandLine -match 'webhook_server\.py'
    )
  } |
  Select-Object ProcessId, ParentProcessId, Name, ExecutablePath, CommandLine |
  Sort-Object ProcessId | Format-Table -AutoSize

Write-Host "`n=== PORT 8080 LISTEN ===" -ForegroundColor Cyan
Get-NetTCPConnection -LocalPort 8080 -State Listen -ErrorAction SilentlyContinue |
  Select-Object LocalAddress, LocalPort, State, OwningProcess |
  Format-Table -AutoSize

Write-Host "`n=== HEALTHZ ===" -ForegroundColor Cyan
try {
  $r = Invoke-RestMethod "http://127.0.0.1:8080/healthz" -TimeoutSec 5
  $r | Format-List
} catch {
  Write-Host ("Healthz unavailable: " + $_.Exception.Message) -ForegroundColor Yellow
}

Write-Host "`n=== REDIS CONTAINER ===" -ForegroundColor Cyan
try {
  docker ps --filter "name=slh_redis"
} catch {
  Write-Host ("docker ps failed: " + $_.Exception.Message) -ForegroundColor Yellow
}

Write-Host "`n=== REDIS PING ===" -ForegroundColor Cyan
try {
  docker exec slh_redis redis-cli PING
} catch {
  Write-Host ("Redis ping failed: " + $_.Exception.Message) -ForegroundColor Yellow
}

Write-Host "`n=== CLOUDFLARED ===" -ForegroundColor Cyan
Get-Process cloudflared -ErrorAction SilentlyContinue |
  Select-Object Id, ProcessName, StartTime |
  Format-Table -AutoSize

Write-Host "`n=== WEBHOOK INFO ===" -ForegroundColor Cyan
try {
  & ".\ops\get-webhook-info.ps1"
} catch {
  Write-Host ("Webhook info failed: " + $_.Exception.Message) -ForegroundColor Yellow
}

Write-Host "`nSTATUS_CORE_DONE" -ForegroundColor Green