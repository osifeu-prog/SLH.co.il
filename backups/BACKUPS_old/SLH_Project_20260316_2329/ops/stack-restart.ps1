param(
    [switch]$WithTunnel
)
$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)

.\ops\stack-down.ps1
Start-Sleep -Seconds 2
.\ops\stack-up.ps1 @PSBoundParameters