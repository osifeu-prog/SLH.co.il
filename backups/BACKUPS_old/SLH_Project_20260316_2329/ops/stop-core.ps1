param()

$ErrorActionPreference = "Continue"
Set-Location (Split-Path $PSScriptRoot -Parent)

$runtimeDir = Join-Path (Get-Location) "runtime"
$workerPidFile  = Join-Path $runtimeDir "worker_wrapper.pid"
$webhookPidFile = Join-Path $runtimeDir "webhook_wrapper.pid"

foreach ($pidFile in @($workerPidFile, $webhookPidFile)) {
  if (Test-Path $pidFile) {
    $pidValue = (Get-Content $pidFile -Raw).Trim()
    if ($pidValue -match '^\d+$') {
      Stop-Process -Id ([int]$pidValue) -Force -ErrorAction SilentlyContinue
    }
    Remove-Item $pidFile -Force -ErrorAction SilentlyContinue
  }
}

Get-CimInstance Win32_Process |
  Where-Object {
    $_.Name -match '^powershell(\.exe)?$|^pwsh(\.exe)?$|^python(\.exe)?$|^pythonw(\.exe)?$' -and
    (
      $_.CommandLine -like "*SLH_PROJECT_V2*" -or
      $_.CommandLine -like "*worker.py*" -or
      $_.CommandLine -like "*webhook_server.py*"
    )
  } |
  ForEach-Object {
    Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
  }

Get-Process cloudflared -ErrorAction SilentlyContinue |
  Stop-Process -Force -ErrorAction SilentlyContinue

Get-NetTCPConnection -LocalPort 8080 -ErrorAction SilentlyContinue |
  Select-Object -ExpandProperty OwningProcess -Unique |
  ForEach-Object { Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue }

docker compose -f .\docker-compose.redis.yml down | Out-Null

Write-Host "CORE_STOP_OK" -ForegroundColor Green