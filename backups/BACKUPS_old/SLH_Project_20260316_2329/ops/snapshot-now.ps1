param()

$ErrorActionPreference="Stop"

$stamp=Get-Date -Format "yyyyMMdd_HHmmss"
$dst=".\\state\\snapshot_$stamp"

New-Item -ItemType Directory -Force -Path $dst | Out-Null

git rev-parse HEAD | Out-File "$dst\\git_head.txt" -Encoding utf8
git log --oneline -n 20 | Out-File "$dst\\git_log.txt" -Encoding utf8
git status --short | Out-File "$dst\\git_status.txt" -Encoding utf8

Copy-Item .\\worker.py "$dst\\worker.py"
Copy-Item .\\webhook_server.py "$dst\\webhook_server.py"
Copy-Item .\\app\\handlers\\purchases.py "$dst\\purchases.py"
Copy-Item .\\app\\i18n.py "$dst\\i18n.py"

Write-Host ""
Write-Host "Snapshot saved to $dst" -ForegroundColor Green