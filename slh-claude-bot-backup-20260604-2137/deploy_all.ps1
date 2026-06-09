cd D:\investor-landing
Write-Host "Running PRO deploy..."
git add .
git commit -m "Deploy via bot $(Get-Date -Format yyyyMMdd-HHmm)"
git push
Write-Host "Deploy complete."
