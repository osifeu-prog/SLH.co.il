param(
  [int]$Lines = 80
)

$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)

$files = @(
  ".\logs\worker.console.out.log",
  ".\logs\worker.console.err.log",
  ".\logs\webhook.console.out.log",
  ".\logs\webhook.console.err.log",
  ".\logs\tunnel.console.out.log",
  ".\logs\tunnel.console.err.log"
)

foreach ($f in $files) {
  Write-Host ""
  Write-Host ("=== " + $f + " ===") -ForegroundColor Cyan
  if (Test-Path $f) {
    Get-Content $f -Tail $Lines
  } else {
    Write-Host "missing" -ForegroundColor Yellow
  }
}