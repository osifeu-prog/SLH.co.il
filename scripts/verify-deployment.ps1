# SLH Deployment Verification (ASCII-safe)
# =========================================
# Run AFTER pushing code, to verify everything is alive.
# Usage: .\scripts\verify-deployment.ps1

param(
    [string]$ApiBase = "https://slhcoil-production.up.railway.app",
    [string]$WebBase = "https://slh-nft.com"
)

$ErrorActionPreference = "Continue"
$script:pass = 0
$script:fail = 0
$script:results = @()

function Test-Endpoint {
    param([string]$Name, [string]$Url, [string]$ExpectedKey)
    Write-Host ("  Testing {0}... " -f $Name) -NoNewline
    try {
        $r = Invoke-RestMethod -Uri $Url -Method GET -TimeoutSec 15 -ErrorAction Stop
        if ($ExpectedKey -and $r.PSObject.Properties.Name -notcontains $ExpectedKey) {
            Write-Host ("FAIL (no '{0}' in response)" -f $ExpectedKey) -ForegroundColor Red
            $script:fail++
            $script:results += @{name=$Name; status="FAIL"; reason="missing key $ExpectedKey"}
        } else {
            Write-Host "OK" -ForegroundColor Green
            $script:pass++
            $script:results += @{name=$Name; status="OK"}
        }
    } catch {
        Write-Host ("FAIL ({0})" -f $_.Exception.Message) -ForegroundColor Red
        $script:fail++
        $script:results += @{name=$Name; status="FAIL"; reason=$_.Exception.Message}
    }
}

function Test-Page {
    param([string]$Name, [string]$Url)
    Write-Host ("  Testing {0}... " -f $Name) -NoNewline
    try {
        $r = Invoke-WebRequest -Uri $Url -Method HEAD -TimeoutSec 15 -ErrorAction Stop -UseBasicParsing
        if ($r.StatusCode -eq 200) {
            Write-Host ("OK ({0})" -f $r.StatusCode) -ForegroundColor Green
            $script:pass++
            $script:results += @{name=$Name; status="OK"}
        } else {
            Write-Host ("FAIL ({0})" -f $r.StatusCode) -ForegroundColor Red
            $script:fail++
        }
    } catch {
        Write-Host ("FAIL ({0})" -f $_.Exception.Message) -ForegroundColor Red
        $script:fail++
    }
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  SLH Deployment Verification" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ("  API Base: {0}" -f $ApiBase)
Write-Host ("  Web Base: {0}" -f $WebBase)
Write-Host ""

Write-Host "Phase 1: API Endpoints (no auth)" -ForegroundColor Yellow
Test-Endpoint "Health"               "$ApiBase/api/health"           "ok"
Test-Endpoint "System Status"        "$ApiBase/api/system/status"    "ok"
Test-Endpoint "Bots Status"          "$ApiBase/api/system/bots"      "bots"
Test-Endpoint "System Stats"         "$ApiBase/api/system/stats"     ""
Test-Endpoint "Courses Catalog"      "$ApiBase/api/courses/"         "items"

Write-Host ""
Write-Host "Phase 2: Web Pages (HTTP 200)" -ForegroundColor Yellow
Test-Page "Home"                "$WebBase/"
Test-Page "Landing v2"          "$WebBase/landing-v2.html"
Test-Page "Command Center"      "$WebBase/command-center.html"
Test-Page "Investor Engine"     "$WebBase/investor-engine.html"
Test-Page "Investor Portal"     "$WebBase/investor-portal.html"
Test-Page "Course AI Tokens"    "$WebBase/course-ai-tokens.html"
Test-Page "Disclosure"          "$WebBase/disclosure.html"
Test-Page "NFT Cards"           "$WebBase/nft-cards.html"

Write-Host ""
Write-Host "Phase 3: Migrated Pages" -ForegroundColor Yellow
Test-Page "About"               "$WebBase/about.html"
Test-Page "Wallet"              "$WebBase/wallet.html"
Test-Page "Admin"               "$WebBase/admin.html"

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
$resColor = if ($script:fail -eq 0) { "Green" } else { "Yellow" }
Write-Host ("  Results: {0} passed, {1} failed" -f $script:pass, $script:fail) -ForegroundColor $resColor
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

if ($script:fail -gt 0) {
    Write-Host "Failures:" -ForegroundColor Red
    $script:results | Where-Object { $_.status -eq "FAIL" } | ForEach-Object {
        Write-Host ("  - {0}: {1}" -f $_.name, $_.reason) -ForegroundColor Red
    }
    Write-Host ""
    Write-Host "Common causes:" -ForegroundColor Yellow
    Write-Host "  - Code not pushed yet (run git push)"
    Write-Host "  - Railway hasn't redeployed (wait 2 min, retry)"
    Write-Host "  - GitHub Pages hasn't published (wait 2 min, retry)"
    Write-Host "  - Missing Railway env vars (see SECURITY_FIX_PLAN.md)"
    exit 1
}

Write-Host "All checks passed. Safe to broadcast." -ForegroundColor Green
exit 0
