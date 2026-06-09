cd D:\slh-website\slh-claude-bot
railway down --service slh-AI-bot -y
railway up --detach
Start-Sleep 45
railway logs --tail 30
