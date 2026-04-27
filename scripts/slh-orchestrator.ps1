# SLH Orchestrator — PowerShell wrapper
# ======================================
# Loads .env (if present) and runs the Python orchestrator.
#
# Usage:
#   .\slh-orchestrator.ps1            # run forever (the normal mode)
#   .\slh-orchestrator.ps1 -Once      # one cycle then exit
#   .\slh-orchestrator.ps1 -Check     # sanity check
#   .\slh-orchestrator.ps1 -Install   # install as Windows scheduled task (auto-start)
#
# Author: Claude (Cowork mode, 2026-04-27)

param(
    [switch]$Once,
    [switch]$HeartbeatsOnly,
    [switch]$Check,
    [switch]$Install,
    [switch]$Uninstall
)

$ErrorActionPreference = "Stop"
$projectRoot = "D:\SLH_ECOSYSTEM"
$pythonScript = Join-Path $projectRoot "scripts\slh-orchestrator.py"
$envFile = Join-Path $projectRoot ".env"
$logFile = Join-Path $projectRoot "ops\orchestrator.log"

# ─────────────────────────────────────────────────────────────────
# Install/Uninstall as Windows scheduled task
# ─────────────────────────────────────────────────────────────────
if ($Install) {
    Write-Host "Installing SLH Orchestrator as a scheduled task (auto-start at boot)…" -ForegroundColor Cyan
    $action = New-ScheduledTaskAction -Execute "powershell.exe" `
        -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$PSCommandPath`""
    $trigger = New-ScheduledTaskTrigger -AtStartup
    $settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1)
    $principal = New-ScheduledTaskPrincipal -UserId "$env:USERNAME" -RunLevel Highest
    Register-ScheduledTask -TaskName "SLH-Orchestrator" -Action $action -Trigger $trigger -Settings $settings -Principal $principal -Force
    Write-Host "✓ Installed. Start now with: Start-ScheduledTask -TaskName SLH-Orchestrator" -ForegroundColor Green
    exit 0
}

if ($Uninstall) {
    Write-Host "Removing SLH-Orchestrator scheduled task…" -ForegroundColor Yellow
    Unregister-ScheduledTask -TaskName "SLH-Orchestrator" -Confirm:$false
    Write-Host "✓ Removed" -ForegroundColor Green
    exit 0
}

# ─────────────────────────────────────────────────────────────────
# Load .env
# ─────────────────────────────────────────────────────────────────
if (Test-Path $envFile) {
    Write-Host "Loading env from $envFile" -ForegroundColor DarkGray
    Get-Content $envFile | ForEach-Object {
        if ($_ -match '^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*?)\s*$' -and $_ -notmatch '^\s*#') {
            $name = $matches[1]
            $value = $matches[2].Trim('"').Trim("'")
            [System.Environment]::SetEnvironmentVariable($name, $value, "Process")
        }
    }
} else {
    Write-Warning "No .env file at $envFile — using existing process env"
}

# ─────────────────────────────────────────────────────────────────
# Verify Python is on PATH
# ─────────────────────────────────────────────────────────────────
$python = (Get-Command python -ErrorAction SilentlyContinue) ?? (Get-Command python3 -ErrorAction SilentlyContinue)
if (-not $python) {
    Write-Error "Python not found on PATH. Install Python 3.10+ first."
    exit 1
}

# ─────────────────────────────────────────────────────────────────
# Build args
# ─────────────────────────────────────────────────────────────────
$args = @($pythonScript)
if ($Once)            { $args += "--once" }
if ($HeartbeatsOnly)  { $args += "--heartbeats-only" }
if ($Check)           { $args += "--check" }

# ─────────────────────────────────────────────────────────────────
# Run
# ─────────────────────────────────────────────────────────────────
Write-Host "Starting SLH Orchestrator…" -ForegroundColor Cyan
Write-Host "  API:    $($env:SLH_API_BASE ?? 'https://slhcoil-production.up.railway.app')" -ForegroundColor DarkGray
Write-Host "  Logs:   $logFile" -ForegroundColor DarkGray
Write-Host ""

& $python.Source @args
$exitCode = $LASTEXITCODE
exit $exitCode
