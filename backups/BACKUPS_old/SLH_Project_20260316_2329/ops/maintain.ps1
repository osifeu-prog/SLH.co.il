Write-Host ""
Write-Host "SLH BOT MAINTENANCE"

.\ops\stop.ps1
.\ops\backup.ps1
.\ops\snapshot.ps1
.\ops\status.ps1
.\ops\start.ps1
