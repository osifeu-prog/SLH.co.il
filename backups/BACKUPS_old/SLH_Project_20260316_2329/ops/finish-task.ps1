param(
    [string]$Status = "done",
    [string]$Notes = ""
)

$ErrorActionPreference = "Stop"

$root = Split-Path $PSScriptRoot -Parent
if (-not $root) { $root = (Get-Location).Path }
Set-Location $root

$stateDir = Join-Path $root "state\tasks"
$currentTaskPath = Join-Path $stateDir "current_task.txt"
$logPath = Join-Path $stateDir "task_log.tsv"

if (-not (Test-Path $currentTaskPath)) {
    throw "No active task found."
}

$raw = Get-Content $currentTaskPath
$data = @{}
foreach ($line in $raw) {
    if ($line -match '=') {
        $k, $v = $line -split '=', 2
        $data[$k] = $v
    }
}

$taskId = $data["TASK_ID"]
$title = $data["TITLE"]
$startedAt = $data["STARTED"]
$minutes = $data["MINUTES"]
$endedAt = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")

$rows = Get-Content $logPath
$header = $rows[0]
$body = $rows | Select-Object -Skip 1

$newRows = New-Object System.Collections.Generic.List[string]
$newRows.Add($header)

foreach ($row in $body) {
    if ($row -like "$taskId`t*") {
        $newRows.Add("$taskId`t$startedAt`t$endedAt`t$minutes`t$Status`t$title`t$Notes")
    }
    else {
        $newRows.Add($row)
    }
}

$newRows | Out-File -FilePath $logPath -Encoding utf8
Remove-Item $currentTaskPath -Force

Write-Host ""
Write-Host "TASK FINISHED" -ForegroundColor Green
Write-Host "Id     : $taskId" -ForegroundColor Cyan
Write-Host "Title  : $title" -ForegroundColor Cyan
Write-Host "Status : $Status" -ForegroundColor Cyan
Write-Host "Notes  : $Notes" -ForegroundColor Cyan