param(
  [Parameter(Mandatory = $true)]
  [string]$SqlFile
)

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

.\ops\db-preflight.ps1 $SqlFile

Write-Host "=== RUN SQL ===" -ForegroundColor Cyan
psql -v ON_ERROR_STOP=1 --dbname="$env:DATABASE_URL" -f $SqlFile

Write-Host "=== SQL DONE ===" -ForegroundColor Green
Write-Host "Run verification queries next." -ForegroundColor Yellow