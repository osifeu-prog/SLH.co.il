param()

$ErrorActionPreference = "Stop"
$ROOT = Split-Path -Parent $MyInvocation.MyCommand.Path
$ROOT = Split-Path -Parent $ROOT
Set-Location $ROOT

function Section([string]$t) {
  Write-Host ""
  Write-Host "======================================================================" -ForegroundColor DarkCyan
  Write-Host $t -ForegroundColor Cyan
  Write-Host "======================================================================" -ForegroundColor DarkCyan
}

function Run-PsqlText([string]$Sql) {
  $tmp = [System.IO.Path]::GetTempFileName()
  try {
    $enc = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($tmp, ($Sql -replace "`r`n","`n"), $enc)
    & psql -X -v ON_ERROR_STOP=1 -U postgres -d slh_db -f $tmp
    if ($LASTEXITCODE -ne 0) {
      throw "psql failed with exit code $LASTEXITCODE"
    }
  }
  finally {
    if (Test-Path $tmp) { Remove-Item $tmp -Force -ErrorAction SilentlyContinue }
  }
}

function Get-PsqlScalar([string]$Sql) {
  $result = & psql -X -t -A -v ON_ERROR_STOP=1 -U postgres -d slh_db -c $Sql
  if ($LASTEXITCODE -ne 0) {
    throw "psql scalar query failed with exit code $LASTEXITCODE"
  }
  return ($result | Out-String).Trim()
}

Section "SLH PROJECT V2 :: RECONCILIATION SMOKE"

Section "POSTGRES"
Run-PsqlText "SELECT now() AS db_now;"
Write-Host "OK postgres connection" -ForegroundColor Green

Section "LEDGER RECONCILIATION"
$ledgerSql = @"
WITH sums AS (
  SELECT
    COALESCE((SELECT SUM(available) FROM user_balances), 0)::numeric(20,8) AS user_balances_available,
    COALESCE((SELECT SUM(locked) FROM user_balances), 0)::numeric(20,8) AS user_balances_locked,
    COALESCE((SELECT SUM(balance)::numeric(20,8) FROM users), 0)::numeric(20,8) AS users_balance,
    COALESCE((SELECT SUM(ledger_available) FROM v_user_finance_snapshot), 0)::numeric(20,8) AS ledger_user_available,
    COALESCE((SELECT SUM(ledger_locked) FROM v_user_finance_snapshot), 0)::numeric(20,8) AS ledger_user_locked
)
SELECT *,
       (user_balances_available = users_balance) AS ok_user_vs_users,
       (user_balances_available = ledger_user_available) AS ok_user_vs_ledger_available,
       (user_balances_locked = ledger_user_locked) AS ok_locked_vs_ledger_locked
FROM sums;
"@
Run-PsqlText $ledgerSql
$ledgerBadSql = @"
WITH sums AS (
  SELECT
    COALESCE((SELECT SUM(available) FROM user_balances), 0)::numeric(20,8) AS user_balances_available,
    COALESCE((SELECT SUM(locked) FROM user_balances), 0)::numeric(20,8) AS user_balances_locked,
    COALESCE((SELECT SUM(balance)::numeric(20,8) FROM users), 0)::numeric(20,8) AS users_balance,
    COALESCE((SELECT SUM(ledger_available) FROM v_user_finance_snapshot), 0)::numeric(20,8) AS ledger_user_available,
    COALESCE((SELECT SUM(ledger_locked) FROM v_user_finance_snapshot), 0)::numeric(20,8) AS ledger_user_locked
)
SELECT CASE
  WHEN user_balances_available = users_balance
   AND user_balances_available = ledger_user_available
   AND user_balances_locked = ledger_user_locked
  THEN 0 ELSE 1 END AS bad
FROM sums;
"@
$ledgerBad = Get-PsqlScalar $ledgerBadSql
if ($ledgerBad -ne "0") { throw "Ledger reconciliation mismatch detected" }
Write-Host "OK ledger reconciliation" -ForegroundColor Green

Section "SNAPSHOT DRIFT"
$driftSql = @"
SELECT *
FROM v_user_finance_snapshot
WHERE delta_available <> 0 OR delta_locked <> 0;
"@
Run-PsqlText $driftSql
$driftCount = Get-PsqlScalar "SELECT COUNT(*) FROM v_user_finance_snapshot WHERE delta_available <> 0 OR delta_locked <> 0;"
if ($driftCount -ne "0") { throw "Snapshot drift detected: $driftCount rows" }
Write-Host "OK no finance snapshot drift" -ForegroundColor Green

Section "WITHDRAWAL RESERVATION SANITY"
$reservationSql = @"
WITH reservation_rows AS (
  SELECT
    wr.withdrawal_id,
    wr.status AS reservation_status,
    w.status AS withdrawal_status
  FROM withdrawal_reservations wr
  LEFT JOIN withdrawals w ON w.id = wr.withdrawal_id
),
summary AS (
  SELECT
    COUNT(*) FILTER (WHERE withdrawal_status IS NULL) AS orphan_reservations,
    COUNT(*) FILTER (WHERE reservation_status = 'consumed' AND withdrawal_status <> 'sent') AS consumed_not_sent,
    COUNT(*) FILTER (WHERE reservation_status = 'released' AND withdrawal_status NOT IN ('failed','rejected')) AS released_not_failed_or_rejected,
    COUNT(*) FILTER (WHERE reservation_status = 'reserved' AND withdrawal_status <> 'approved') AS reserved_not_approved
  FROM reservation_rows
)
SELECT * FROM summary;
"@
Run-PsqlText $reservationSql
$reservationBadSql = @"
WITH reservation_rows AS (
  SELECT
    wr.withdrawal_id,
    wr.status AS reservation_status,
    w.status AS withdrawal_status
  FROM withdrawal_reservations wr
  LEFT JOIN withdrawals w ON w.id = wr.withdrawal_id
),
summary AS (
  SELECT
    COUNT(*) FILTER (WHERE withdrawal_status IS NULL) AS orphan_reservations,
    COUNT(*) FILTER (WHERE reservation_status = 'consumed' AND withdrawal_status <> 'sent') AS consumed_not_sent,
    COUNT(*) FILTER (WHERE reservation_status = 'released' AND withdrawal_status NOT IN ('failed','rejected')) AS released_not_failed_or_rejected,
    COUNT(*) FILTER (WHERE reservation_status = 'reserved' AND withdrawal_status <> 'approved') AS reserved_not_approved
  FROM reservation_rows
)
SELECT CASE
  WHEN orphan_reservations = 0
   AND consumed_not_sent = 0
   AND released_not_failed_or_rejected = 0
   AND reserved_not_approved = 0
  THEN 0 ELSE 1 END AS bad
FROM summary;
"@
$reservationBad = Get-PsqlScalar $reservationBadSql
if ($reservationBad -ne "0") { throw "Withdrawal reservation sanity check failed" }
Write-Host "OK withdrawal reservation sanity" -ForegroundColor Green

Write-Host ""
Write-Host "RECON_SMOKE_OK" -ForegroundColor Green