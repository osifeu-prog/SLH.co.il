# SESSION HANDOFF — 2026-05-01 — PRODUCTION LIVE
## API
- URL: https://slh-fastapi-production.up.railway.app
- Status: ok, db=connected, version=1.1.0
- Railway service: slh-fastapi (project: diligent-radiance)
- 10 Variables: PORT, DATABASE_URL, REDIS_URL, OPENAI_API_KEY, JWT_SECRET, ADMIN_USER_ID, PYTHONUNBUFFERED, ADMIN_API_KEYS, ENCRYPTION_KEY, INITIAL_ADMIN_PASSWORD

## Website
- URL: https://slh-nft.com (GitHub Pages)
- shared.js: API_BASE = https://slh-fastapi-production.up.railway.app (updated 2026-05-01)
- 140+ HTML pages connected

## Git Repos
- API: github.com/osifeu-prog/slh-api (master) -> Railway slh-fastapi
- Site: github.com/osifeu-prog/osifeu-prog.github.io (main) -> GitHub Pages
- Legacy: github.com/osifeu-prog/SLH.co.il (main) -> Railway SLH.co.il

## Health Check
Invoke-RestMethod https://slh-fastapi-production.up.railway.app/api/health

## P0 Next
1. Update API_BASE in admin-bot/main.py line 33 to new URL
2. Add BOT_HEARTBEAT_KEY to Railway variables
3. docker compose up -d to restart bots with new API_BASE

## P1 Next
4. Fix pay.html 3 bugs
5. Add JWT auth to /api/user/{id}, /api/user/wallet/{id}, /api/user/full/{id}
6. Connect wallet.html to /api/wallet/{user_id}/balances
7. Rotate 30 remaining bot tokens (1/day via BotFather)

## Osif
- Telegram ID: 224223270
- Admin bot: @MY_SUPER_ADMIN_bot
- Local path: D:\SLH_ECOSYSTEM
