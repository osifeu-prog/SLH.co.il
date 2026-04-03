param()

$ErrorActionPreference = "Continue"
Set-Location (Split-Path $PSScriptRoot -Parent)

$root = (Get-Location).Path
$runtimeDir = Join-Path $root "runtime"
$logsDir = Join-Path $root "logs"

New-Item -ItemType Directory -Force -Path $runtimeDir | Out-Null
New-Item -ItemType Directory -Force -Path $logsDir | Out-Null

$pidFile = Join-Path $runtimeDir "tunnel_wrapper.pid"
$logFile = Join-Path $logsDir "tunnel.console.log"

$Host.UI.RawUI.WindowTitle = "SLH_TUNNEL"
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
chcp 65001 > $null

$PID | Set-Content -Path $pidFile -Encoding utf8

function Write-LogLine([string]$line) {
  Add-Content -Path $logFile -Value $line -Encoding utf8
  Write-Host $line
}

Write-LogLine "=== SLH_TUNNEL_WRAPPER_STARTED ==="

try {
  cmd /d /c "cloudflared tunnel --url http://127.0.0.1:8080 2>&1" | ForEach-Object {
    Write-LogLine ([string]$_)
  }
}
finally {
  if (Test-Path $pidFile) {
    Remove-Item $pidFile -Force -ErrorAction SilentlyContinue
  }
  Write-Host "=== SLH_TUNNEL_WRAPPER_EXITED ==="
}