Start-Sleep -Seconds 30

Set-Location D:\SLH_PROJECT_V2

docker compose up -d

Start-Process powershell -WindowStyle Hidden -ArgumentList "-ExecutionPolicy Bypass -File D:\SLH_PROJECT_V2\ops\start-core.ps1"