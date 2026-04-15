# SLH Ecosystem - Windows Defender Optimization
# Run as Administrator: powershell -ExecutionPolicy Bypass -File defender-fix.ps1
# Fixes: MsMpEng eating CPU because it scans Docker volumes + bot logs continuously

Write-Host "=== SLH Defender Optimization ===" -ForegroundColor Cyan
Write-Host ""

# 1. Stop any running scan
Write-Host "[1/5] Stopping current Defender scan..." -ForegroundColor Yellow
try {
    Stop-MpScan -ErrorAction SilentlyContinue
    Write-Host "  -> OK" -ForegroundColor Green
} catch {
    Write-Host "  -> No active scan to stop" -ForegroundColor Gray
}

# 2. Add SLH project paths to exclusions
Write-Host "[2/5] Adding SLH paths to Defender exclusions..." -ForegroundColor Yellow
$paths = @(
    "D:\SLH_ECOSYSTEM",
    "D:\SLH_ECOSYSTEM\backups",
    "D:\SLH_ECOSYSTEM\logs",
    "D:\SLH_ECOSYSTEM\venv_shared",
    "D:\SLH_ECOSYSTEM\__pycache__",
    "C:\ProgramData\Docker",
    "C:\Users\Giga Store\.docker",
    "C:\Users\Giga Store\AppData\Local\Docker"
)
foreach ($p in $paths) {
    try {
        Add-MpPreference -ExclusionPath $p -ErrorAction SilentlyContinue
        Write-Host "  -> Added: $p" -ForegroundColor Green
    } catch {
        Write-Host "  -> Skipped (already excluded?): $p" -ForegroundColor Gray
    }
}

# 3. Add process exclusions (Docker, Python, Node)
Write-Host "[3/5] Adding process exclusions..." -ForegroundColor Yellow
$processes = @("python.exe", "node.exe", "docker.exe", "Docker Desktop.exe", "claude.exe")
foreach ($proc in $processes) {
    try {
        Add-MpPreference -ExclusionProcess $proc -ErrorAction SilentlyContinue
        Write-Host "  -> Added: $proc" -ForegroundColor Green
    } catch {
        Write-Host "  -> Skipped: $proc" -ForegroundColor Gray
    }
}

# 4. Lower scan throttle (max 30% CPU during scans)
Write-Host "[4/5] Limiting Defender CPU usage to 30%..." -ForegroundColor Yellow
Set-MpPreference -ScanAvgCPULoadFactor 30
Write-Host "  -> Scan CPU throttled to 30%" -ForegroundColor Green

# 5. Schedule scans for night (3 AM daily)
Write-Host "[5/5] Scheduling Defender scans for 3 AM..." -ForegroundColor Yellow
Set-MpPreference -ScanScheduleTime 03:00:00
Set-MpPreference -ScanScheduleDay Everyday
Write-Host "  -> Scans scheduled for 3:00 AM daily" -ForegroundColor Green

Write-Host ""
Write-Host "=== Done ===" -ForegroundColor Cyan
Write-Host "Recommended: restart MsMpEng to apply changes:" -ForegroundColor Yellow
Write-Host "  Restart-Service -Name WinDefend -Force" -ForegroundColor White
Write-Host ""
Write-Host "Verify exclusions: Get-MpPreference | Select-Object ExclusionPath" -ForegroundColor Gray
