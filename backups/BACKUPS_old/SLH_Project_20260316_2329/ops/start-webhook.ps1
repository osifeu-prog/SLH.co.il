param()
$ErrorActionPreference = "Stop"
. (Join-Path $PSScriptRoot "common.ps1")
Set-Location $ProjectRoot

$python = Get-PythonExe
$log = Join-Path $LogsDir "webhook.console.log"
$cmd = "& '$python' -u '.\webhook_server.py'"
$pid = Start-BackgroundPowerShell "SLH Webhook" $cmd $log
Set-StateValue "webhook_pid" $pid
Write-Host "WEBHOOK_STARTED PID=$pid" -ForegroundColor Green