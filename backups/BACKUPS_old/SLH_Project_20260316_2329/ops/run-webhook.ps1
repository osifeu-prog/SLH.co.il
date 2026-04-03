param()

$ErrorActionPreference = "Continue"
Set-Location (Split-Path $PSScriptRoot -Parent)

$root = (Get-Location).Path
$python = Join-Path $root "venv\Scripts\python.exe"
$runtimeDir = Join-Path $root "runtime"
$logsDir = Join-Path $root "logs"

New-Item -ItemType Directory -Force -Path $runtimeDir | Out-Null
New-Item -ItemType Directory -Force -Path $logsDir | Out-Null

$pidFile = Join-Path $runtimeDir "webhook_wrapper.pid"
$logFile = Join-Path $logsDir "webhook.console.log"

$Host.UI.RawUI.WindowTitle = "SLH_WEBHOOK"
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
chcp 65001 > $null

$PID | Set-Content -Path $pidFile -Encoding utf8

function Write-LogLine([string]$line) {
  Add-Content -Path $logFile -Value $line -Encoding utf8
  Write-Host $line
}

Write-LogLine "=== SLH_WEBHOOK_WRAPPER_STARTED ==="

try {
  $cmdLine = "`"$python`" -u .\webhook_server.py 2>&1"
  cmd /d /c $cmdLine | ForEach-Object {
    Write-LogLine ([string]$_)
  }
}
finally {
  if (Test-Path $pidFile) {
    Remove-Item $pidFile -Force -ErrorAction SilentlyContinue
  }
  Write-Host "=== SLH_WEBHOOK_WRAPPER_EXITED ==="
}