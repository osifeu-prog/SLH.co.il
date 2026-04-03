$db = [Environment]::GetEnvironmentVariable("DATABASE_URL")
if (-not $db) {
  Write-Error "DATABASE_URL is empty"
  exit 1
}

Write-Host "DATABASE_URL found" -ForegroundColor Green
psql $db -c "SELECT current_database(), current_user;"
psql $db -c "SELECT to_regclass('public.purchase_orders');"