# 👩‍💻 SLH Contributor Guide
> Everything you need to start contributing to SLH Spark.
> **Start here if you landed from [slh-nft.com/join.html](https://slh-nft.com/join.html).**

---

## 🎯 TL;DR (3 דק' קריאה)
1. הרשם בבוט: [@SLH_AIR_bot](https://t.me/SLH_AIR_bot) עם `/start` → תקבל 1,000 ZVK
2. Fork את ה-repo: [github.com/osifeu-prog/slh-api](https://github.com/osifeu-prog/slh-api)
3. בחר משימה מ-`ops/TASK_BOARD.md` או פתח GitHub Issue
4. פתח PR → code review → merge → 500 ZVK

---

## 🗂️ מבנה הפרויקט
```
D:\SLH_ECOSYSTEM\ (root — pushed to github.com/osifeu-prog/slh-api)
├── api/
│   └── main.py         ← FastAPI, 117 endpoints, ~9900 lines
├── main.py             ← MIRROR of api/main.py (Railway deploys this!)
├── shared/             ← shared Python modules (payments, wallet, filters)
├── dockerfiles/        ← per-bot Dockerfiles
├── docker-compose.yml  ← 25 bots + postgres + redis
├── ops/                ← docs, session handoffs, audits, SQL migrations
│   ├── SESSION_STATUS.md    ← live state (SSoT)
│   ├── DECISIONS.md         ← append-only decision log
│   ├── TASK_BOARD.md        ← pick a task from here
│   ├── ARCHITECTURE.md
│   └── sql/                 ← DB migrations (numbered 901..909)
└── *-bot/              ← per-bot code (airdrop-bot/, campaign-bot/, etc.)

D:\SLH_ECOSYSTEM\website\ (separate repo → GitHub Pages)
├── *.html              ← 45 pages
├── js/
│   ├── shared.js       ← nav, FAB, auto-capture (loaded on every page)
│   ├── translations.js ← i18n
│   └── analytics.js
└── assets/             ← images, OG cards
```

---

## 💻 הגדרה לוקלית (10 דק')

### דרישות
- Python 3.11+
- Docker Desktop
- Git
- Node.js (ל-linting)

### צעדים
```bash
# 1. Clone
git clone https://github.com/<your-fork>/slh-api.git D:\SLH_DEV
cd D:\SLH_DEV

# 2. Copy .env.example → .env (fill with test tokens from @BotFather for testing)
cp .env.example .env

# 3. Run the DB + infra only (not all bots — that's for Osif's machine)
docker compose up -d postgres redis

# 4. Run API locally
cd api
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# 5. Open http://localhost:8000/docs → Swagger UI
```

### Website לוקלית
```bash
cd D:\SLH_ECOSYSTEM\website
python -m http.server 3000
# Open http://localhost:3000
```

---

## 🎨 קונבנציות קוד

### Python
- **Async all the way:** use `asyncio`, `asyncpg`, `aiohttp`, `aiogram 3.x`
- **No ORM:** raw SQL via `pool.acquire()` (team choice — readability over abstraction)
- **Type hints on public endpoints** (Pydantic models for request/response)
- **English in code/comments, Hebrew in UI strings**
- **No print() in production** — use `logging`

### HTML/JS/CSS
- **Vanilla only.** No React/Vue/Svelte. Keep it lean.
- **RTL-aware:** `dir="rtl"` on `<html>` for Hebrew pages
- **CSS variables** for theming (`var(--gold)`, `var(--bg2)`)
- **Load shared.js + analytics.js on every page**
- **Hebrew strings inline** (future: migrate to js/translations.js)

### Commits
- **Conventional commits:** `feat(bugs): ...`, `fix(api): ...`, `docs(ops): ...`, `chore: ...`
- **Body explains WHY, not WHAT** (diff shows what)
- Include `Co-Authored-By:` if you paired with AI

### PRs
- **One PR = one logical change**
- **Title:** clear + conventional
- **Description:** what/why + screenshots if UI change
- **Checklist:**
  - [ ] Ran `python -c "import ast; ast.parse(open('api/main.py',encoding='utf-8-sig').read())"` (syntax OK)
  - [ ] Tested locally against `/api/health`
  - [ ] Updated docs in ops/ if needed
  - [ ] No secrets in diff

---

## 🏆 תגמולים (בפירוט)

| תרומה | ZVK | SLH | הערה |
|-------|-----|-----|------|
| Signup | 1,000 | — | One-time |
| Accepted PR (bug fix) | 500 | — | Per PR |
| Accepted PR (feature) | 2,000 | — | Per feature |
| Accepted PR (large feature) | 5,000 | 5 | Discretionary |
| Translation of 1 page | 200 | — | Full i18n JSON |
| High-quality bug report | 50-200 | — | Depends on severity |
| Security vulnerability disclosure | 1,000-10,000 | 10-100 | Responsible disclosure |
| Weekly code review participation | 300 | — | Per review cycle |
| Referral (new active contributor) | 1,000 | — | One-time per referral |
| Documentation contribution | 100-500 | — | Per doc |

**ZVK value:** ~₪4.4 ליחידה (internal exchange rate).
**SLH value:** market price on PancakeSwap (volatile, ~₪444 target).

---

## 🏗️ תחומים ל-onboarding

### 🤖 בוטי Telegram
- **Stack:** aiogram 3.x, asyncpg, aiohttp
- **Good first tasks:**
  - הוסף `/status` command לבוט כלשהו
  - תרגם messages של בוט לאנגלית (i18n)
  - Fix bot-to-bot message filter (use `shared/bot_filters.py`)
- **Key files:** `*-bot/`, `shared/bot_template.py`, `shared/bot_filters.py`

### 🌐 Frontend
- **Stack:** Vanilla HTML/JS, Font Awesome, Chart.js
- **Good first tasks:**
  - Dark mode toggle ל-5 עמודים
  - Mobile responsive fixes
  - Lighthouse score improvements
- **Key files:** `website/*.html`, `website/js/shared.js`

### ⚡ API / Backend
- **Stack:** FastAPI, PostgreSQL 15, Redis 7, JWT auth
- **Good first tasks:**
  - הוסף endpoint לדוח שבועי על revenue
  - Rate limiting per IP
  - Cache responses ב-Redis
- **Key files:** `api/main.py`, `ops/sql/*.sql`

### 📡 ESP32 / IoT
- **Stack:** PlatformIO, Arduino Framework, ESP32-S3
- **Good first tasks:**
  - Implement Device Registration Flow (see `ops/DEVICE_ONBOARDING_FLOW.md`)
  - OLED display integration
  - Sensor → signed payload → API
- **Key files:** `ops/DEVICE_ONBOARDING_FLOW.md`, TBD `esp32/` dir

### 🧪 QA / Testing
- **Good first tasks:**
  - Write integration test for `/api/bugs/report`
  - E2E test for purchase flow
  - Automate `/api/health` monitoring
- **Key files:** `ops/ENDPOINTS_TEST_GUIDE.md`, TBD `tests/` dir

### 📝 תיעוד / תרגום
- **Good first tasks:**
  - Translate `website/about.html` to English/Russian
  - Simplify `ops/ARCHITECTURE.md` for new contributors
  - Video tutorial (YouTube channel exists)

---

## 🚫 אל תעשה (חוקי-ברזל)
1. **אל תקומיט `.env` או טוקן כלשהו** (gitignored + pre-commit checks)
2. **אל תקומיט ל-master ישירות** — כל שינוי דרך PR
3. **אל תריץ `git push --force` על master**
4. **אל תיגע ב-Railway env vars** ללא אישור של Osif
5. **אל תשלח הודעות טלגרם יזומות** למשתמשים (רק תשובות לפקודות שלהם)
6. **אל תוסיף backward-compatibility shims** — החלף, אל תשכבה
7. **אל תכתוב mocks בתור real data** — השתמש בתווית `[DEMO]` אם חייב

---

## 📞 איך לקבל עזרה

| צורך | איפה |
|------|-----|
| שאלה טכנית כללית | GitHub Issues |
| אני תקוע באג | [@SLH_AIR_bot](https://t.me/SLH_AIR_bot) → /help |
| Code review לא הגיע תוך 48h | tag @osifeu-prog |
| חשד לדליפת סוד | email: osif.erez.ungar@gmail.com (no GitHub issue!) |
| רעיון לפיצ'ר | Discussion tab ב-GitHub |

---

## 🏅 Hall of Fame
מפתחים שתרמו נכנסים ל-`ops/CONTRIBUTORS.md` + לפאנל הקרדיטים באתר.

---

## 📜 License
Apache 2.0 — free to fork, modify, use commercially. Attribution required (link back to main repo).

---

**שאלה שלא ענה עליה המדריך?** פתח GitHub Issue עם label `question`. אענה תוך 24 שעות.

💙 תודה שאתה שוקל לתרום ל-SLH.
