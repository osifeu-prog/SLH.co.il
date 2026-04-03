$ErrorActionPreference = "Stop"
$ROOT = "D:\SLH_PROJECT_V2"
Set-Location $ROOT

function Good([string]$m) { Write-Host $m -ForegroundColor Green }
function Warn([string]$m) { Write-Host $m -ForegroundColor Yellow }

function Section([string]$t) {
  Write-Host ""
  Write-Host "=== $t ===" -ForegroundColor Magenta
}

function Sum-Minutes($items) {
  if(-not $items){ return 0.0 }
  $sum = ($items | Measure-Object -Property duration_minutes -Sum).Sum
  if($null -eq $sum){ $sum = 0.0 }
  return [Math]::Round([double]$sum, 2)
}

function Avg-Minutes($items) {
  if(-not $items -or $items.Count -eq 0){ return 0.0 }
  $avg = ($items | Measure-Object -Property duration_minutes -Average).Average
  if($null -eq $avg){ $avg = 0.0 }
  return [Math]::Round([double]$avg, 2)
}

$csvPath = ".\runtime\work_sessions.csv"

Section "SESSION REPORT"

if (-not (Test-Path $csvPath)) {
  Warn "Missing runtime\work_sessions.csv"
  exit 0
}

$rows = Import-Csv $csvPath
if (-not $rows -or $rows.Count -eq 0) {
  Warn "No session rows found"
  exit 0
}

$today = (Get-Date).Date
$weekStart = $today.AddDays(-([int]$today.DayOfWeek))
$parsed = @()

foreach ($r in $rows) {
  $start = $null
  $end = $null
  $dur = 0.0

  try { if ($r.start_local) { $start = [datetime]$r.start_local } } catch {}
  try { if ($r.end_local)   { $end   = [datetime]$r.end_local } } catch {}
  try { if ($r.duration_minutes) { $dur = [double]$r.duration_minutes } } catch {}

  $parsed += [pscustomobject]@{
    session_id       = $r.session_id
    start_local      = $start
    end_local        = $end
    duration_minutes = $dur
    session_type     = $r.session_type
    status           = $r.status
    notes            = $r.notes
  }
}

$todayRows = $parsed | Where-Object { $_.start_local -and $_.start_local.Date -eq $today }
$weekRows  = $parsed | Where-Object { $_.start_local -and $_.start_local.Date -ge $weekStart }

Section "1) TODAY"
Good ("Sessions today : " + $todayRows.Count)
Good ("Minutes today  : " + (Sum-Minutes $todayRows))
Good ("Average today  : " + (Avg-Minutes $todayRows))

Section "2) THIS WEEK"
Good ("Sessions week  : " + $weekRows.Count)
Good ("Minutes week   : " + (Sum-Minutes $weekRows))
Good ("Average week   : " + (Avg-Minutes $weekRows))

Section "3) BY STATUS"
$byStatus = $parsed | Group-Object status | Sort-Object Name
foreach($g in $byStatus){
  $sum = Sum-Minutes $g.Group
  $name = $g.Name
  if([string]::IsNullOrWhiteSpace($name)){ $name = "<blank>" }
  Write-Host ($name + " :: count=" + $g.Count + " minutes=" + $sum) -ForegroundColor Cyan
}

Section "4) BY TYPE"
$byType = $parsed | Group-Object session_type | Sort-Object Name
foreach($g in $byType){
  $sum = Sum-Minutes $g.Group
  $name = $g.Name
  if([string]::IsNullOrWhiteSpace($name)){ $name = "<blank>" }
  Write-Host ($name + " :: count=" + $g.Count + " minutes=" + $sum) -ForegroundColor Cyan
}

Section "5) LAST 10 SESSIONS"
$parsed |
  Sort-Object start_local -Descending |
  Select-Object -First 10 start_local, end_local, duration_minutes, session_type, status, notes |
  Format-Table -AutoSize