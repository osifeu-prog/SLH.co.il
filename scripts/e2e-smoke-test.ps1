#
# SLH E2E Smoke Test v1.0
# Validates core endpoints with clear pass/fail per track.
#
# Usage: .\scripts\e2e-smoke-test.ps1 [-AdminKey "slh2026admin"]
#

param(
  [string]$ApiBase = "https://slh-api-production.up.railway.app",
  [string]$AdminKey = "slh2026admin",
  [int]$TestUserId = 224223270
)

$ErrorActionPreference = "Continue"
$script:pass = 0
$script:fail = 0
$script:fails = @()

function Test-Endpoint {
  param(
    [string]$Track,
    [string]$Name,
    [string]$Method = "GET",
    [string]$Url,
    [hashtable]$Headers = @{},
    [object]$Body = $null,
    [string]$ExpectKey = $null,
    [int[]]$OkStatus = @(200, 201)
  )
  $full = "$ApiBase$Url"
  Write-Host ""
  Write-Host "[$Track] $Name" -ForegroundColor Cyan
  Write-Host "  $Method $Url"
  try {
    $params = @{
      Method  = $Method
      Uri     = $full
      Headers = $Headers
      TimeoutSec = 15
    }
    if ($Body) {
      $params.Body = ($Body | ConvertTo-Json -Depth 10)
      $params.ContentType = "application/json"
    }
    $r = Invoke-WebRequest @params -UseBasicParsing
    if ($OkStatus -contains $r.StatusCode) {
      if ($ExpectKey) {
        $json = $r.Content | ConvertFrom-Json
        if ($json.PSObject.Properties.Name -contains $ExpectKey) {
          Write-Host "  PASS · $($r.StatusCode) · found '$ExpectKey'" -ForegroundColor Green
          $script:pass++
          return $json
        } else {
          Write-Host "  FAIL · '$ExpectKey' missing" -ForegroundColor Red
          $script:fail++
          $script:fails += "[$Track] $Name"
          return $null
        }
      }
      Write-Host "  PASS · $($r.StatusCode)" -ForegroundColor Green
      $script:pass++
      return ($r.Content | ConvertFrom-Json -ErrorAction SilentlyContinue)
    } else {
      Write-Host "  FAIL · status $($r.StatusCode)" -ForegroundColor Red
      $script:fail++
      $script:fails += "[$Track] $Name"
    }
  } catch {
    $status = try { $_.Exception.Response.StatusCode.Value__ } catch { "ERR" }
    Write-Host "  FAIL · $status · $($_.Exception.Message.Split("`n")[0])" -ForegroundColor Red
    $script:fail++
    $script:fails += "[$Track] $Name"
  }
  return $null
}

Write-Host "========================================"
Write-Host "  SLH E2E SMOKE TEST"
Write-Host "  Target: $ApiBase"
Write-Host "  Admin key: $($AdminKey.Substring(0,[Math]::Min(6,$AdminKey.Length)))..."
Write-Host "========================================"

$adminHeaders = @{ "X-Admin-Key" = $AdminKey }

# Track 1: Health + Users
Test-Endpoint "T1" "Health check" -Url "/api/health" -ExpectKey "status"
Test-Endpoint "T1" "User info" -Url "/api/user/$TestUserId" -ExpectKey "telegram_id"
Test-Endpoint "T1" "Admin users list" -Url "/api/admin/users" -Headers $adminHeaders

# Track 2: Community + RSS
Test-Endpoint "T2" "Community posts" -Url "/api/community/posts"
Test-Endpoint "T2" "Community RSS" -Url "/api/community/rss"

# Track 3: Tokens + Balances
Test-Endpoint "T3" "Token SLH info" -Url "/api/tokens/SLH"
Test-Endpoint "T3" "User balances" -Url "/api/user/$TestUserId/balances"

# Track 4: Payments + Broadcast
Test-Endpoint "T4" "Payment providers list" -Url "/api/payments/providers"
Test-Endpoint "T4" "Broadcast history" -Url "/api/broadcast/history" -Headers $adminHeaders

# Track 5: Sudoku + Dating
Test-Endpoint "T5" "Sudoku daily" -Url "/api/sudoku/daily"
Test-Endpoint "T5" "Dating profile (gated)" -Url "/api/dating/profile/$TestUserId"

# Track 6: Experts + ESP
Test-Endpoint "T6" "Experts list" -Url "/api/experts"
Test-Endpoint "T6" "ESP registry" -Url "/api/esp/devices" -Headers $adminHeaders

Write-Host ""
Write-Host "========================================"
Write-Host "  RESULTS"
Write-Host "========================================"
Write-Host "  PASS: $script:pass" -ForegroundColor Green
Write-Host "  FAIL: $script:fail" -ForegroundColor $(if ($script:fail -eq 0) { "Green" } else { "Red" })
if ($script:fails.Count -gt 0) {
  Write-Host ""
  Write-Host "  Failed tests:"
  foreach ($f in $script:fails) { Write-Host "    - $f" -ForegroundColor Yellow }
}
Write-Host ""
if ($script:fail -eq 0) {
  Write-Host "  STATUS: ALL GREEN" -ForegroundColor Green
  exit 0
} else {
  Write-Host "  STATUS: FAILURES DETECTED" -ForegroundColor Red
  exit 1
}
