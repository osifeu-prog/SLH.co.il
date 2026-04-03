param(
    [Parameter(Mandatory = $true)]
    [string]$Title,

    [int]$Minutes = 25
)

$ErrorActionPreference = "Stop"

$root = Split-Path $PSScriptRoot -Parent
if (-not $root) { $root = (Get-Location).Path }
Set-Location $root

$stateDir = Join-Path $root "state\tasks"
New-Item -ItemType Directory -Force -Path $stateDir | Out-Null

$taskId = "task_" + (Get-Date -Format "yyyyMMdd_HHmmss")
$started = Get-Date
$currentTaskPath = Join-Path $stateDir "current_task.txt"
$logPath = Join-Path $stateDir "task_log.tsv"

if (-not (Test-Path $logPath)) {
    "task_id`tstarted_at`tended_at`tminutes`tstatus`ttitle`tnotes" | Out-File -FilePath $logPath -Encoding utf8
}

@"
TASK_ID=$taskId
TITLE=$Title
STARTED=$($started.ToString("yyyy-MM-dd HH:mm:ss"))
MINUTES=$Minutes
STATUS=active
"@ | Out-File -FilePath $currentTaskPath -Encoding utf8

"$taskId`t$($started.ToString("yyyy-MM-dd HH:mm:ss"))``t$Minutes`tactive`t$Title`t" | Add-Content -Path $logPath -Encoding utf8

Write-Host ""
Write-Host "TASK STARTED" -ForegroundColor Green
Write-Host "Id     : $taskId" -ForegroundColor Cyan
Write-Host "Title  : $Title" -ForegroundColor Cyan
Write-Host "Length : $Minutes min" -ForegroundColor Cyan

Start-Process powershell.exe `
    -WorkingDirectory $root `
    -ArgumentList "-NoExit -ExecutionPolicy Bypass -File `"$root\ops\task-countdown.ps1`" -TaskTitle `"$Title`" -Minutes $Minutes -TaskId `"$taskId`""