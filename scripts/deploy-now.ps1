# SLH Deploy-Now (ASCII-safe for Windows PowerShell 5.x)
# ========================================================
# Usage:
#     cd D:\SLH_ECOSYSTEM
#     .\scripts\deploy-now.ps1
#
# Steps: push API repo, push website repo, wait, run verify-deployment.

$ErrorActionPreference = "Stop"

function Step {
    param([int]$n, [string]$msg)
    Write-Host ""
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host ("  STEP {0} -- {1}" -f $n, $msg) -ForegroundColor Cyan
    Write-Host "============================================================" -ForegroundColor Cyan
}

# --- Step 1: Push API repo (root) ---
Step 1 "Push API repo (root)"
Set-Location D:\SLH_ECOSYSTEM

Write-Host "  Files staged:" -ForegroundColor Gray
git status --short

Write-Host ""
$confirm = Read-Host "  Continue with API push? (y/N)"
if ($confirm -ne "y") {
    Write-Host "  Cancelled." -ForegroundColor Yellow
    exit 0
}

git add -A
$msg1 = @"
feat: control layer + investor engine + content marketplace + AI optimizer

- New routers: system_status, investor_engine, courses, esp_events
- AI Optimizer module with prompt caching (shared/ai_optimizer.py)
- Claude bot system prompt: 520 -> 360 tokens (-31%) + cache_control enabled
- Orchestrator script for local Docker control
- Verify + analyze scripts for ongoing maintenance
- Updated CLAUDE.md (230 endpoints, 11765 lines, 140 pages, 3 repos)
"@
git commit -m $msg1
git push origin master
if ($LASTEXITCODE -ne 0) {
    Write-Host "  ERROR: Push failed. Check git remote / auth." -ForegroundColor Red
    exit 1
}
Write-Host "  OK: API pushed" -ForegroundColor Green

# --- Step 2: Push website repo ---
Step 2 "Push website repo"
Set-Location D:\SLH_ECOSYSTEM\website

Write-Host "  Files staged:" -ForegroundColor Gray
git status --short

Write-Host ""
$confirm2 = Read-Host "  Continue with website push? (y/N)"
if ($confirm2 -ne "y") {
    Write-Host "  Cancelled." -ForegroundColor Yellow
    exit 0
}

git add -A
$msg2 = @"
feat: Command Center + Investor Engine UI + Course Marketplace + Neural migration

- New pages: command-center, investor-engine, investor-portal, course-ai-tokens, disclosure, landing-v2, nft-cards
- Design system: css/slh-neural.css (DNA + Neural Network theme)
- Migrated to Neural theme: index, about, wallet, admin
- Theme picker now includes Neural (8 themes total)
"@
git commit -m $msg2
git push origin main
if ($LASTEXITCODE -ne 0) {
    Write-Host "  ERROR: Push failed. Check git remote / auth." -ForegroundColor Red
    exit 1
}
Write-Host "  OK: Website pushed" -ForegroundColor Green

# --- Step 3: Wait for Railway + GitHub Pages ---
Step 3 "Wait 90 seconds for Railway redeploy + GitHub Pages publish"
for ($i = 90; $i -gt 0; $i--) {
    Write-Host ("`r  Waiting... {0} sec  " -f $i) -NoNewline
    Start-Sleep -Seconds 1
}
Write-Host ""

# --- Step 4: Verify deployment ---
Step 4 "Verify deployment"
Set-Location D:\SLH_ECOSYSTEM
& "$PSScriptRoot\verify-deployment.ps1"

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "============================================================" -ForegroundColor Green
    Write-Host "  DEPLOYED + VERIFIED. Open Morning Report:" -ForegroundColor Green
    Write-Host "  D:\SLH_ECOSYSTEM\ops\MORNING_REPORT_2026-04-28.md" -ForegroundColor Green
    Write-Host "============================================================" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "  WARNING: Some checks failed. Common causes:" -ForegroundColor Yellow
    Write-Host "    - Railway hasn't redeployed yet (wait 2 more min, retry)"
    Write-Host "    - Missing env vars on Railway (JWT_SECRET, ADMIN_API_KEYS)"
    Write-Host "    - GitHub Pages still building (wait + retry)"
}
