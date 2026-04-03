param(
  [switch]$DeleteWebhook
)

$ErrorActionPreference = "Continue"
Set-Location (Split-Path $PSScriptRoot -Parent)

$root = (Get-Location).Path
$runtimeDir = Join-Path $root "runtime"
$logsDir = Join-Path $root "logs"
New-Item -ItemType Directory -Force -Path $logsDir | Out-Null

$stopLog = Join-Path $logsDir "stop-stack.log"
$global:STOP_T0 = Get-Date

function Log([string]$msg) {
  $dt = New-TimeSpan -Start $global:STOP_T0 -End (Get-Date)
  $line = "[{0:mm\:ss}] {1}" -f $dt, $msg
  Add-Content -Path $stopLog -Value $line -Encoding utf8
  Write-Host $line
}

function Stop-PidFile([string]$name) {
  $pidFile = Join-Path $runtimeDir "$name.pid"
  if (Test-Path $pidFile) {
    $pidValue = (Get-Content $pidFile -Raw).Trim()
    if ($pidValue -match '^\d+$') {
      Stop-Process -Id ([int]$pidValue) -Force -ErrorAction SilentlyContinue
      Log "stop pidfile target: $name pid=$pidValue"
    } else {
      Log "bad pidfile format: $name"
    }
    Remove-Item $pidFile -Force -ErrorAction SilentlyContinue
  } else {
    Log "pidfile missing: $name"
  }
}

function Is-LocalHealthUp {
  try {
    $h = Invoke-RestMethod "http://127.0.0.1:8080/healthz" -TimeoutSec 3
    return [bool]$h.ok
  } catch {
    return $false
  }
}

"" | Set-Content -Path $stopLog -Encoding utf8
Log "STOP_STACK_BEGIN"

Stop-PidFile "worker"
Stop-PidFile "webhook"
Stop-PidFile "tunnel"

Get-Process cloudflared -ErrorAction SilentlyContinue |
  ForEach-Object {
    Stop-Process -Id $_.Id -Force -ErrorAction SilentlyContinue
    Log "stop cloudflared pid=$($_.Id)"
  }

Get-NetTCPConnection -LocalPort 8080 -ErrorAction SilentlyContinue |
  Select-Object -ExpandProperty OwningProcess -Unique |
  ForEach-Object {
    Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue
    Log "stop port8080 owner pid=$_"
  }

Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
  Where-Object {
    $_.Name -match '^python(\.exe)?$|^pythonw(\.exe)?$' -and
    ($_.CommandLine -like "*worker.py*" -or $_.CommandLine -like "*webhook_server.py*")
  } |
  ForEach-Object {
    Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
    Log "stop python target pid=$($_.ProcessId)"
  }

docker compose -f .\docker-compose.redis.yml down | Out-Null
Log "docker compose redis down"

if ($DeleteWebhook) {
  try {
    & ".\ops\clear-pending-updates.ps1" | Out-Null
    Log "telegram webhook deleted with drop_pending_updates=true"
  } catch {
    Log ("telegram webhook delete failed: " + $_.Exception.Message)
  }
}

Start-Sleep -Seconds 2

$cloudflaredAlive = [bool](Get-Process cloudflared -ErrorAction SilentlyContinue)
$listen8080 = [bool](Get-NetTCPConnection -State Listen -LocalPort 8080 -ErrorAction SilentlyContinue)
$localHealth = Is-LocalHealthUp

$redisUp = $false
try {
  $pong = docker exec slh_redis redis-cli PING 2>$null
  if ($pong -match "PONG") { $redisUp = $true }
} catch {}

Log ("verify cloudflared_running=" + $cloudflaredAlive)
Log ("verify port_8080_listen=" + $listen8080)
Log ("verify local_healthz_ok=" + $localHealth)
Log ("verify redis_up=" + $redisUp)
Log "STOP_STACK_END"

Write-Host "STACK_STOP_OK" -ForegroundColor Green
Write-Host ("Stop log: " + $stopLog) -ForegroundColor Yellow