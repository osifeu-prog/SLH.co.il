# 🧩 Task Brief · Sudoku for SLH
> **משימה עצמאית לסוכן מבצע.** 4-6 שעות עבודה. engagement multiplier.

---

## 🎯 מטרה

הוסף משחק Sudoku לאתר SLH כ‑engagement tool. משתמשים פותרים → צוברים **AIC + REP**. פתרונות מהירים → דירוג גבוה יותר. משלב עם כלכלת הטוקנים הקיימת.

---

## 🏆 Value proposition

| למשתמש | למערכת |
|--------|--------|
| משחק יומי קצר (~5 דק') | reason-to-return יומי |
| AIC + REP אוטומטיים | utility מוכח ל‑AIC |
| דירוג ציבורי | social competition |
| משהו מהנה בלי כסף | engagement ללא סיכון |

---

## 🏗 Spec

### Frontend (`website/sudoku.html`)
- HTML/CSS/JS vanilla (אין framework — עקבי עם שאר האתר)
- 3 רמות: Easy / Medium / Hard
- Grid 9×9 עם הדגשת שורה/עמודה/בלוק
- Undo/Redo buttons
- Timer (עוצר כשהכרטיסייה לא active)
- Check / Solve / Hint (hint עולה 1 AIC)
- Mobile-first responsive
- RTL-friendly
- Dark theme (עקבי עם mission-control)
- פריסה זהה לעיצוב הכללי של הקהילה

### Backend endpoints (extend main.py via new file `api/routes/sudoku.py`)
```
POST /api/sudoku/start               → יוצר session חדש + מחזיר puzzle + session_id
POST /api/sudoku/submit              → בדיקת פתרון + חישוב rewards
GET  /api/sudoku/leaderboard         → top 50 weekly + all-time
GET  /api/sudoku/my-stats/{user_id}  → streak, avg time, rank
GET  /api/sudoku/daily-puzzle        → puzzle היומי הקבוע (כולם פותרים אותו)
```

### Reward rules (wire to AIC + REP)
| Difficulty | Base AIC | Base REP | Bonus if <5 min |
|------------|---------:|---------:|----------------:|
| Easy | 1.0 | 2 | +0.5 AIC |
| Medium | 2.5 | 5 | +1 AIC |
| Hard | 5.0 | 12 | +2 AIC |

Daily puzzle: first solve gets +3 AIC bonus. Cap: 3 puzzles/day earn AIC, unlimited for fun.

### DB schema (auto-migrate in `_ensure_sudoku_tables`)
```sql
CREATE TABLE IF NOT EXISTS sudoku_sessions (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    difficulty TEXT NOT NULL,
    puzzle_grid TEXT NOT NULL,   -- 81 chars, 0 = empty
    solution_grid TEXT NOT NULL, -- 81 chars
    started_at TIMESTAMPTZ DEFAULT now(),
    completed_at TIMESTAMPTZ,
    time_seconds INTEGER,
    hints_used INTEGER DEFAULT 0,
    solved BOOLEAN DEFAULT FALSE,
    aic_awarded NUMERIC(10,4) DEFAULT 0,
    rep_awarded INTEGER DEFAULT 0
);
CREATE INDEX idx_sudoku_user ON sudoku_sessions(user_id, started_at DESC);
CREATE INDEX idx_sudoku_leaderboard ON sudoku_sessions(solved, time_seconds) WHERE solved = TRUE;

CREATE TABLE IF NOT EXISTS sudoku_daily (
    date DATE PRIMARY KEY,
    puzzle_grid TEXT NOT NULL,
    solution_grid TEXT NOT NULL,
    difficulty TEXT NOT NULL DEFAULT 'medium'
);
```

---

## 🛠 Templates שנמליץ להשתמש בהם

1. **Sudoku generator** — [sudoku (Python)](https://pypi.org/project/py-sudoku/) · pip install py-sudoku
   - `Sudoku(3).difficulty(0.5)` → מייצר puzzle + solution
2. **Frontend template** — https://github.com/NorbertDuskorn/sudoku (MIT, vanilla JS) או https://github.com/robatron/sudoku.js
3. **Icons** — FontAwesome (כבר באתר)

**אל תשתמש** ב‑heavy frameworks (React/Vue) — לא מתיישב עם שאר האתר.

---

## 🔗 אינטגרציה עם המערכת הקיימת

### 1. AIC earn (חובה)
לאחר solve מוצלח → POST ל‑`/api/aic/earn`:
```json
{"user_id": 123, "amount": 2.5, "reason": "sudoku_solve", "metadata": {"difficulty": "medium", "time_seconds": 245}}
```
הוסף `"sudoku_solve"` ל‑`VALID_EARN_REASONS` ב‑`api/routes/aic_tokens.py`.

### 2. REP earn
אם `/api/rep/add` קיים — השתמש בו. אחרת: הוסף column ישירות.

### 3. Leaderboard integration
הוסף ל‑community.html trending section: "🧩 Top Sudoku solvers this week"

### 4. learning-path
יום 7+ של learning-path → "Bonus: solve today's sudoku for +3 AIC"

### 5. Navigation
הוסף `/sudoku.html` ל‑shared.js `renderTopNav()` בקטגוריית "Play" / "להרוויח"

---

## 🎨 Design reference

- העתק הsign pattern מ‑`admin-tokens.html` או `mission-control.html`
- Grid cells: 48×48px מינימום
- Selected cell: `background: rgba(0,255,65,.15); border: 2px solid var(--accent)`
- Same-row/col/block highlight: `background: rgba(255,255,255,.04)`
- Errors (wrong digit): subtle red glow
- Win animation: confetti + sound (optional)

---

## ✅ Definition of Done

- [ ] `website/sudoku.html` live + mobile-responsive
- [ ] 5 endpoints deployed to Railway (`/api/sudoku/*`)
- [ ] 3 difficulty levels working
- [ ] Daily puzzle auto-refreshes at UTC midnight
- [ ] Solve → AIC earned (verified with `/api/aic/balance/{uid}`)
- [ ] Leaderboard shows top 50 weekly
- [ ] Link from community.html + learning-path.html
- [ ] FAQ entry in join-guide.html
- [ ] Report posted to workers group

---

## ⏱ Time estimate
- Frontend: 2 hours
- Backend + DB: 1.5 hours
- Reward integration: 1 hour
- Polish + test: 0.5 hours
- **Total: ~5 hours**

---

## 🚫 Don't

- ❌ Don't store full solved grids in localStorage (cheating)
- ❌ Don't let users solve the same puzzle twice for AIC (idempotency via session_id)
- ❌ Don't award REP to users with ZUZ > 50
- ❌ Don't expose solution_grid in `/api/sudoku/start` response — only on submit after solve check

---

## 🎁 Extension ideas (after MVP)

- Weekly tournaments with SLH prize pool
- Multiplayer race mode (same puzzle, speed)
- Custom puzzles from community (moderated)
- Print-friendly page for offline play
- Hebrew/Russian/Arabic number display options (Unicode digits)

---

**Agent: Pick this task, announce "Starting Sudoku", ship MVP in 5h, report to workers group.**
