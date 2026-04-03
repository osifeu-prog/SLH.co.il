param()

$ErrorActionPreference = "Continue"
Set-Location (Split-Path $PSScriptRoot -Parent)

$runtimeDir = Join-Path (Get-Location) "runtime"

function ReadPidFile($name) {
  $p = Join-Path $runtimeDir "$name.pid"
  if (Test-Path $p) {
    $pidValue = (Get-Content $p -Raw).Trim()
    if ($pidValue -match '^\d+$') {
      $proc = Get-Process -Id ([int]$pidValue) -ErrorAction SilentlyContinue
      return [pscustomobject]@{
        name = $name
        pid = [int]$pidValue
        alive = [bool]$proc
      }
    }
  }
  return [pscustomobject]@{
    name = $name
    pid = $null
    alive = $false
  }
}

$redisUp = $false
try {
  $pong = docker exec slh_redis redis-cli PING 2>$null
  if ($pong -match "PONG") { $redisUp = $true }
} catch {}

$localHealth = $false
try {
  $h = Invoke-RestMethod "http://127.0.0.1:8080/healthz" -TimeoutSec 5
  $localHealth = [bool]$h.ok
} catch {}

$status = @(
  ReadPidFile "worker"
  ReadPidFile "webhook"
  ReadPidFile "tunnel"
)

$status | Format-Table -AutoSize

[pscustomobject]@{
  redis_up = $redisUp
  local_healthz_ok = $localHealth
  stack_up = ($redisUp -and $localHealth)
} | Format-Table -AutoSize

try {
  $wh = & ".\ops\get-webhook-info.ps1" | ConvertFrom-Json
  [pscustomobject]@{
    telegram_webhook_registered = [bool]($wh.result.url)
    telegram_webhook_url = $wh.result.url
    telegram_pending_update_count = $wh.result.pending_update_count
  } | Format-Table -Wrap -AutoSize
} catch {
  Write-Host "telegram webhook info unavailable" -ForegroundColor Yellow
}