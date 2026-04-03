param()
$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)

function Info([string]$m) { Write-Host $m -ForegroundColor Cyan }
function Good([string]$m) { Write-Host $m -ForegroundColor Green }
function Warn([string]$m) { Write-Host $m -ForegroundColor Yellow }

$stream = "slh:updates"

Info "`n=== REDIS STREAM HEALTH ==="

try {
  $exists = (docker exec slh_redis redis-cli --raw EXISTS $stream).Trim()
  $len    = (docker exec slh_redis redis-cli --raw XLEN $stream).Trim()
  $type   = (docker exec slh_redis redis-cli --raw TYPE $stream).Trim()

  $lastSeen  = (docker exec slh_redis redis-cli --raw GET slh:worker:last_seen_ts).Trim()
  $lastMsgId = (docker exec slh_redis redis-cli --raw GET slh:worker:last_msg_id).Trim()
  $processed = (docker exec slh_redis redis-cli --raw GET slh:worker:processed_total).Trim()
  $failed    = (docker exec slh_redis redis-cli --raw GET slh:worker:failed_total).Trim()

  Write-Host ("stream: " + $stream)
  Write-Host ("exists: " + $exists)
  Write-Host ("type: " + $type)
  Write-Host ("length: " + $len)
  Write-Host ("worker_last_seen_ts: " + $(if ($lastSeen) { $lastSeen } else { "-" }))
  Write-Host ("worker_last_msg_id: " + $(if ($lastMsgId) { $lastMsgId } else { "-" }))
  Write-Host ("worker_processed_total: " + $(if ($processed) { $processed } else { "0" }))
  Write-Host ("worker_failed_total: " + $(if ($failed) { $failed } else { "0" }))

  Write-Host ""
  Info "=== LAST 5 STREAM ENTRIES ==="
  docker exec slh_redis redis-cli XRANGE $stream - + COUNT 5
}
catch {
  Warn ("queue health failed: " + $_.Exception.Message)
  exit 1
}

Write-Host ""
Good "QUEUE_HEALTH_DONE"