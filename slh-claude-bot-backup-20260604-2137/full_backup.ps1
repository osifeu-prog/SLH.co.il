$timestamp = Get-Date -Format "yyyyMMdd-HHmm"
$backupDir = "D:\slh-website\slh-claude-bot\backups"
$zipName = "$backupDir\full_backup_$timestamp.zip"

# Create ZIP containing bot.py + investor-landing
Compress-Archive -Path "D:\slh-website\slh-claude-bot\bot.py", "D:\investor-landing\*" -DestinationPath $zipName -Force
Write-Host "Backup created: $zipName"
