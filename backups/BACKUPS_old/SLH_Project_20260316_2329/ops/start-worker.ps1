param()
$ErrorActionPreference = "Stop"
. (Join-Path $PSScriptRoot "common.ps1")
Set-Location $ProjectRoot

$python = Get-PythonExe
$log = Join-Path $LogsDir "worker.console.log"
$cmd = "& '$python' -u '.\worker.py'"
$pid = Start-BackgroundPowerShell "SLH Worker" $cmd $log
Set-StateValue "worker_pid" $pid
Write-Host "WORKER_STARTED PID=$pid" -ForegroundColor Green