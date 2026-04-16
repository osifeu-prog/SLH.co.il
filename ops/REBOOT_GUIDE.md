# SLH Ecosystem - Reboot Guide
> Everything you need for a clean restart

## Auto-Start Setup (One-Time)

### Option 1: Windows Startup Folder (Recommended)
1. Press `Win+R`, type `shell:startup`, press Enter
2. Right-click → New → Shortcut
3. Location: `D:\SLH_ECOSYSTEM\ops\slh-startup.bat`
4. Name: `SLH Startup`
5. Done! Script runs automatically on login

### Option 2: Docker Desktop Auto-Start
1. Open Docker Desktop → Settings → General
2. Check ✅ "Start Docker Desktop when you sign in to Windows"
3. Docker containers with `restart: always` will auto-start

### Option 3: Task Scheduler (No login required)
1. Open Task Scheduler (`taskschd.msc`)
2. Create Basic Task → "SLH Startup"
3. Trigger: "At system startup"
4. Action: Start program → `D:\SLH_ECOSYSTEM\ops\slh-startup.bat`
5. Check "Run with highest privileges"

## Before Shutdown
```
Run: D:\SLH_ECOSYSTEM\ops\slh-shutdown.bat
```
This will:
- Log all container states
- Backup PostgreSQL database
- Stop Docker services gracefully

## After Reboot
If auto-start is set up, wait ~2 minutes after login. Otherwise:
```
Run: D:\SLH_ECOSYSTEM\ops\slh-startup.bat
```

## Manual Recovery Commands (PowerShell)
```powershell
# Start Docker services
cd D:\SLH_ECOSYSTEM
docker compose up -d

# Check all containers
docker ps --format "table {{.Names}}\t{{.Status}}"

# Check specific bot logs
docker logs slh-nfty --tail 20
docker logs slh-ton-mnh --tail 20

# Check Railway API
curl.exe -s https://slh-api-production.up.railway.app/api/health

# Restart a specific bot
docker compose restart slh-nfty
```

## Backup Anytime
```
Run: D:\SLH_ECOSYSTEM\ops\slh-backup.bat
```
Backups saved to: `D:\SLH_BACKUPS\backup_YYYYMMDD_HHMM\`
Auto-cleans: keeps last 10 backups

## Current Status (2026-04-08)
- ✅ 23/23 Docker containers running
- ✅ Railway API healthy
- ✅ PostgreSQL + Redis healthy
- ✅ All bot tokens verified
- ✅ slh-ton-mnh lock bug fixed
- ✅ slh-nfty token fixed
- ✅ Website live at slh-nft.com

## Logs Location
```
D:\SLH_ECOSYSTEM\ops\logs\
  startup_YYYYMMDD.log
  shutdown_YYYYMMDD.log
  db_shutdown_TIMESTAMP.sql
```

## Known Issues
- **NFTY Bot (tamagotchi at D:\SLH_BOTS)**: Cannot run simultaneously with Docker nfty-bot 
  (same bot token @NFTY_madness_bot). Choose one or regenerate token.
- **Windows PostgreSQL**: If installed locally, may conflict with Docker on port 5432.
  Fix: Stop Windows PostgreSQL service or change Docker port.
