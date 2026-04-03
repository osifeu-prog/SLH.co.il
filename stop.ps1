# SLH ECOSYSTEM - Stop all services
Set-Location $PSScriptRoot
Write-Host "Stopping SLH Ecosystem..." -ForegroundColor Yellow
docker compose down
Write-Host "All services stopped." -ForegroundColor Green
