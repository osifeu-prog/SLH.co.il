$ErrorActionPreference = "Stop"

$root = Split-Path $PSScriptRoot -Parent
if (-not $root) { $root = (Get-Location).Path }
Set-Location $root

$currentTaskPath = Join-Path $root "state\tasks\current_task.txt"

if (-not (Test-Path $currentTaskPath)) {
    Write-Host "No active task." -ForegroundColor Yellow
    exit 0
}

Get-Content $currentTaskPath