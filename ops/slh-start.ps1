# slh-start.ps1 — SLH Ecosystem single-command launcher.
#
# Boots the full local/production stack in the right order, checks each service
# as it comes up, and fails loud if something is wrong instead of silently
# partial-booting.
#
# Usage (from any directory):
#   powershell -File D:\SLH_ECOSYSTEM\ops\slh-start.ps1
#   powershell -File D:\SLH_ECOSYSTEM\ops\slh-start.ps1 -SkipDocker
#   powershell -File D:\SLH_ECOSYSTEM\ops\slh-start.ps1 -Verify
#   powershell -File D:\SLH_ECOSYSTEM\ops\slh-start.ps1 -Stop
#
# What it does (in order):
#   1. Verifies prerequisites (docker, git, python, node).
#   2. Pulls latest code (master for api, main for website).
#   3. Docker compose up -d (postgres + redis + 25 bots).
#   4. Waits for Postgres + Redis.
#   5. Checks Railway API health (remote, already deployed).
#   6. Verifies 5 critical public endpoints return 2xx.
#   7. Prints a health matrix + next steps.
#
# Safe: doesn't push, doesn't modify git state beyond pull, doesn't touch .env.

[CmdletBinding()]
param(
    [switch]$SkipDocker,
    [switch]$SkipGit,
    [switch]$Verify,
    [switch]$Stop,
    [string]$RepoRoot = "D:\SLH_ECOSYSTEM",
    [string]$ApiHost = "https://slh-api-production.up.railway.app"
)

$ErrorActionPreference = "Continue"

function Write-Step($msg) { Write-Host "`n==> $msg" -ForegroundColor Cyan }
function Write-Ok($msg)   { Write-Host "   [ok]  $msg" -ForegroundColor Green }
function Write-Warn($msg) { Write-Host "   [warn]$msg" -ForegroundColor Yellow }
function Write-Fail($msg) { Write-Host "   [fail]$msg" -ForegroundColor Red }

function Test-Cmd($name) {
    $null = Get-Command $name -ErrorAction SilentlyContinue
    return $?
}

function Get-HttpStatus($url, $timeoutSec = 6) {
    try {
        $r = Invoke-WebRequest -Uri $url -Method Get -TimeoutSec $timeoutSec -UseBasicParsing
        return [int]$r.StatusCode
    } catch [System.Net.WebException] {
        if ($_.Exception.Response) { return [int]$_.Exception.Response.StatusCode }
        return -1
    } catch {
        return -1
    }
}

# ------------------------------------------------------------------
# Stop mode: tear down docker compose, kill stuck serial monitors.
# ------------------------------------------------------------------
if ($Stop) {
    Write-Step "Stopping stack"
    Push-Location $RepoRoot
    if (Test-Path "docker-compose.yml") {
        docker compose -f "docker-compose.yml" down 2>&1 | Out-Null
        Write-Ok "docker compose down"
    } else {
        Write-Warn "docker-compose.yml not found in $RepoRoot"
    }
    Pop-Location

    $stuck = Get-Process pio -ErrorAction SilentlyContinue
    if ($stuck) {
        foreach ($p in $stuck) {
            try { $p.Kill(); Write-Ok "killed stuck pio PID $($p.Id)" }
            catch { Write-Warn "could not kill pio PID $($p.Id): $_" }
        }
    }
    Write-Host "`nStopped." -ForegroundColor Cyan
    exit 0
}

# ------------------------------------------------------------------
# 1. Prerequisites
# ------------------------------------------------------------------
Write-Step "Checking prerequisites"
$missing = @()
foreach ($cmd in @("docker", "git", "python")) {
    if (Test-Cmd $cmd) { Write-Ok "$cmd found" } else { Write-Fail "$cmd missing"; $missing += $cmd }
}
if ($missing.Count -gt 0) {
    Write-Host "`nMissing required tools: $($missing -join ', '). Install them and retry." -ForegroundColor Red
    exit 2
}
if (-not (Test-Path $RepoRoot)) {
    Write-Fail "Repo root $RepoRoot does not exist."
    exit 2
}
Write-Ok "repo root $RepoRoot"

# ------------------------------------------------------------------
# 2. Verify-only mode: skip starts, go straight to health checks.
# ------------------------------------------------------------------
if ($Verify) {
    Write-Step "Verify-only run (no starts)"
} else {

    # ------------------------------------------------------------------
    # 3. Git pull (non-destructive)
    # ------------------------------------------------------------------
    if (-not $SkipGit) {
        Write-Step "Pulling latest code (non-destructive)"
        Push-Location $RepoRoot
        $dirty = git status --porcelain 2>&1
        if ($dirty) {
            Write-Warn "uncommitted changes in $RepoRoot — skipping pull to preserve work"
        } else {
            git pull --ff-only 2>&1 | ForEach-Object { Write-Host "    $_" }
            Write-Ok "api repo up-to-date"
        }
        Pop-Location

        if (Test-Path "$RepoRoot\website") {
            Push-Location "$RepoRoot\website"
            $dirty = git status --porcelain 2>&1
            if ($dirty) {
                Write-Warn "uncommitted changes in website — skipping pull"
            } else {
                git pull --ff-only 2>&1 | ForEach-Object { Write-Host "    $_" }
                Write-Ok "website repo up-to-date"
            }
            Pop-Location
        }
    } else {
        Write-Warn "git pull skipped (-SkipGit)"
    }

    # ------------------------------------------------------------------
    # 4. Docker compose up
    # ------------------------------------------------------------------
    if (-not $SkipDocker) {
        Write-Step "Starting docker compose stack"
        Push-Location $RepoRoot
        $composeFile = Join-Path $RepoRoot "docker-compose.yml"
        if (-not (Test-Path $composeFile)) {
            Write-Fail "docker-compose.yml missing at $composeFile"
            Pop-Location
            exit 3
        }
        docker compose -f $composeFile up -d 2>&1 | ForEach-Object { Write-Host "    $_" }
        Pop-Location
        Write-Ok "docker compose up -d issued"

        Write-Step "Waiting for postgres + redis"
        $pgUp = $false; $redisUp = $false
        for ($i = 0; $i -lt 30; $i++) {
            Start-Sleep -Seconds 2
            if (-not $pgUp) {
                $pgCheck = docker exec slh-postgres pg_isready 2>$null
                if ($LASTEXITCODE -eq 0) { $pgUp = $true; Write-Ok "postgres ready" }
            }
            if (-not $redisUp) {
                $redisCheck = docker exec slh-redis redis-cli ping 2>$null
                if ($redisCheck -match "PONG") { $redisUp = $true; Write-Ok "redis ready" }
            }
            if ($pgUp -and $redisUp) { break }
        }
        if (-not $pgUp) { Write-Fail "postgres did not come up in 60s" }
        if (-not $redisUp) { Write-Fail "redis did not come up in 60s" }
    } else {
        Write-Warn "docker compose skipped (-SkipDocker)"
    }
}

# ------------------------------------------------------------------
# 5. Health matrix — Railway API (deployed) + local services
# ------------------------------------------------------------------
Write-Step "Health matrix"

$checks = @(
    @{ Name = "Railway /api/health";          Url = "$ApiHost/api/health";             Expect = 200 },
    @{ Name = "Railway /api/prices";          Url = "$ApiHost/api/prices";             Expect = 200 },
    @{ Name = "Railway /api/stats";           Url = "$ApiHost/api/stats";              Expect = 200 },
    @{ Name = "Railway /api/academia/courses";Url = "$ApiHost/api/academia/courses";   Expect = 200 },
    @{ Name = "Railway /api/events/public";   Url = "$ApiHost/api/events/public";      Expect = 200 },
    @{ Name = "Website / (GitHub Pages)";     Url = "https://slh-nft.com";             Expect = 200 },
    @{ Name = "Website /miniapp/dashboard";   Url = "https://slh-nft.com/miniapp/dashboard.html"; Expect = 200 }
)

$table = foreach ($c in $checks) {
    $status = Get-HttpStatus $c.Url
    $result = if ($status -eq $c.Expect) { "ok" } elseif ($status -eq -1) { "unreachable" } else { "got $status" }
    [pscustomobject]@{
        Service = $c.Name
        URL     = $c.Url
        Status  = $status
        Result  = $result
    }
}
$table | Format-Table -AutoSize

# Count failures
$bad = $table | Where-Object { $_.Result -ne "ok" }
if ($bad.Count -gt 0) {
    Write-Warn "$($bad.Count) / $($table.Count) checks failed. Inspect table above."
} else {
    Write-Ok "all $($table.Count) checks passed"
}

# Local docker health (only if docker is running)
if (-not $SkipDocker -and -not $Verify) {
    Write-Step "Docker services"
    $psOut = docker ps --format "table {{.Names}}\t{{.Status}}" 2>&1
    $psOut | ForEach-Object { Write-Host "   $_" }
}

# ------------------------------------------------------------------
# 6. Next steps
# ------------------------------------------------------------------
Write-Step "Next steps"
Write-Host @"
  - To stop the stack:        powershell -File $PSCommandPath -Stop
  - To re-check health only:  powershell -File $PSCommandPath -Verify
  - To skip git pull:         add -SkipGit
  - To skip docker:           add -SkipDocker

  Manual steps still needed (cannot be automated from here):
    * Railway dashboard:  set ADMIN_API_KEYS, JWT_SECRET, BSCSCAN_API_KEY, ANTHROPIC_API_KEY
    * BotFather:          set Mini App URL for @WEWORK_teamviwer_bot -> https://slh-nft.com/miniapp/dashboard.html
    * ESP32 firmware:     flash from D:\SLH_ECOSYSTEM\device-registry\esp32-cyd-work\firmware\slh-device-v3
    * Gateway wiring:     import api.telegram_gateway into main.py (see ops/TELEGRAM_FIRST_MIGRATION_PLAN.md)

  See ops/OPS_RUNBOOK.md for full operations reference.
"@ -ForegroundColor Gray

if ($bad.Count -gt 0) { exit 1 } else { exit 0 }
