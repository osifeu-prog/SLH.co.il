param()
$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)
& ".\ops\status-stack.ps1"
Write-Host ""
& ".\ops\status-core.ps1"