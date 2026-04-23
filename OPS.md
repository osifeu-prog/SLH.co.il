# SLH.co.il - Operations Guide v1.0

## 🚀 Deployment Status
- **Bot**: t.me/SLH_macro_bot
- **Monitor**: monitor.slh.co.il  
- **Website**: www.slh.co.il

## 🔧 Railway Services
```bash
railway status
railway logs --service bot --lines 100
railway logs --service monitor --lines 100
📊 Monitoring Commands
/status - System health

/users - User list

/signals - Trading signals

/add_roi 15.5 - Add ROI

/last_roi - Last ROI

🔐 Environment Variables
TELEGRAM_BOT_TOKEN

DATABASE_URL

🐛 Troubleshooting
Bot not responding → Check if service is running on Railway

DB errors → Verify DATABASE_URL in Variables

SSL errors → Windows async issue, ignore (works on Railway)

📅 Last Update
April 23, 2026 - All systems operational
