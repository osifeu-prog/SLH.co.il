# slh-start.ps1 — SLH Spark One-Command Orchestrator
# Usage:
#   .\slh-start.ps1                        # full start
#   .\slh-start.ps1 -SkipPull              # don't fetch origin
#   .\slh-start.ps1 -SkipBuild             # skip docker compose build
#   .\slh-start.ps1 -SkipHealth            # don't run health checks
#   .\slh-start.ps1 -DryRun                # print what would happen
#   .\slh-start.ps1 -StatusOnly            # only check current state
#
# Exit codes:
#   0  — all healthy
#   1  — something unhealthy (see output)
#   2  — critical (git dirty + -StatusOnly wants block)
#
# Docs: ops/SYSTEM_ARCHITECTURE.md
# Incident log: ops/INCIDENT_20260421_GIT_DRIFT.md (drift recovery pattern)

param(
    [switch]$SkipPull,
    [switch]$SkipBuild,
    [switch]$SkipHealth,
    [switch]$DryRun,
    [switch]$StatusOnly
)

$ErrorActionPreference = "Continue"

# ─── Config ───────────────────────────────────────────────────────
$REPO_ROOT   = "D:\SLH_ECOSYSTEM"
$API_URL     = "https://slh-api-production.up.railway.app"
$WEBSITE_URL = "https://slh-nft.com"

# ─── Output helpers ───────────────────────────────────────────────
function Write-Step($msg) { Write-Host "`n▶ $msg" -ForegroundColor Cyan }
function Write-OK($msg)   { Write-Host "  ✓ $msg" -ForegroundColor Green }
function Write-Warn($msg) { Write-Host "  ⚠ $msg" -ForegroundColor Yellow }
function Write-Err($msg)  { Write-Host "  ✗ $msg" -ForegroundColor Red }
function Write-Info($msg) { Write-Host "  • $msg" -ForegroundColor Gray }

$script:exitCode = 0

# ─── Preflight ────────────────────────────────────────────────────
Write-Host ""
Write-Host "╔══════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║  SLH Spark — Control Layer $(Get-Date -Format 'yyyy-MM-dd HH:mm') ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════════════╝" -ForegroundColor Cyan

if (-not (Test-Path $REPO_ROOT)) {
    Write-Err "Repo root not found: $REPO_ROOT"
    exit 2
}
Set-Location $REPO_ROOT

# ─── 1. Git state ─────────────────────────────────────────────────
Write-Step "Git"
$branch = (git branch --show-current 2>$null).Trim()
$gitStatus = git status --porcelain 2>$null
$headHash = (git rev-parse --short HEAD 2>$null).Trim()
$headMsg  = (git log -1 --format='%s' HEAD 2>$null).Trim()

Write-Info "branch: $branch  @  $headHash  —  $headMsg"

if ($gitStatus) {
    $count = ($gitStatus | Measure-Object).Count
    Write-Warn "$count uncommitted file(s) — review with ``git status``"
    $script:exitCode = 1
} else {
    Write-OK "working tree clean"
}

if (-not $SkipPull -and -not $DryRun) {
    git fetch origin 2>&1 | Out-Null
    $ahead  = (git rev-list --count "origin/$branch..HEAD" 2>$null).Trim()
    $behind = (git rev-list --count "HEAD..origin/$branch" 2>$null).Trim()
    if ([int]$behind -gt 0) { Write-Warn "behind origin/$branch by $behind commit(s) — consider ``git pull``" }
    if ([int]$ahead  -gt 0) { Write-Info "ahead of origin/$branch by $ahead commit(s)" }
    if ([int]$ahead -eq 0 -and [int]$behind -eq 0) { Write-OK "in sync with origin/$branch" }
}

if ($StatusOnly) { exit $script:exitCode }

# ─── 2. Docker Compose lifecycle ──────────────────────────────────
if (-not $DryRun) {
    Write-Step "Docker Compose"

    if (-not $SkipBuild) {
        Write-Info "building changed services..."
        docker compose build 2>&1 | Select-Object -Last 5 | ForEach-Object { Write-Host "    $_" }
    }

    Write-Info "starting services (detached)..."
    docker compose up -d 2>&1 | Select-Object -Last 10 | ForEach-Object { Write-Host "    $_" }
    Write-OK "compose up -d issued"
} else {
    Write-Step "Docker (DRY RUN — skipped)"
}

# ─── 3. Health matrix ─────────────────────────────────────────────
if (-not $SkipHealth -and -not $DryRun) {
    Write-Step "Health matrix"
    Start-Sleep -Seconds 8  # give containers time to bind ports

    # Postgres
    try {
        $pg = docker exec slh-postgres pg_isready -U postgres 2>&1
        if ($pg -match "accepting connections") { Write-OK "postgres: accepting connections" }
        else { Write-Err "postgres: $pg"; $script:exitCode = 1 }
    } catch { Write-Err "postgres: exec failed"; $script:exitCode = 1 }

    # Redis (if present)
    try {
        $redis = docker exec slh-redis redis-cli ping 2>&1
        if ($redis -match "PONG") { Write-OK "redis: PONG" }
        else { Write-Warn "redis: $redis" }
    } catch { Write-Info "redis: not running (optional)" }

    # Railway API
    try {
        $h = Invoke-RestMethod "$API_URL/api/health" -TimeoutSec 10 -ErrorAction Stop
        if ($h.status -eq "ok" -and $h.db -eq "connected") {
            Write-OK "API (Railway): $($h.status) | v$($h.version) | db=$($h.db)"
        } else {
            Write-Warn "API (Railway) degraded: $($h | ConvertTo-Json -Compress)"
            $script:exitCode = 1
        }
    } catch {
        Write-Err "API (Railway): unreachable — $($_.Exception.Message)"
        $script:exitCode = 1
    }

    # Ambassador CRM endpoint (Phase 0, should return 200 or 422 once deployed)
    try {
        $r = Invoke-WebRequest -Uri "$API_URL/api/ambassador/contacts?ambassador_id=0" `
             -Headers @{ 'X-Admin-Key' = $env:SLH_ADMIN_KEY ? $env:SLH_ADMIN_KEY : 'no-key' } `
             -TimeoutSec 10 -SkipHttpErrorCheck -ErrorAction Stop
        if ($r.StatusCode -in @(200, 403)) { Write-OK "CRM endpoint: reachable (HTTP $($r.StatusCode))" }
        elseif ($r.StatusCode -eq 404)    { Write-Warn "CRM endpoint: 404 — Railway not yet deployed latest" ; $script:exitCode = 1 }
        else                               { Write-Warn "CRM endpoint: HTTP $($r.StatusCode)" }
    } catch { Write-Warn "CRM endpoint: check failed" }

    # Running SLH containers
    $containers = docker ps --filter "name=slh-" --format "{{.Names}}:{{.Status}}" 2>$null
    $runningCount = ($containers | Measure-Object).Count
    Write-Info "running slh-* containers: $runningCount"
    $containers | Select-Object -First 8 | ForEach-Object { Write-Host "      $_" -ForegroundColor DarkGray }
    if ($runningCount -gt 8) { Write-Host "      ... ($($runningCount - 8) more)" -ForegroundColor DarkGray }
}

# ─── 4. Summary ───────────────────────────────────────────────────
Write-Step "URLs"
Write-Info "API:       $API_URL"
Write-Info "Website:   $WEBSITE_URL"
Write-Info "Admin:     $WEBSITE_URL/admin/"
Write-Info "Reality:   $WEBSITE_URL/admin/reality.html"
Write-Info "Community: $WEBSITE_URL/community.html"

Write-Host ""
if ($script:exitCode -eq 0) {
    Write-Host "✓ All healthy." -ForegroundColor Green
} else {
    Write-Host "⚠ Some checks failed (exit=$script:exitCode). Scroll up for details." -ForegroundColor Yellow
}
Write-Host ""

exit $script:exitCode
