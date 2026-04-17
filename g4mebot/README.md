# 🤖 @G4meb0t_bot_bot · SLH Dating Telegram Bot

## מה זה
בוט טלגרם ל‑SLH Dating. משתמש ב‑`/api/dating/*` endpoints של ה‑SLH API המרכזי.
אין DB מקומי, אין state פרסיסטנטי — הכל דרך ה‑API.

## Commands
| Command | מה עושה |
|---------|---------|
| `/start` | welcome + age gate 18+ |
| `/match` | מועמד הבא + כפתורי pass/like/super |
| `/matches` | רשימת התאמות הדדיות |
| `/profile` | תצוגת פרופיל (עריכה באתר) |
| `/help` | רשימת פקודות |

## Run locally
```powershell
cd D:\SLH_ECOSYSTEM\g4mebot
pip install -r requirements.txt
$env:G4MEBOT_TOKEN = "<token-from-BotFather>"
python bot.py
```

## Run via Docker
```powershell
cd D:\SLH_ECOSYSTEM
docker compose up -d g4mebot
```
(הוסף ל‑`docker-compose.yml`:)
```yaml
g4mebot:
  build: ./g4mebot
  container_name: slh-g4mebot
  restart: always
  environment:
    G4MEBOT_TOKEN: ${G4MEBOT_TOKEN}
    SLH_API: https://slh-api-production.up.railway.app
```

## Env vars
- `G4MEBOT_TOKEN` (required) — token from `@BotFather → /newbot` or existing
- `SLH_API` (default: `https://slh-api-production.up.railway.app`)

## Security
- User ID `6466974138` (osif's nephew, 13yo) is **blocked** at `/start`
- Age gate on first interaction; minors can't pass
- All profile edits done on website — bot is interaction-only
- No secrets in code — everything via env

## Architecture
```
user ↔ @G4meb0t_bot_bot (aiogram 3.x)
        │
        ├── GET  /api/dating/profile/{uid}
        ├── POST /api/dating/match/candidates
        ├── POST /api/dating/match/action
        └── GET  /api/dating/matches/{uid}
        │
        ↓
   SLH API (Railway) → PostgreSQL
```

## TODO (post-MVP)
- [ ] Inline query support (search by interest)
- [ ] Photo upload via Telegram (stored at SLH API)
- [ ] Push notifications on new match
- [ ] Video-intro support
- [ ] Language picker (HE/EN/RU/AR/FR)
