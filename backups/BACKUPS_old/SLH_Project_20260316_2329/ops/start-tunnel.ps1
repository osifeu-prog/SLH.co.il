param()

$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)

$runtimeDir = Join-Path (Get-Location) "runtime"
$logsDir    = Join-Path (Get-Location) "logs"
$pidFile    = Join-Path $runtimeDir "tunnel_wrapper.pid"
$logFile    = Join-Path $logsDir "tunnel.console.log"

New-Item -ItemType Directory -Force -Path $runtimeDir | Out-Null
New-Item -ItemType Directory -Force -Path $logsDir | Out-Null

if (Test-Path $pidFile) {
  $oldPid = (Get-Content $pidFile -Raw).Trim()
  if ($oldPid -match '^\d+$') {
    Stop-Process -Id ([int]$oldPid) -Force -ErrorAction SilentlyContinue
  }
  Remove-Item $pidFile -Force -ErrorAction SilentlyContinue
}

Get-Process cloudflared -ErrorAction SilentlyContinue |
  Stop-Process -Force -ErrorAction SilentlyContinue

if (Test-Path $logFile) {
  Remove-Item $logFile -Force
}

Write-Host "`n=== START TUNNEL WINDOW ===" -ForegroundColor Cyan
Start-Process powershell.exe -ArgumentList @(
  "-NoExit",
  "-ExecutionPolicy","Bypass",
  "-File",".\ops\run-tunnel.ps1"
) | Out-Null

$tunnelUrl = $null
$registered = $false

for ($i = 0; $i -lt 90; $i++) {
  Start-Sleep -Seconds 1

  if (-not (Test-Path $logFile)) {
    continue
  }

  $txt = Get-Content $logFile -Raw -ErrorAction SilentlyContinue

  if (-not $tunnelUrl) {
    $m = [regex]::Match($txt, 'https://[-a-z0-9]+\.trycloudflare\.com')
    if ($m.Success) {
      $tunnelUrl = $m.Value
    }
  }

  if ($txt -match 'Registered tunnel connection') {
    $registered = $true
    break
  }
}

if (-not $tunnelUrl) {
  throw "Tunnel URL not detected in tunnel log"
}

Write-Host ""
Write-Host "TUNNEL_URL: $tunnelUrl" -ForegroundColor Green

if (-not $registered) {
  throw "Tunnel URL found, but tunnel did not reach registered state in time"
}

Write-Host "TUNNEL_REGISTERED: YES" -ForegroundColor Green