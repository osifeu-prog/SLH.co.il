param()

$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)

$baseUrl = & ".\ops\get-tunnel-url.ps1"
if (-not $baseUrl) { throw "Tunnel URL is empty" }

& ".\ops\wait-tunnel-ready.ps1"

Write-Host "Using tunnel URL: $baseUrl" -ForegroundColor Cyan

$ok = $false
$lastErr = $null

for ($i = 1; $i -le 18; $i++) {
  try {
    & ".\ops\set-webhook.ps1" -BaseUrl $baseUrl
    $ok = $true
    break
  } catch {
    $lastErr = $_
    Write-Host "set-webhook attempt $i failed; retrying in 10s..." -ForegroundColor Yellow
    Start-Sleep -Seconds 10
  }
}

if (-not $ok) {
  throw $lastErr
}

Write-Host "SET_WEBHOOK_FROM_TUNNEL_OK" -ForegroundColor Green