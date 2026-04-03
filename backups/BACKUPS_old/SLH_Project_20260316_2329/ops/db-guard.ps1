param()

$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)

Write-Host "`n=== DB GUARD :: CHECK TABLES ===" -ForegroundColor Cyan

$checkSql = @"
SELECT table_schema || '.' || table_name
FROM information_schema.tables
WHERE table_schema NOT IN ('pg_catalog','information_schema')
ORDER BY table_schema, table_name;
"@

$tablesText = $checkSql | docker exec -i slhb_postgres psql -U slh_user -d slh_database -At
$tables = @()
if ($tablesText) {
    $tables = $tablesText -split "`n" | Where-Object { $_.Trim() -ne "" }
}

if ($tables.Count -eq 0) {
    Write-Host "No app tables found. Commerce schema likely not applied." -ForegroundColor Yellow
} else {
    $tables | ForEach-Object { Write-Host $_ }
}

Write-Host "`n=== DB GUARD :: CHECK COMMERCE TABLES ===" -ForegroundColor Cyan

$required = @(
    "public.system_settings",
    "public.products",
    "public.product_groups",
    "public.purchase_orders"
)

$missing = @()
foreach ($name in $required) {
    if ($tables -notcontains $name) {
        $missing += $name
    }
}

if ($missing.Count -gt 0) {
    Write-Host "Missing tables:" -ForegroundColor Red
    $missing | ForEach-Object { Write-Host " - $_" -ForegroundColor Red }

    Write-Host "`n=== APPLY COMMERCE SQL PATCHES ===" -ForegroundColor Yellow
    Get-Content .\ops\sql\patch_commerce_foundation_v1.sql -Raw | docker exec -i slhb_postgres psql -U slh_user -d slh_database -v ON_ERROR_STOP=1
    Get-Content .\ops\sql\patch_commerce_groups_and_flags_v1.sql -Raw | docker exec -i slhb_postgres psql -U slh_user -d slh_database -v ON_ERROR_STOP=1
    Get-Content .\ops\sql\patch_commerce_product_controls_v1.sql -Raw | docker exec -i slhb_postgres psql -U slh_user -d slh_database -v ON_ERROR_STOP=1
    Get-Content .\ops\sql\patch_purchase_receipts_v1.sql -Raw | docker exec -i slhb_postgres psql -U slh_user -d slh_database -v ON_ERROR_STOP=1
    Get-Content .\ops\sql\patch_commerce_events_v1.sql -Raw | docker exec -i slhb_postgres psql -U slh_user -d slh_database -v ON_ERROR_STOP=1
    Get-Content .\ops\sql\seed_products_v1.sql -Raw | docker exec -i slhb_postgres psql -U slh_user -d slh_database -v ON_ERROR_STOP=1

    Write-Host "`n=== RECHECK TABLES ===" -ForegroundColor Cyan
    $checkSql | docker exec -i slhb_postgres psql -U slh_user -d slh_database -At
} else {
    Write-Host "Commerce tables already exist." -ForegroundColor Green
}

Write-Host "`n=== CHECK SETTINGS ===" -ForegroundColor Cyan
@"
SELECT key, value_text
FROM system_settings
WHERE key LIKE '%commerce%'
   OR key LIKE '%store%'
   OR key LIKE '%purchase%'
ORDER BY key;
"@ | docker exec -i slhb_postgres psql -U slh_user -d slh_database

Write-Host "`n=== CHECK PRODUCTS ===" -ForegroundColor Cyan
@"
SELECT code, title, price_amount, price_currency, is_active, is_visible
FROM products
ORDER BY id;
"@ | docker exec -i slhb_postgres psql -U slh_user -d slh_database