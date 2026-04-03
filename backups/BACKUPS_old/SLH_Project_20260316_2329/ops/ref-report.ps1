param()
$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)

Write-Host "=== REFERRAL REPORT ===" -ForegroundColor Cyan

Write-Host "`n[1] invites rows" -ForegroundColor Cyan
psql -U postgres -d slh_db -c "SELECT id, inviter_user_id, invited_user_id, invite_code, created_at FROM invites ORDER BY id DESC LIMIT 50;"

Write-Host "`n[2] top inviters" -ForegroundColor Cyan
psql -U postgres -d slh_db -c "SELECT user_id, username, invited_count FROM users ORDER BY invited_count DESC, user_id ASC LIMIT 20;"

Write-Host "`n[3] recent invite audit" -ForegroundColor Cyan
psql -U postgres -d slh_db -c "SELECT id, user_id, event_type, payload_json, created_at FROM audit_log WHERE event_type LIKE 'invite.%' ORDER BY id DESC LIMIT 50;"