# SLH Wake-Up Script
# ===================
# Run this when you wake up to see exactly where things stand.
# It does NOT change anything — it only shows you the current state.

$ErrorActionPreference = "Continue"

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  Good morning, Osif." -ForegroundColor Cyan
Write-Host "  Here is the state of your system." -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# --- Run verify-deployment ---
Write-Host "Running deployment check..." -ForegroundColor Yellow
& "$PSScriptRoot\verify-deployment.ps1"

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  Quick links to open" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Morning Report (start here):" -ForegroundColor Yellow
Write-Host "    D:\SLH_ECOSYSTEM\ops\MORNING_REPORT_2026-04-28.md"
Write-Host ""
Write-Host "  Live pages:" -ForegroundColor Yellow
Write-Host "    https://slh-nft.com/command-center.html       (Unified control)"
Write-Host "    https://slh-nft.com/investor-engine.html      (Financial admin)"
Write-Host "    https://slh-nft.com/investor-portal.html      (For investors)"
Write-Host "    https://slh-nft.com/course-ai-tokens.html     (First product)"
Write-Host "    https://slh-nft.com/disclosure.html           (Legal disclosure)"
Write-Host "    https://slh-nft.com/landing-v2.html           (Investor landing)"
Write-Host ""
Write-Host "  API health:" -ForegroundColor Yellow
Write-Host "    https://slhcoil-production.up.railway.app/api/health"
Write-Host ""
Write-Host "  Tomorrow's task: Talk to your investors honestly." -ForegroundColor Yellow
Write-Host "    Read: D:\SLH_ECOSYSTEM\ops\INVESTOR_UPDATE_DRAFT.md"
Write-Host ""
Write-Host "  Open the Morning Report now:"
Write-Host '    notepad "D:\SLH_ECOSYSTEM\ops\MORNING_REPORT_2026-04-28.md"' -ForegroundColor Gray
Write-Host ""

# Try to open the morning report automatically
$morningReport = "D:\SLH_ECOSYSTEM\ops\MORNING_REPORT_2026-04-28.md"
if (Test-Path $morningReport) {
    $auto = Read-Host "Open Morning Report now? (Y/n)"
    if ($auto -ne "n") {
        Start-Process notepad.exe -ArgumentList "`"$morningReport`""
    }
}
