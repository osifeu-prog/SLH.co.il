param(
  [switch]$SaveReport
)

$ErrorActionPreference = "Stop"
$ROOT = "D:\SLH_PROJECT_V2"
Set-Location $ROOT

function Info([string]$m) { Write-Host $m -ForegroundColor Cyan }
function Good([string]$m) { Write-Host $m -ForegroundColor Green }
function Warn([string]$m) { Write-Host $m -ForegroundColor Yellow }
function Bad([string]$m)  { Write-Host $m -ForegroundColor Red }

function Section([string]$t) {
  Write-Host ""
  Write-Host "=== $t ===" -ForegroundColor Magenta
}

function Test-CommandExists([string]$cmd) {
  return $null -ne (Get-Command $cmd -ErrorAction SilentlyContinue)
}

function Save-Text([string]$Path,[string]$Text){
  $dir = Split-Path $Path -Parent
  if($dir -and -not (Test-Path $dir)){
    New-Item -ItemType Directory -Force -Path $dir | Out-Null
  }
  $enc = New-Object System.Text.UTF8Encoding($false)
  [System.IO.File]::WriteAllText($Path, ($Text -replace "`r`n","`n"), $enc)
}

$lines = New-Object System.Collections.Generic.List[string]
function Add-Line([string]$s) {
  $null = $lines.Add($s)
}

Section "MIDDAY CHECK"
Add-Line ("MIDDAY CHECK :: " + (Get-Date).ToString("yyyy-MM-dd HH:mm:ss"))

Section "1) HEALTH"
try {
  $r = Invoke-WebRequest "http://127.0.0.1:8080/healthz" -UseBasicParsing -TimeoutSec 10
  Good ("HTTP: " + $r.StatusCode)
  Write-Host $r.Content
  Add-Line ("HEALTH HTTP=" + $r.StatusCode)
  Add-Line ("HEALTH BODY=" + $r.Content)
} catch {
  Warn "Health check failed"
  Add-Line ("HEALTH ERROR=" + $_.Exception.Message)
}

Section "2) STATUS"
try {
  & ".\slh.ps1" status
  Good "status completed"
  Add-Line "STATUS=OK"
} catch {
  Warn "status failed"
  Add-Line ("STATUS ERROR=" + $_.Exception.Message)
}

Section "3) PORT 8080"
try {
  $p8080 = Get-NetTCPConnection -LocalPort 8080 -ErrorAction Stop |
    Select-Object LocalAddress, LocalPort, State, OwningProcess
  $p8080 | Format-Table -AutoSize
  Add-Line "PORT8080=LISTENING"
  foreach($row in $p8080){
    Add-Line ("PORT8080 PID=" + $row.OwningProcess + " STATE=" + $row.State)
  }
} catch {
  Warn "No listener on 8080"
  Add-Line "PORT8080=NO_LISTENER"
}

Section "4) PROJECT PYTHON"
$py = Get-Process python -ErrorAction SilentlyContinue |
  Where-Object { $_.Path -like "*SLH_PROJECT_V2*" } |
  Select-Object Id, ProcessName, Path, StartTime

if($py){
  $py | Format-Table -AutoSize
  Add-Line ("PROJECT_PYTHON_COUNT=" + $py.Count)
  foreach($p in $py){
    Add-Line ("PYTHON PID=" + $p.Id + " PATH=" + $p.Path)
  }
} else {
  Warn "No project python processes found"
  Add-Line "PROJECT_PYTHON_COUNT=0"
}

Section "5) REDIS"
try {
  if (Test-CommandExists "docker") {
    $redisPs = docker ps --format "{{.Names}}`t{{.Status}}" | Select-String -Pattern "slh_redis" -SimpleMatch
    if ($redisPs) {
      Good "Redis container found"
      $redisPs | ForEach-Object { $_.ToString() | Write-Host }
      Add-Line ("REDIS=" + ($redisPs.ToString()))
    } else {
      Warn "Redis container not found"
      Add-Line "REDIS=NOT_FOUND"
    }
  } else {
    Warn "docker not found"
    Add-Line "REDIS=DOCKER_NOT_FOUND"
  }
} catch {
  Warn "Redis check failed"
  Add-Line ("REDIS ERROR=" + $_.Exception.Message)
}

Section "6) DB PING"
try {
  if (Test-CommandExists "psql") {
    $dbOut = & psql -h 127.0.0.1 -p 5432 -U postgres -d slh_db -t -A -c "SELECT NOW();"
    Good "Postgres OK"
    $dbOut | Write-Host
    Add-Line ("DB_NOW=" + ($dbOut | Out-String).Trim())
  } else {
    Warn "psql not found"
    Add-Line "DB=PSQL_NOT_FOUND"
  }
} catch {
  Warn "Postgres check failed"
  Add-Line ("DB ERROR=" + $_.Exception.Message)
}

Section "7) TELEGRAM WEBHOOK"
try {
  $envText = Get-Content .\.env -Raw
  $botToken = ([regex]::Match($envText,'(?m)^BOT_TOKEN=(.+)$')).Groups[1].Value.Trim()
  if ($botToken) {
    $wh = Invoke-RestMethod -Uri ("https://api.telegram.org/bot{0}/getWebhookInfo" -f $botToken)
    $wh.result | Format-List
    Add-Line ("WEBHOOK_URL=" + $wh.result.url)
    Add-Line ("WEBHOOK_PENDING=" + $wh.result.pending_update_count)
  } else {
    Warn "BOT_TOKEN missing in .env"
    Add-Line "WEBHOOK=BOT_TOKEN_MISSING"
  }
} catch {
  Warn "Webhook check failed"
  Add-Line ("WEBHOOK ERROR=" + $_.Exception.Message)
}

if($SaveReport){
  $stamp = Get-Date -Format "yyyyMMdd_HHmmss"
  $reportPath = ".\state\midday_check_$stamp.txt"
  Save-Text $reportPath (($lines -join [Environment]::NewLine) + [Environment]::NewLine)
  Good ("Saved report: " + $reportPath)
}