# SESSION HANDOFF 03/05/2026

## מה עובד
- /ps עובד מהבוט (PowerShell מלא)
- /status עובד (ריק)
- agent_api.py רץ על localhost:8090
- agent_simple.py רץ עם PowerShell

## מה שבור
- /scan timeout (scan_registry.ps1 לא מעדכן registry)
- /registry ריק
- PROJECT_COMMAND_CENTER.html סימני ?? (encoding)

## קבצים קריטיים
- agent_api.py = D:\SLH_ECOSYSTEM\agent_api.py
- agent_simple.py = D:\SLH_ECOSYSTEM\agent_simple.py
- bot.py = D:\SLH_ECOSYSTEM\control-bot\bot.py
- scan_registry.ps1 = D:\SLH_ECOSYSTEM\control-bot\scan_registry.ps1
- registry = D:\SLH_ECOSYSTEM\control-bot\slh_registry.json

## הפעלה מחדש
Start-Process python -ArgumentList "D:\SLH_ECOSYSTEM\agent_api.py" -WindowStyle Hidden
Start-Sleep 4
Start-Process python -ArgumentList "D:\SLH_ECOSYSTEM\agent_simple.py" -WindowStyle Hidden

## משימה ראשונה
תקן scan_registry.ps1:
Get-Content D:\SLH_ECOSYSTEM\control-bot\scan_registry.ps1

## P0
1. תקן /scan
2. תקן ?? ב-PROJECT_COMMAND_CENTER.html
3. Railway env vars: JWT_SECRET, ADMIN_API_KEYS

## P1
1. תמיכת קבוצה — צביקה קאופמן מזין משימות
2. לוח משימות משותף
3. סנכרון PROJECT_COMMAND_CENTER ↔ bot