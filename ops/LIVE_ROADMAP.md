# 🎯 SLH · LIVE ROADMAP
> **מסמך חי אחד.** עודכן: 2026-04-17 16:20 · 35+ commits היום.

---

## 🧭 סטטוס 6 tracks

| # | יעד | אתמול | עכשיו | שינוי |
|---|-----|:-----:|:-----:|:-----:|
| 1 | 💰 Payments | 70% | **95%** | +25 |
| 2 | 🎓 Verified Experts | 30% | **65%** | +35 |
| 3 | 💝 Dating (@G4meb0t_bot_bot) | 5% | **65%** | +60 |
| 4 | 🚪 No-Facebook Traffic | 10% | 20% | +10 |
| 5 | 🏘 Social Network | 40% | **75%** | +35 |
| 6 | 🧠 AIC · AI Economy | 0% | **80%** | NEW |

**ממוצע כללי: 67% (היה 26%). הקפיצה הגדולה ביותר ביום אחד.**

---

## ✅ מה נשלח היום לפרודקשן

### 💰 Track 1 · Payments (95%)
- ✅ TON auto-verify · toncenter · live
- ✅ BSC auto-verify · **Binance public RPC** (חינמי, ללא מפתח)
- ✅ External providers · 10 מסלולים (Stripe/PayPal/iCount/Cardcom/Meshulam/Isracard/GrowClub/manual_bank/ton_direct/bsc_direct)
- ✅ Digital receipts · SLH-YYYYMMDD-NNNNNN
- ✅ PancakeSwap TX tracker (Binance dataseed RPCs)
- ✅ pay.html · 4-step funnel עם QR + Tonkeeper/MetaMask deep-links
- ✅ buy.html · updated עם TON+BSC direct
- 🟡 Stripe webhook (pending user signup)

### 🎓 Track 2 · Verified Experts (65%)
- ✅ Proof-of-expertise fields (LinkedIn/website/YouTube/credentials/years)
- ✅ Registration blocks unless ≥1 proof
- ✅ `/api/admin/experts/pending` + `/api/admin/experts/approve`
- ✅ admin-experts.html · login gate, stats, 4-action approval
- ✅ ZVK bonus on approval

### 💝 Track 3 · Dating (65%)
- ✅ `/api/dating/*` · 8 endpoints (profile/candidates/action/matches/stats)
- ✅ Age 18+ enforced · minors (nephew ID 6466974138) blocked
- ✅ Interest-overlap matching algorithm
- ✅ Mutual-match detection · TG deep-link after match
- ✅ dating.html · age gate, 3 tabs, 28 interests, Hebrew-first
- ✅ g4mebot/ · @G4meb0t_bot_bot skeleton (aiogram 3.x, 200 lines)
- ✅ g4mebot Dockerfile + README
- 🟡 Bot deploy (needs BotFather token + docker-compose entry)

### 🏘 Track 5 · Social Network (75%)
- ✅ 6-emoji reactions (👍❤️😂😮😢😡) + toggle/change
- ✅ Threaded replies (1 level deep)
- ✅ Presence heartbeat + online dots
- ✅ DM button on posts (TG deep-link OR inline reply)
- ✅ learning-path.html · 21-day + streak + ZVK
- ✅ join-guide.html · 5 languages + 3-step onboarding
- ✅ Sudoku engagement (9×9, 3 difficulties, daily puzzle, leaderboard)

### 🧠 Track 6 · AIC (80%)
- ✅ 6th token shipped (AI Credits, 1 AIC ≈ $0.001)
- ✅ admin-tokens.html unified dashboard
- ✅ `/api/ai/chat-metered` with AIC burn + welcome gift (5 AIC)
- ✅ Hint costs in Sudoku (1 AIC/hint)
- ✅ Mint/reserve admin flows
- 🟡 AIC circulation = 0 (needs first mint)

### 🛠 Agent Tooling
- ✅ 5 agent prompts public at `/prompts/*.md`
- ✅ agent-brief.html interactive
- ✅ SCAN by secondary agent (partial but informative)
- ✅ MASTER_EXECUTOR_AGENT_PROMPT · 339 lines
- ✅ LEDGER_GUARDIAN_ESP prompt · 280 lines
- ✅ ESP_QUICKSTART · PowerShell exact
- ✅ SYSTEM_SCAN · read-only auditor
- ✅ TASK_SUDOKU · 5h task brief
- ✅ ALL_AGENT_PROMPTS · master index

### 🐛 Track F (new) · AI Bug Analysis
- ✅ `POST /api/admin/bugs/{id}/ai-analyze` · 3 agent modes (claude_code/advisor/human_only)
- ✅ DB columns: ai_analysis, ai_analyzed_at, ai_agent
- 🟡 admin-bugs.html frontend integration (pending)

---

## 🔴 מה נשאר עליך (Osif-only)

### ⚡ היום (5 דק' לכל אחד)
1. `SILENT_MODE=1` ב-Railway
2. Login ב‑admin-tokens.html + mint ראשון של AIC
3. בדיקת תשלום TON חי (0.5 TON → `/pay.html`)

### 📅 השבוע
4. יצירת `@G4meb0t_bot_bot` ב‑BotFather → הפק TOKEN → שים ב‑.env
5. Stripe signup (אם תרצה תשלומי כרטיס בינלאומיים)

### 🏗 החודש
6. סיבוב 31 bot tokens (אבטחה)
7. Twilio API key (SMS אמיתי)

---

## 📊 מצב המערכת (live)

| Component | Status |
|-----------|--------|
| API | ✅ 1.0.0 · **225+ endpoints** |
| Frontend | ✅ 15+ pages (כולל pay, sudoku, dating) |
| TON verify | ✅ live |
| BSC verify | ✅ live (free RPC) |
| AIC Economy | ✅ live · 0 supply (awaiting mint) |
| Community+ | ✅ reactions, replies, presence live |
| Sudoku | ✅ 8 endpoints live |
| Dating API | ✅ 8 endpoints live |
| @G4meb0t_bot_bot | 🟡 code ready, deploy pending |
| AI Gateway | ✅ with AIC burn |
| Bug AI analyze | ✅ backend live |

---

## 🎯 הצעות להמשך (בחר A/B/C/D/E/F)

**A.** admin-bugs.html · wire AI analyze button (~45 דק')
**B.** Deploy @G4meb0t_bot_bot (דורש TOKEN מ-BotFather)
**C.** Stripe webhook · תשלומי כרטיס בינלאומיים (~60 דק')
**D.** Mission-control · הוספת Dating + Sudoku widgets (~30 דק')
**E.** Community.html · "Top Sudoku solvers" trending section (~30 דק')
**F.** אחר — תגיד

---

**🤖 Claude Code · 35+ commits היום. 6 tracks לחצי הדרך+.**
