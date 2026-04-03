param()
$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)

Write-Host "=== DB REPORT ===" -ForegroundColor Cyan

Write-Host "`n[1] users count" -ForegroundColor Cyan
psql -U postgres -d slh_db -c "SELECT COUNT(*) AS users_count FROM users;"

Write-Host "`n[2] balances totals" -ForegroundColor Cyan
psql -U postgres -d slh_db -c "SELECT COUNT(*) AS balance_rows, COALESCE(SUM(available),0) AS total_available, COALESCE(SUM(locked),0) AS total_locked FROM user_balances;"

Write-Host "`n[3] claims totals" -ForegroundColor Cyan
psql -U postgres -d slh_db -c "SELECT COUNT(*) AS claims_count, COALESCE(SUM(amount),0) AS claims_total_amount FROM claims;"

Write-Host "`n[4] top balances" -ForegroundColor Cyan
psql -U postgres -d slh_db -c "SELECT u.user_id, u.username, ub.available, ub.locked FROM user_balances ub JOIN users u ON u.user_id = ub.user_id ORDER BY ub.available DESC, u.user_id ASC LIMIT 10;"

Write-Host "`n[5] referral rewards" -ForegroundColor Cyan
psql -U postgres -d slh_db -c "SELECT id, inviter_user_id, invited_user_id, invite_code, reward_granted, created_at FROM invites ORDER BY id DESC LIMIT 50;"

Write-Host "`n[6] recent audit" -ForegroundColor Cyan
psql -U postgres -d slh_db -c "SELECT id, user_id, event_type, created_at FROM audit_log ORDER BY id DESC LIMIT 30;"