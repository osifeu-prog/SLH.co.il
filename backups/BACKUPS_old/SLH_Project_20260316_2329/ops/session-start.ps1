param(
  [Parameter(Mandatory=$true)]
  [string]$Type,

  [string]$Notes = ""
)

$ErrorActionPreference = "Stop"
$ROOT = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location (Split-Path -Parent $ROOT)

$currentSessionPath = ".\runtime\current_session.json"

if (Test-Path $currentSessionPath) {
  throw "An active session already exists: runtime\current_session.json. End it first with .\ops\session-end.ps1"
}

if (-not (Test-Path ".\runtime")) {
  New-Item -ItemType Directory -Force -Path ".\runtime" | Out-Null
}

$now = Get-Date
$session_id = [guid]::NewGuid().ToString()
$start_local = $now.ToString("yyyy-MM-dd HH:mm:ss")
$start_iso = $now.ToUniversalTime().ToString("o")
$machine = $env:COMPUTERNAME
$user_name = $env:USERNAME
$project_root = (Get-Location).Path

$obj = [pscustomobject]@{
  session_id   = $session_id
  start_local  = $start_local
  start_iso    = $start_iso
  machine      = $machine
  user_name    = $user_name
  session_type = $Type
  notes        = $Notes
  project_root = $project_root
}

$obj | ConvertTo-Json -Depth 5 | Out-File -FilePath $currentSessionPath -Encoding utf8

Write-Host ""
Write-Host "SESSION STARTED" -ForegroundColor Green
Write-Host ("session_id   : {0}" -f $session_id)
Write-Host ("start_local  : {0}" -f $start_local)
Write-Host ("session_type : {0}" -f $Type)
Write-Host ("notes        : {0}" -f $Notes)

Write-Host ""
Write-Host "+--------------------------------------+" -ForegroundColor DarkCyan
Write-Host "|        SLH WORK SESSION STARTED      |" -ForegroundColor Cyan
Write-Host "+--------------------------------------+" -ForegroundColor DarkCyan
Write-Host ("| Start    : {0,-25} |" -f $start_local) -ForegroundColor White
Write-Host ("| Type     : {0,-25} |" -f $Type) -ForegroundColor Yellow

$notesDisplay = $Notes
if ([string]::IsNullOrWhiteSpace($notesDisplay)) { $notesDisplay = "-" }
if ($notesDisplay.Length -gt 25) { $notesDisplay = $notesDisplay.Substring(0,25) }

Write-Host ("| Notes    : {0,-25} |" -f $notesDisplay) -ForegroundColor Green
Write-Host "+--------------------------------------+" -ForegroundColor DarkCyan

$motivation = @(
  "Deep work mode: ON",
  "Build mode engaged",
  "Focus. Execute. Finish.",
  "System upgrade in progress",
  "Engineering session live"
)

$msg = Get-Random $motivation
if ($msg.Length -gt 36) { $msg = $msg.Substring(0,36) }
Write-Host ("| {0,-36} |" -f $msg) -ForegroundColor Magenta
Write-Host "+--------------------------------------+" -ForegroundColor DarkCyan
Write-Host ""