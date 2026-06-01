param(
    [string]$Type = "manual_test"
)

$event = @{
    timestamp = (Get-Date).ToString("s")
    event_type = $Type
    source = "powershell"
    severity = "INFO"
} | ConvertTo-Json -Compress

Add-Content logs\events\runtime_events.jsonl $event

Write-Host "EVENT EMITTED: $Type" -ForegroundColor Yellow
