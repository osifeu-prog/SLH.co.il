# setup-scheduled-tasks.ps1
# One-command installer for SLH Spark scheduled tasks:
#   - SLH_Railway_Watchdog  : every 5 minutes, alerts if Railway deploy stuck
#   - SLH_Daily_Digest      : every day at 21:00 Israel, DMs Osif with summary
#
# Usage (requires admin PowerShell):
#   .\scripts\setup-scheduled-tasks.ps1            # install both
#   .\scripts\setup-scheduled-tasks.ps1 -List      # show current state
#   .\scripts\setup-scheduled-tasks.ps1 -Uninstall # remove both
#   .\scripts\setup-scheduled-tasks.ps1 -TestRun   # run both once, don't schedule

param(
    [switch]$List,
    [switch]$Uninstall,
    [switch]$TestRun
)

$ErrorActionPreference = "Stop"

$REPO = "D:\SLH_ECOSYSTEM"
$PYTHON = (Get-Command python -ErrorAction SilentlyContinue).Source
if (-not $PYTHON) {
    Write-Host "[ERR] python not found in PATH. Install Python or add to PATH." -ForegroundColor Red
    exit 1
}

$TASKS = @(
    @{
        Name        = "SLH_Railway_Watchdog"
        Description = "Alerts Osif via Telegram if Railway deploy version is stuck for >15 min"
        Script      = "$REPO\scripts\railway_watchdog.py"
        Trigger     = "Every 5 minutes"
    },
    @{
        Name        = "SLH_Daily_Digest"
        Description = "Compiles and DMs Osif a daily summary at 21:00 Israel time"
        Script      = "$REPO\scripts\daily_digest.py"
        Trigger     = "Daily at 21:00"
    },
    @{
        Name        = "SLH_Secrets_Sweep"
        Description = "Health-checks all 12 vault secrets every 6h, fires Telegram alerts on transitions"
        Script      = "$REPO\scripts\secrets_health_sweep.py"
        Trigger     = "Every 6 hours"
    },
    @{
        Name        = "SLH_Secrets_Digest"
        Description = "Sends Hebrew Telegram digest of secret health + overdue rotations daily at 21:05"
        Script      = "$REPO\scripts\secrets_daily_digest.py"
        Trigger     = "Daily at 21:05"
    }
)

function Show-List {
    Write-Host "`nSLH Scheduled Tasks status:`n" -ForegroundColor Cyan
    foreach ($t in $TASKS) {
        $existing = Get-ScheduledTask -TaskName $t.Name -ErrorAction SilentlyContinue
        if ($existing) {
            $info = Get-ScheduledTaskInfo -TaskName $t.Name
            $nextRun = if ($info.NextRunTime) { $info.NextRunTime.ToString("yyyy-MM-dd HH:mm") } else { "never" }
            $lastRun = if ($info.LastRunTime) { $info.LastRunTime.ToString("yyyy-MM-dd HH:mm") } else { "never" }
            Write-Host "  [$($existing.State)] $($t.Name)" -ForegroundColor Green
            Write-Host "      last=$lastRun  next=$nextRun  result=$($info.LastTaskResult)" -ForegroundColor Gray
        } else {
            Write-Host "  [NOT INSTALLED] $($t.Name)" -ForegroundColor Yellow
        }
    }
    Write-Host ""
}

function Uninstall-All {
    foreach ($t in $TASKS) {
        $existing = Get-ScheduledTask -TaskName $t.Name -ErrorAction SilentlyContinue
        if ($existing) {
            Unregister-ScheduledTask -TaskName $t.Name -Confirm:$false
            Write-Host "  ✓ Removed $($t.Name)" -ForegroundColor Green
        } else {
            Write-Host "  - Not installed: $($t.Name)" -ForegroundColor Gray
        }
    }
}

function Install-All {
    foreach ($t in $TASKS) {
        if (-not (Test-Path $t.Script)) {
            Write-Host "  ✗ Script not found: $($t.Script)" -ForegroundColor Red
            continue
        }

        $existing = Get-ScheduledTask -TaskName $t.Name -ErrorAction SilentlyContinue
        if ($existing) {
            Write-Host "  ⚠ $($t.Name) already exists — unregistering first" -ForegroundColor Yellow
            Unregister-ScheduledTask -TaskName $t.Name -Confirm:$false
        }

        $action = New-ScheduledTaskAction `
            -Execute $PYTHON `
            -Argument $t.Script `
            -WorkingDirectory $REPO

        switch ($t.Name) {
            "SLH_Railway_Watchdog" {
                # Every 5 minutes, for 1 day, repeat indefinitely
                $trigger = New-ScheduledTaskTrigger -Once -At (Get-Date) `
                    -RepetitionInterval (New-TimeSpan -Minutes 5) `
                    -RepetitionDuration ([TimeSpan]::MaxValue)
            }
            "SLH_Daily_Digest" {
                # Daily at 21:00
                $trigger = New-ScheduledTaskTrigger -Daily -At "21:00"
            }
            "SLH_Secrets_Sweep" {
                # Every 6 hours starting from now
                $trigger = New-ScheduledTaskTrigger -Once -At (Get-Date) `
                    -RepetitionInterval (New-TimeSpan -Hours 6) `
                    -RepetitionDuration ([TimeSpan]::MaxValue)
            }
            "SLH_Secrets_Digest" {
                # Daily at 21:05 (5 min after general digest, so sweep already ran)
                $trigger = New-ScheduledTaskTrigger -Daily -At "21:05"
            }
        }

        $settings = New-ScheduledTaskSettingsSet `
            -AllowStartIfOnBatteries `
            -DontStopIfGoingOnBatteries `
            -StartWhenAvailable `
            -ExecutionTimeLimit (New-TimeSpan -Minutes 10) `
            -RestartCount 2 `
            -RestartInterval (New-TimeSpan -Minutes 5)

        Register-ScheduledTask `
            -TaskName $t.Name `
            -Description $t.Description `
            -Action $action `
            -Trigger $trigger `
            -Settings $settings `
            -User $env:USERNAME `
            -RunLevel Limited | Out-Null

        Write-Host "  ✓ Installed $($t.Name) — $($t.Trigger)" -ForegroundColor Green
    }
}

function Test-Run {
    foreach ($t in $TASKS) {
        if (-not (Test-Path $t.Script)) {
            Write-Host "  ✗ Script not found: $($t.Script)" -ForegroundColor Red
            continue
        }
        Write-Host "`n──── Running: $($t.Name) ────" -ForegroundColor Cyan
        $env:PYTHONIOENCODING = "utf-8"
        if ($t.Name -eq "SLH_Daily_Digest") {
            & $PYTHON $t.Script --no-send
        } else {
            & $PYTHON $t.Script --verbose --no-alert
        }
    }
}

# ── Main ──
Write-Host ""
Write-Host "SLH Spark · Scheduled Tasks Manager" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════" -ForegroundColor Cyan

if ($List) {
    Show-List
    exit 0
}
if ($Uninstall) {
    Write-Host "`nUninstalling..." -ForegroundColor Yellow
    Uninstall-All
    Write-Host ""
    Show-List
    exit 0
}
if ($TestRun) {
    Write-Host "`nTest run (scripts execute once, no schedule change)..." -ForegroundColor Yellow
    Test-Run
    exit 0
}

# Default: install
Write-Host "`nInstalling..." -ForegroundColor Yellow
Install-All
Write-Host ""
Show-List
Write-Host "Done. Run with -List to verify state, -TestRun to dry-run, -Uninstall to remove." -ForegroundColor Cyan
Write-Host ""
