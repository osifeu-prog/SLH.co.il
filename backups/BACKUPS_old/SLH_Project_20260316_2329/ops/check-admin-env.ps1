$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)

Write-Host "=== ADMIN ENV CHECK ===" -ForegroundColor Cyan
Get-Content .\.env | Select-String '^ADMIN_USER_ID='

Write-Host "`n=== PYTHON ADMIN CHECK ===" -ForegroundColor Cyan
.\venv\Scripts\python.exe -c "from dotenv import load_dotenv; load_dotenv(); from app.core.admin_guard import ADMIN_USER_ID; print(f'ADMIN OK: {ADMIN_USER_ID}')"