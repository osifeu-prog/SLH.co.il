param()
$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)
& ".\ops\stop-stack.ps1"
Start-Sleep -Seconds 2
& ".\ops\start-stack.ps1"