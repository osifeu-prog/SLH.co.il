Write-Host ""
Write-Host "=== SLH LIVE EVENTS ===" -ForegroundColor Cyan
Write-Host ""

Get-Content logs\events\runtime_events.jsonl -Wait
