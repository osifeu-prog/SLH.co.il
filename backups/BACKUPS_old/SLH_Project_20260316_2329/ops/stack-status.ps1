param()
$ErrorActionPreference = "Continue"
. (Join-Path $PSScriptRoot "common.ps1")
Set-Location $ProjectRoot

Show-Section "STACK STATUS"

$state = Read-State

$dockerResponsive = Test-DockerResponsive
$redisRunning = $false
$containerExists = $false

if ($dockerResponsive) {
    $namesResult = Invoke-Docker -Arguments 'ps -a --format "{{.Names}}"' -TimeoutMs 4000
    if ((-not $namesResult.TimedOut) -and $namesResult.ExitCode -eq 0) {
        $names = $namesResult.StdOut
        if ($names -and ($names | Select-String "^slh_redis$")) {
            $containerExists = $true
        }
    }

    if ($containerExists) {
        $pingResult = Invoke-Docker -Arguments 'exec slh_redis redis-cli PING' -TimeoutMs 4000
        if ((-not $pingResult.TimedOut) -and $pingResult.ExitCode -eq 0 -and $pingResult.StdOut -match "PONG") {
            $redisRunning = $true
        }
    }
}

if (-not $dockerResponsive) {
    Write-Host "Docker     : NOT_RESPONDING" -ForegroundColor Yellow
} else {
    Write-Host "Docker     : OK" -ForegroundColor Green
}

Write-Host ("Redis      : " + ($(if($redisRunning){"RUNNING"}elseif($containerExists){"CONTAINER_EXISTS_BUT_DOWN"}else{"DOWN"}))) -ForegroundColor $(if($redisRunning){"Green"}elseif($containerExists){"Yellow"}else{"Red"})

foreach($name in @("worker_pid","webhook_pid","tunnel_pid")) {
    $procId = $state.$name
    $alive = $false
    if ($procId) {
        try { $alive = Test-ProcessAlive([int]$procId) } catch {}
    }
    $label = $name.Replace("_pid","").PadRight(10)
    Write-Host ($label + ": " + ($(if($alive){"RUNNING (PID=$procId)"}else{"DOWN"}))) -ForegroundColor $(if($alive){"Green"}else{"Red"})
}

try {
    $r = Invoke-RestMethod -Uri "http://127.0.0.1:8080/healthz" -TimeoutSec 2
    if ($r.ok -eq $true) {
        Write-Host "healthz    : OK" -ForegroundColor Green
    } else {
        Write-Host "healthz    : BAD" -ForegroundColor Yellow
    }
} catch {
    Write-Host "healthz    : DOWN" -ForegroundColor Red
}

Write-Host ""
if (Test-Path $PidFile) {
    Write-Host "State file : $PidFile" -ForegroundColor DarkGray
    try { Get-Content $PidFile -Raw | Write-Host -ForegroundColor DarkGray } catch {}
} else {
    Write-Host "State file : MISSING" -ForegroundColor DarkGray
}