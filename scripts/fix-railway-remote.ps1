# SLH Fix-Railway-Remote
# =======================
# The repo has remote "origin" pointing to slh-api.git (legacy).
# Railway watches osifeu-prog/SLH.co.il.git (branch: main).
# This script adds the missing remote and pushes there too.
#
# Usage: .\scripts\fix-railway-remote.ps1

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  SLH Fix Railway Remote" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

Set-Location D:\SLH_ECOSYSTEM

# --- Step 1: Show current remotes ---
Write-Host ""
Write-Host "Current remotes:" -ForegroundColor Yellow
git remote -v

# --- Step 2: Add the SLH.co.il remote if missing ---
$existing = git remote
if ($existing -contains "slhcoil") {
    Write-Host ""
    Write-Host "Remote 'slhcoil' already exists. Skipping add." -ForegroundColor Gray
} else {
    Write-Host ""
    Write-Host "Adding remote 'slhcoil' -> osifeu-prog/SLH.co.il.git" -ForegroundColor Cyan
    git remote add slhcoil https://github.com/osifeu-prog/SLH.co.il.git
    Write-Host "  OK" -ForegroundColor Green
}

# --- Step 3: Show updated remotes ---
Write-Host ""
Write-Host "Updated remotes:" -ForegroundColor Yellow
git remote -v

# --- Step 4: Fetch the SLH.co.il main branch ---
Write-Host ""
Write-Host "Fetching slhcoil..." -ForegroundColor Cyan
git fetch slhcoil 2>&1 | Out-String | Write-Host

# --- Step 5: Push master -> main (Railway watches "main") ---
Write-Host ""
Write-Host "Pushing master -> slhcoil/main (Railway will redeploy)..." -ForegroundColor Cyan
Write-Host ""
$confirm = Read-Host "Push? (y/N)"
if ($confirm -ne "y") {
    Write-Host "  Cancelled." -ForegroundColor Yellow
    exit 0
}

git push slhcoil master:main 2>&1 | Out-String | Write-Host
if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "  Push to slhcoil/main failed." -ForegroundColor Red
    Write-Host "  This may be because slhcoil/main has commits we don't have locally." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "  Recovery options:" -ForegroundColor Yellow
    Write-Host "    A) Force-push (overwrites slhcoil/main with master):" -ForegroundColor Yellow
    Write-Host "         git push slhcoil master:main --force" -ForegroundColor Gray
    Write-Host "    B) Pull slhcoil/main first, merge, then push:" -ForegroundColor Yellow
    Write-Host "         git fetch slhcoil" -ForegroundColor Gray
    Write-Host "         git merge slhcoil/main --allow-unrelated-histories" -ForegroundColor Gray
    Write-Host "         git push slhcoil master:main" -ForegroundColor Gray
    Write-Host ""
    $forceConfirm = Read-Host "Try option A (force-push)? (y/N)"
    if ($forceConfirm -eq "y") {
        git push slhcoil master:main --force
    } else {
        exit 1
    }
}

Write-Host ""
Write-Host "  OK: Pushed to SLH.co.il/main. Railway will redeploy in ~2 min." -ForegroundColor Green

# --- Step 6: Wait + verify ---
Write-Host ""
Write-Host "Waiting 120 seconds for Railway redeploy..." -ForegroundColor Yellow
for ($i = 120; $i -gt 0; $i -= 5) {
    Write-Host ("`r  Waiting... {0} sec  " -f $i) -NoNewline
    Start-Sleep -Seconds 5
}
Write-Host ""
Write-Host ""

Write-Host "Running verify-deployment.ps1..." -ForegroundColor Cyan
& "$PSScriptRoot\verify-deployment.ps1"
