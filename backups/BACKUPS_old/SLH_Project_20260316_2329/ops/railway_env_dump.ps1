$names = @(
  "RAILWAY_SERVICE_NAME",
  "DATABASE_URL",
  "DB_HOST",
  "DB_NAME",
  "DB_USER",
  "DB_PORT",
  "REDIS_URL",
  "WEBHOOK_URL"
)

foreach ($n in $names) {
  $v = [Environment]::GetEnvironmentVariable($n)
  Write-Host ($n + "=" + $v)
}