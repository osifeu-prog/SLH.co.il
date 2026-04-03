param(
    [Parameter(Mandatory = $true)]
    [string]$TaskTitle,

    [int]$Minutes = 25,

    [string]$TaskId = "",

    [int]$RefreshSeconds = 1
)

$ErrorActionPreference = "Stop"

$root = Split-Path $PSScriptRoot -Parent
if (-not $root) { $root = (Get-Location).Path }
Set-Location $root

$stateDir = Join-Path $root "state\tasks"
New-Item -ItemType Directory -Force -Path $stateDir | Out-Null

if ([string]::IsNullOrWhiteSpace($TaskId)) {
    $TaskId = "task_" + (Get-Date -Format "yyyyMMdd_HHmmss")
}

$beatPath = Join-Path $stateDir "$TaskId.heartbeat.txt"
$metaPath = Join-Path $stateDir "$TaskId.txt"

$Host.UI.RawUI.WindowTitle = "TASK TIMER :: $TaskTitle"
$started = Get-Date
$end = $started.AddMinutes($Minutes)

@"
TASK_ID=$TaskId
TITLE=$TaskTitle
STARTED=$($started.ToString("yyyy-MM-dd HH:mm:ss"))
ENDS=$($end.ToString("yyyy-MM-dd HH:mm:ss"))
MINUTES=$Minutes
"@ | Out-File -FilePath $metaPath -Encoding utf8

Write-Host ""
Write-Host "====================================" -ForegroundColor DarkCyan
Write-Host "          SLH TASK TIMER            " -ForegroundColor Green
Write-Host "====================================" -ForegroundColor DarkCyan
Write-Host "Task   : $TaskTitle" -ForegroundColor Cyan
Write-Host "TaskId : $TaskId" -ForegroundColor DarkGray
Write-Host "Length : $Minutes min" -ForegroundColor DarkGray
Write-Host ""

while ((Get-Date) -lt $end) {
    $now = Get-Date
    $remaining = $end - $now
    $mm = "{0:00}" -f [int]$remaining.TotalMinutes
    $ss = "{0:00}" -f $remaining.Seconds
    $line = "[TASK {0}] Remaining: {1}:{2} :: {3}" -f $now.ToString("HH:mm:ss"), $mm, $ss, $TaskTitle
    Write-Host ("`r" + $line + "   ") -NoNewline -ForegroundColor Yellow

    @"
TASK_ID=$TaskId
TITLE=$TaskTitle
NOW=$($now.ToString("yyyy-MM-dd HH:mm:ss"))
REMAINING=$mm`:$ss
"@ | Out-File -FilePath $beatPath -Encoding utf8

    Start-Sleep -Seconds $RefreshSeconds
}

Write-Host ""
Write-Host ""
Write-Host "TASK TIMER COMPLETE: $TaskTitle" -ForegroundColor Cyan
[console]::beep(1200,300)
[console]::beep(1400,300)
