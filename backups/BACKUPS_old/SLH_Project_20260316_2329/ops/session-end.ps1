param(
  [Parameter(Mandatory=$true)]
  [string]$Status,

  [string]$Notes = ""
)

$ErrorActionPreference = "Stop"
$ROOT = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location (Split-Path -Parent $ROOT)

$currentSessionPath = ".\runtime\current_session.json"
$csvPath = ".\runtime\work_sessions.csv"

if (-not (Test-Path $currentSessionPath)) {
  throw "No active session found. Start one first with .\ops\session-start.ps1"
}

$session = Get-Content $currentSessionPath -Raw | ConvertFrom-Json

$session_id   = [string]$session.session_id
$start_local  = [string]$session.start_local
$session_type = [string]$session.session_type
$start_notes  = [string]$session.notes
$machine      = [string]$session.machine
$user_name    = [string]$session.user_name
$project_root = [string]$session.project_root

$endDt = Get-Date
$end_local = $endDt.ToString("yyyy-MM-dd HH:mm:ss")
$startDt = [datetime]::ParseExact($start_local, "yyyy-MM-dd HH:mm:ss", $null)
$duration_minutes = [Math]::Round((($endDt - $startDt).TotalMinutes), 2)

$combinedNotes = $start_notes
if (-not [string]::IsNullOrWhiteSpace($Notes)) {
  if (-not [string]::IsNullOrWhiteSpace($combinedNotes)) {
    $combinedNotes = "$combinedNotes | $Notes"
  } else {
    $combinedNotes = $Notes
  }
}

if (-not (Test-Path ".\runtime")) {
  New-Item -ItemType Directory -Force -Path ".\runtime" | Out-Null
}

if (-not (Test-Path $csvPath)) {
  'session_id,start_local,end_local,duration_minutes,session_type,status,machine,user_name,notes,project_root' |
    Out-File -FilePath $csvPath -Encoding utf8
}

$row = [pscustomobject]@{
  session_id        = $session_id
  start_local       = $start_local
  end_local         = $end_local
  duration_minutes  = $duration_minutes
  session_type      = $session_type
  status            = $Status
  machine           = $machine
  user_name         = $user_name
  notes             = $combinedNotes
  project_root      = $project_root
}

$row | Export-Csv -Path $csvPath -Append -NoTypeInformation

Remove-Item $currentSessionPath -Force -ErrorAction SilentlyContinue

Write-Host ""
Write-Host "SESSION ENDED" -ForegroundColor Green
Write-Host ("session_id        : {0}" -f $session_id)
Write-Host ("start_local       : {0}" -f $start_local)
Write-Host ("end_local         : {0}" -f $end_local)
Write-Host ("duration_minutes  : {0}" -f $duration_minutes)
Write-Host ("status            : {0}" -f $Status)
Write-Host ("notes             : {0}" -f $combinedNotes)
Write-Host ("csv               : {0}" -f $csvPath)

Write-Host ""
Write-Host "+--------------------------------------+" -ForegroundColor DarkCyan
Write-Host "|        SLH WORK SESSION CLOSED       |" -ForegroundColor Cyan
Write-Host "+--------------------------------------+" -ForegroundColor DarkCyan
Write-Host ("| Start    : {0,-25} |" -f $start_local) -ForegroundColor White
Write-Host ("| End      : {0,-25} |" -f $end_local) -ForegroundColor White
Write-Host ("| Duration : {0,-25} |" -f ($duration_minutes.ToString() + " minutes")) -ForegroundColor Yellow
Write-Host ("| Status   : {0,-25} |" -f $Status) -ForegroundColor Green
Write-Host "+--------------------------------------+" -ForegroundColor DarkCyan

$motivation = @(
  "Great work. Commit. Push. Rest.",
  "Another brick in the architecture.",
  "Engineers build the future.",
  "Progress logged. System stronger.",
  "Code. Test. Ship. Repeat."
)

$msg = Get-Random $motivation
if ($msg.Length -gt 36) { $msg = $msg.Substring(0,36) }
Write-Host ("| {0,-36} |" -f $msg) -ForegroundColor Magenta
Write-Host "+--------------------------------------+" -ForegroundColor DarkCyan
Write-Host ""