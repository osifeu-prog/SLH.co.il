param(
  [string]$SqlFile = ""
)

$ErrorActionPreference = "Stop"

function Fail([string]$Message) {
  Write-Host "ERROR: $Message" -ForegroundColor Red
  exit 1
}

Write-Host "=== DB PREFLIGHT ===" -ForegroundColor Cyan

if (-not (Get-Command psql -ErrorAction SilentlyContinue)) {
  Fail "psql not found in PATH."
}

if ([string]::IsNullOrWhiteSpace($env:DATABASE_URL)) {
  Fail "DATABASE_URL is missing in current shell."
}

if ([string]::IsNullOrWhiteSpace($env:PGCLIENTENCODING)) {
  $env:PGCLIENTENCODING = "UTF8"
}

if ($env:PGCLIENTENCODING -ne "UTF8") {
  Fail "PGCLIENTENCODING must be UTF8."
}

if (-not [string]::IsNullOrWhiteSpace($SqlFile)) {
  if (-not (Test-Path $SqlFile)) {
    Fail "SQL file not found: $SqlFile"
  }
}

Write-Host "OK  psql found" -ForegroundColor Green
Write-Host "OK  DATABASE_URL present" -ForegroundColor Green
Write-Host "OK  PGCLIENTENCODING=$env:PGCLIENTENCODING" -ForegroundColor Green

if (-not [string]::IsNullOrWhiteSpace($SqlFile)) {
  Write-Host "OK  SQL file exists: $SqlFile" -ForegroundColor Green
}

Write-Host "DB preflight passed." -ForegroundColor Green