# Windows Task Scheduler Setup — SLH Automation
**Date:** 2026-04-21
**Purpose:** Schedule `daily_backtest.py` + `telegram_push_alerts.py` to run automatically on Osif's dev machine.

---

## Overview

Two tasks need automation:

| Task | Script | Frequency | Output |
|---|---|---|---|
| **Backtest snapshot** | `D:\SLH_ECOSYSTEM\daily_backtest.py` | Every 6 hours | `backtest_YYYYMMDD_HHMMSS.csv` in project root |
| **Telegram digest** | `D:\SLH_ECOSYSTEM\ops\telegram_push_alerts.py` | Daily at 09:00 | DM to Osif's chat_id (224223270) |
| **Health check** | Same script, `--mode health` | Every 30 min | Silent when ok, alert when down |

---

## Task 1: Daily Backtest (every 6 hours)

### Via PowerShell (run once as Admin):

```powershell
$action = New-ScheduledTaskAction -Execute 'python.exe' `
  -Argument 'D:\SLH_ECOSYSTEM\daily_backtest.py' `
  -WorkingDirectory 'D:\SLH_ECOSYSTEM'

$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date).Date.AddHours(6) `
  -RepetitionInterval (New-TimeSpan -Hours 6)

$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable `
  -DontStopOnIdleEnd -RestartCount 2 -RestartInterval (New-TimeSpan -Minutes 5)

Register-ScheduledTask -TaskName 'SLH_Daily_Backtest' `
  -Action $action -Trigger $trigger -Settings $settings `
  -Description 'Fetch BSC token prices and save to backtest_*.csv' `
  -User $env:USERNAME -RunLevel Highest
```

### Verify:
```powershell
Get-ScheduledTask -TaskName 'SLH_Daily_Backtest' | Select-Object State,TaskName
Get-ScheduledTaskInfo -TaskName 'SLH_Daily_Backtest' | Select-Object LastRunTime,LastTaskResult,NextRunTime
```

### Manual test first:
```powershell
cd D:\SLH_ECOSYSTEM
python daily_backtest.py
# Should produce backtest_YYYYMMDD_HHMMSS.csv with ~30 rows
```

---

## Task 2: Telegram Digest (daily 09:00)

### Prerequisites
Ensure `D:/SLH_ECOSYSTEM/.env` contains:
```
BROADCAST_BOT_TOKEN=<bot token of @SLH_AIR_bot>
```
(Already present per existing `.env`.)

### Via PowerShell (run once as Admin):

```powershell
$action = New-ScheduledTaskAction -Execute 'python.exe' `
  -Argument 'D:\SLH_ECOSYSTEM\ops\telegram_push_alerts.py --chat-id 224223270 --mode digest' `
  -WorkingDirectory 'D:\SLH_ECOSYSTEM'

$trigger = New-ScheduledTaskTrigger -Daily -At '09:00'

$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -DontStopOnIdleEnd

Register-ScheduledTask -TaskName 'SLH_Telegram_Digest' `
  -Action $action -Trigger $trigger -Settings $settings `
  -Description 'Daily performance digest sent to Osif via @SLH_AIR_bot' `
  -User $env:USERNAME -RunLevel Highest
```

### Manual test first:
```powershell
python D:\SLH_ECOSYSTEM\ops\telegram_push_alerts.py --chat-id 224223270 --mode digest
# You should receive a Telegram DM from @SLH_AIR_bot with the performance summary
```

---

## Task 3: Health Check (every 30 min)

```powershell
$action = New-ScheduledTaskAction -Execute 'python.exe' `
  -Argument 'D:\SLH_ECOSYSTEM\ops\telegram_push_alerts.py --chat-id 224223270 --mode health' `
  -WorkingDirectory 'D:\SLH_ECOSYSTEM'

$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date) `
  -RepetitionInterval (New-TimeSpan -Minutes 30)

$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable

Register-ScheduledTask -TaskName 'SLH_Health_Check' `
  -Action $action -Trigger $trigger -Settings $settings `
  -Description 'Alerts Osif if Railway API is down (silent when OK)' `
  -User $env:USERNAME -RunLevel Highest
```

**Silent when OK, alerts on degradation.** State persists between runs in `~/.slh_push_state.json`.

---

## Monitoring & Logs

### View task run history:
```powershell
Get-ScheduledTaskInfo -TaskName 'SLH_*' | Select-Object TaskName,LastRunTime,LastTaskResult,NumberOfMissedRuns
```

### Check Telegram send state:
```powershell
cat "$env:USERPROFILE\.slh_push_state.json"
# {"last_event_id": 42}
```

### Stream output to log file:
Edit the task to redirect:
```powershell
python.exe ... > D:\SLH_ECOSYSTEM\logs\scheduler_YYYYMMDD.log 2>&1
```

---

## Disable / Remove

```powershell
# Stop + remove all 3
Get-ScheduledTask -TaskName 'SLH_*' | Unregister-ScheduledTask -Confirm:$false
```

---

## Troubleshooting

### "Python.exe not found"
- Add Python to system PATH, or use full path: `C:\Python310\python.exe`

### "Access denied" when registering
- Run PowerShell as Administrator

### Telegram send fails
- Verify `BROADCAST_BOT_TOKEN` in `.env` is the @SLH_AIR_bot token
- Verify `chat_id` is correct (use `/myid` command with any bot to get yours)
- Check the bot hasn't been blocked by the user

### API unreachable
- Check Railway deploy status: https://slh-api-production.up.railway.app/api/health
- If 503, Phase 0 DB Core is reporting honest failure — investigate DB

---

*End of Task Scheduler setup — 2026-04-21*
