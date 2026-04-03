param()

$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)

Write-Host "`n=== START CORE GUARDED ===" -ForegroundColor Cyan
& ".\ops\start-core.ps1"

Write-Host "`n=== POST-START ALERT CHECK ===" -ForegroundColor Cyan
& ".\ops\db-alert.ps1"