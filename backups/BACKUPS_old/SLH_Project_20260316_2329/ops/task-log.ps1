$ErrorActionPreference = "Stop"

$root = Split-Path $PSScriptRoot -Parent
if (-not $root) { $root = (Get-Location).Path }
Set-Location $root

$logPath = Join-Path $root "state\tasks\task_log.tsv"

if (-not (Test-Path $logPath)) {
    Write-Host "No task log yet." -ForegroundColor Yellow
    exit 0
}

Get-Content $logPath