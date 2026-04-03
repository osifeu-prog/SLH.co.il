param(
  [ValidateSet("worker","webhook","all")]
  [string]$Target = "all",

  [int]$Lines = 80
)

$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)

$workerLog  = Join-Path (Get-Location) "logs\worker.console.log"
$webhookLog = Join-Path (Get-Location) "logs\webhook.console.log"

function TailFile([string]$path, [string]$title, [int]$lines) {
  Write-Host ""
  Write-Host "=== $title ===" -ForegroundColor Cyan
  if (-not (Test-Path $path)) {
    Write-Host "File not found: $path" -ForegroundColor Yellow
    return
  }
  Get-Content $path -Tail $lines -Wait
}

switch ($Target) {
  "worker"  { TailFile $workerLog  "WORKER LOG"  $Lines }
  "webhook" { TailFile $webhookLog "WEBHOOK LOG" $Lines }
  "all" {
    Write-Host "Open two windows for real-time parallel tail if needed:" -ForegroundColor Yellow
    Write-Host ".\ops\tail-logs.ps1 -Target worker" -ForegroundColor Yellow
    Write-Host ".\ops\tail-logs.ps1 -Target webhook" -ForegroundColor Yellow

    Write-Host ""
    Write-Host "=== WORKER LOG (snapshot) ===" -ForegroundColor Cyan
    if (Test-Path $workerLog) { Get-Content $workerLog -Tail $Lines }
    else { Write-Host "File not found: $workerLog" -ForegroundColor Yellow }

    Write-Host ""
    Write-Host "=== WEBHOOK LOG (snapshot) ===" -ForegroundColor Cyan
    if (Test-Path $webhookLog) { Get-Content $webhookLog -Tail $Lines }
    else { Write-Host "File not found: $webhookLog" -ForegroundColor Yellow }
  }
}