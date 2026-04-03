param(
  [string]$SessionStatus = "completed",
  [string]$SessionNotes = "day closed cleanly",
  [switch]$SkipSessionEnd
)

$ErrorActionPreference = "Stop"
$ROOT = "D:\SLH_PROJECT_V2"
Set-Location $ROOT

function Good([string]$m) { Write-Host $m -ForegroundColor Green }
function Warn([string]$m) { Write-Host $m -ForegroundColor Yellow }

function Section([string]$t) {
  Write-Host ""
  Write-Host "=== $t ===" -ForegroundColor Magenta
}

Section "SAFE STOP AND CLOSE DAY"

if (-not $SkipSessionEnd) {
  Section "1) CLOSE ACTIVE SESSION"
  if (Test-Path ".\runtime\current_session.json") {
    & ".\ops\session-end.ps1" -Status $SessionStatus -Notes $SessionNotes
    Good "Session closed"
  } else {
    Warn "No active session file found"
  }
} else {
  Warn "SkipSessionEnd enabled"
}

Section "2) GIT STATUS"
try {
  git status --short
} catch {
  Warn "git status failed"
}

Section "3) SAFE STOP"
& ".\ops\stop-stable.ps1"

Section "4) VERIFY PYTHON STOPPED"
$projectPy = Get-Process python -ErrorAction SilentlyContinue |
  Where-Object { $_.Path -like "*SLH_PROJECT_V2*" } |
  Select-Object Id, ProcessName, Path, StartTime

if ($projectPy) {
  Warn "Project python still running"
  $projectPy | Format-Table -AutoSize
} else {
  Good "No project python processes"
}

Section "5) VERIFY PORT 8080 CLOSED"
try {
  $p8080 = Get-NetTCPConnection -LocalPort 8080 -ErrorAction Stop
  Warn "Port 8080 still open"
  $p8080 | Select-Object LocalAddress, LocalPort, State, OwningProcess | Format-Table -AutoSize
} catch {
  Good "Port 8080 is closed"
}

Section "6) VERIFY NO ACTIVE SESSION"
if (Test-Path ".\runtime\current_session.json") {
  Warn "current_session.json still exists"
  Get-Content ".\runtime\current_session.json"
} else {
  Good "No active session file"
}

Section "DONE"
Good "SAFE CLOSE DAY COMPLETE"