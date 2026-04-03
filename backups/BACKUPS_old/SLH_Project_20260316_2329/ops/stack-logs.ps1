param(
    [int]$Tail = 40
)
$ErrorActionPreference = "Stop"
. (Join-Path $PSScriptRoot "common.ps1")
Set-Location $ProjectRoot

Show-Section "RUNTIME WEBHOOK LOG"
if (Test-Path ".\logs\runtime_webhook.log") {
    Get-Content ".\logs\runtime_webhook.log" -Tail $Tail
} else {
    Write-Host "missing logs\runtime_webhook.log" -ForegroundColor Yellow
}

Show-Section "WORKER LOG"
if (Test-Path ".\logs\worker.log") {
    Get-Content ".\logs\worker.log" -Tail $Tail
} else {
    Write-Host "missing logs\worker.log" -ForegroundColor Yellow
}

Show-Section "TUNNEL CONSOLE LOG"
if (Test-Path ".\logs\tunnel.console.log") {
    Get-Content ".\logs\tunnel.console.log" -Tail $Tail
} else {
    Write-Host "missing logs\tunnel.console.log" -ForegroundColor Yellow
}