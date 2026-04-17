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

## ⭐ Deploy → Railway (recommended — בחירת ברירת המחדל)

פעולה חד-פעמית (3 דק'):

1. https://railway.app/dashboard → פרויקט `slh-api`
2. `+ New` → `GitHub Repo` → `osifeu-prog/slh-api`
3. ב-Service החדש → `Settings` → `Root Directory`: `g4mebot`
4. `Variables` — הדבק:
   ```
   G4MEBOT_TOKEN=8298897331:AAFCJcgqddM96tvgDcoElwdAPtrCZwy9KqE
   SLH_API=https://slh-api-production.up.railway.app
   SLH_SITE=https://slh-nft.com
   G4MEBOT_USERNAME=G4meb0t_bot_bot
   ```
5. `Deploy` — Railway בונה מ-`Dockerfile`, מריץ `python bot.py`, ומפעיל מחדש אוטומטית בכשל (עד 10 נסיונות).

אחרי זה הבוט חי 24/7 בלי תלות ב-PC שלך.

## Alternatives (אם תרצה לשנות)

### Local Python
```powershell
cd D:\SLH_ECOSYSTEM\g4mebot
pip install -r requirements.txt
$env:G4MEBOT_TOKEN = "<token>"
python bot.py
```

### Docker Compose
```yaml
g4mebot:
  build: ./g4mebot
  container_name: slh-g4mebot
  restart: always
  environment:
    G4MEBOT_TOKEN: ${G4MEBOT_TOKEN}
    SLH_API: https://slh-api-production.up.railway.app
    SLH_SITE: https://slh-nft.com
    G4MEBOT_USERNAME: G4meb0t_bot_bot
```

## Env vars
- `G4MEBOT_TOKEN` (חובה) — מ-BotFather
- `SLH_API` (default: `https://slh-api-production.up.railway.app`)
- `SLH_SITE` (default: `https://slh-nft.com`)
- `G4MEBOT_USERNAME` (default: `G4meb0t_bot_bot`) — לבניית deep-links

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
