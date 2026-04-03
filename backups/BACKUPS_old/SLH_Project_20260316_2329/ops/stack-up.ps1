param(
    [switch]$WithTunnel
)
$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)

.\ops\doctor.ps1
if ($LASTEXITCODE -ne 0) { throw "doctor failed" }

.\ops\start-redis.ps1
Start-Sleep -Seconds 2
.\ops\start-worker.ps1
Start-Sleep -Seconds 2
.\ops\start-webhook.ps1
Start-Sleep -Seconds 3

if ($WithTunnel) {
    .\ops\start-tunnel.ps1
    Start-Sleep -Seconds 2
}

.\ops\stack-status.ps1