# SLH.co.il — מערכת ניהול ROI, בוט טלגרם וניטור

## 🚀 תכונות עיקריות
- **בוט טלגרם** `@SLH_macro_bot` — ניהול ROI, משובים, אדמינים
- **Frontend סטטי** — [www.slh.co.il](https://www.slh.co.il)
- **לוח ניטור** — [monitor.slh.co.il](https://monitor.slh.co.il)
- **PostgreSQL** — ROI, משובים, משתמשים, אדמינים

## 🤖 פקודות הבוט

### פקודות בסיסיות
| פקודה | תיאור |
|--------|--------|
| `/start` | רישום משתמש וברוכים הבאים |
| `/menu` | תפריט ראשי אינטראקטיבי (6 כפתורים) |
| `/status` | סטטוס מערכת + ספירת משתמשים/ROI |
| `/docs` | רשימת פקודות |
| `/roadmap` | מפת דרכים |

### ROI (אדמין בלבד)
| פקודה | דוגמה |
|--------|--------|
| `/add_roi <percent> [description]` | `/add_roi 15.5 Q2 Profit` |
| `/last_roi` | מחזיר את הרישום האחרון |

### משובים
| פקודה | תיאור |
|--------|--------|
| `/feedback_ai <text>` | שליחת משוב (מוכן ל-AI) |
| `/suggest <idea>` | הצעת שיפור |
| `/report <issue>` | דיווח על תקלה |

### ניתוח
| פקודה | תיאור |
|--------|--------|
| `/summary_today` | סיכום יומי (משתמשים חדשים, ROI, משובים) |

### אדמין
| פקודה | תיאור |
|--------|--------|
| `/make_me_admin` | הופך את המשתמש הראשון לאדמין (חד-פעמי) |
| `/request_admin` | בקשת הרשאת אדמין |

## 🗄️ מבנה מסד הנתונים (פרודקשן)

### `users`
```
user_id    BIGINT  PRIMARY KEY
username   TEXT
first_seen TEXT     -- ISO-8601 timestamp
is_admin   BOOLEAN  DEFAULT FALSE
```

### `roi_records`
```
id             SERIAL PRIMARY KEY
user_id        BIGINT
roi_percentage FLOAT
description    TEXT
created_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP
```

### `feedback`
```
id        SERIAL PRIMARY KEY
user_id   TEXT
username  TEXT
message   TEXT
timestamp TEXT    -- ISO-8601 timestamp
```

## 🔧 טכנולוגיות
- Python 3.11
- python-telegram-bot v20.7
- PostgreSQL (Railway)
- Docker / Nixpacks
- Railway (hosting)

## 📁 מבנה פרויקט
```
SLH.co.il/
├── bot.py              # הבוט הראשי
├── requirements.txt    # תלויות
├── railway.json        # קונפיגורציה
├── Dockerfile          # Container
├── .env.example        # דוגמת משתני סביבה
├── .gitignore
├── ai/                 # מודולי AI (אופציונלי, דורש OPENAI_API_KEY)
├── utils/              # כלי עזר
├── docs/               # Frontend סטטי
├── monitor/            # לוח ניטור
└── backups/            # גיבויים
```

## 🏗️ הרצה מקומית

```powershell
cd D:\SLH.co.il
$env:TELEGRAM_BOT_TOKEN="..."
$env:DATABASE_URL="postgresql://..."
pip install -r requirements.txt
python bot.py
```

או דרך Railway env (מומלץ):
```powershell
railway run python bot.py
```

## 🚀 דיפלוי

מחוברים ל-Railway? פשוט `git push origin main` — Railway יעשה rebuild אוטומטי.

פריסה ידנית:
```powershell
railway up
railway logs --build
```

## 🔐 משתני סביבה נדרשים
ראה [`.env.example`](./.env.example). חובה:
- `TELEGRAM_BOT_TOKEN` — מ-@BotFather
- `DATABASE_URL` — מ-Railway Postgres

אופציונלי:
- `OPENAI_API_KEY` — להפעלת ניתוח AI של משובים (`ai/feedback_analyzer.py`)

## 🌐 כתובות
- אתר: https://www.slh.co.il
- בוט: https://t.me/SLH_macro_bot
- מוניטור: https://monitor.slh.co.il

## 📞 קשר
באמצעות `/feedback_ai`, `/suggest`, `/report` בבוט.
