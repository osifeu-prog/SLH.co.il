param(
  [int]$MaxAttempts = 24,
  [int]$SleepSeconds = 10
)

$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)

$baseUrl = & ".\ops\get-tunnel-url.ps1"
if (-not $baseUrl) { throw "Tunnel URL is empty" }

$healthUrl = "$baseUrl/healthz"

Write-Host "Waiting for tunnel readiness: $baseUrl" -ForegroundColor Cyan

for ($i = 1; $i -le $MaxAttempts; $i++) {
  Write-Host "Attempt $i/$MaxAttempts ..." -ForegroundColor Yellow

  $dnsOk = $false
  $httpOk = $false

  try {
    $hostName = ([uri]$baseUrl).Host
    Resolve-DnsName $hostName -ErrorAction Stop | Out-Null
    $dnsOk = $true
    Write-Host "DNS OK" -ForegroundColor Green
  } catch {
    Write-Host "DNS not ready yet" -ForegroundColor DarkYellow
  }

  try {
    $r = Invoke-WebRequest -Uri $healthUrl -UseBasicParsing -TimeoutSec 10
    if ($r.StatusCode -ge 200 -and $r.StatusCode -lt 499) {
      $httpOk = $true
      Write-Host ("HTTP OK: " + $r.StatusCode) -ForegroundColor Green
    }
  } catch {
    Write-Host "HTTP not ready yet" -ForegroundColor DarkYellow
  }

  if ($dnsOk -and $httpOk) {
    Write-Host "TUNNEL_READY_OK" -ForegroundColor Green
    exit 0
  }

  Start-Sleep -Seconds $SleepSeconds
}

throw "Tunnel did not become ready in time: $baseUrl"