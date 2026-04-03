param()

$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)

$logFile = Join-Path (Get-Location) "logs\tunnel.console.log"
if (-not (Test-Path $logFile)) {
  throw "tunnel log not found: $logFile"
}

$txt = Get-Content $logFile -Raw
$m = [regex]::Match($txt, 'https://[-a-z0-9]+\.trycloudflare\.com')

if ($m.Success) {
  Write-Output $m.Value
} else {
  throw "No trycloudflare URL found in tunnel log"
}