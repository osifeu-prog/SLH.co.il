param(
    [string]$Title = "SLH LIVE SESSION",
    [string]$SessionName = "work",
    [int]$RefreshSeconds = 1
)

$ErrorActionPreference = "Stop"

$root = Split-Path $PSScriptRoot -Parent
if (-not $root) { $root = (Get-Location).Path }
Set-Location $root

$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$sessionId = "$SessionName`_$stamp"
$stateDir = Join-Path $root "state\live_sessions"
New-Item -ItemType Directory -Force -Path $stateDir | Out-Null

$metaPath = Join-Path $stateDir "$sessionId.txt"
$beatPath = Join-Path $stateDir "$sessionId.heartbeat.txt"

$Host.UI.RawUI.WindowTitle = $Title
$started = Get-Date

@"
SESSION_ID=$sessionId
TITLE=$Title
STARTED=$($started.ToString("yyyy-MM-dd HH:mm:ss"))
ROOT=$root
"@ | Out-File -FilePath $metaPath -Encoding utf8

Write-Host ""
Write-Host "====================================" -ForegroundColor DarkCyan
Write-Host "         SLH LIVE SESSION           " -ForegroundColor Green
Write-Host "====================================" -ForegroundColor DarkCyan
Write-Host "Session: $sessionId" -ForegroundColor Cyan
Write-Host "Started: $($started.ToString("yyyy-MM-dd HH:mm:ss"))" -ForegroundColor DarkGray
Write-Host "Stop with Ctrl+C in this timer window." -ForegroundColor Yellow
Write-Host ""

try {
    while ($true) {
        $now = Get-Date
        $elapsed = $now - $started
        $hh = "{0:00}" -f [int]$elapsed.TotalHours
        $mm = "{0:00}" -f $elapsed.Minutes
        $ss = "{0:00}" -f $elapsed.Seconds

        $line = "[LIVE {0}] Elapsed: {1}:{2}:{3}" -f $now.ToString("HH:mm:ss"), $hh, $mm, $ss
        Write-Host ("`r" + $line + "   ") -NoNewline -ForegroundColor Yellow

        @"
SESSION_ID=$sessionId
NOW=$($now.ToString("yyyy-MM-dd HH:mm:ss"))
ELAPSED=$hh`:$mm`:$ss
"@ | Out-File -FilePath $beatPath -Encoding utf8

        Start-Sleep -Seconds $RefreshSeconds
    }
}
finally {
    Write-Host ""
    Write-Host ""
    Write-Host "SESSION STOPPED: $sessionId" -ForegroundColor Cyan
    Write-Host "Started : $($started.ToString("yyyy-MM-dd HH:mm:ss"))" -ForegroundColor DarkGray
    Write-Host "Stopped : $((Get-Date).ToString("yyyy-MM-dd HH:mm:ss"))" -ForegroundColor DarkGray
    Write-Host "Meta    : $metaPath" -ForegroundColor DarkGray
    Write-Host "Beat    : $beatPath" -ForegroundColor DarkGray
}
