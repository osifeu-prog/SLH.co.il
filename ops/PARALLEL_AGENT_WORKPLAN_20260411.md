# 🤖 SLH Parallel Agent Work Plan
**Date:** 2026-04-11
**Author:** Claude (with Osif's direction)
**Purpose:** Tasks that can run in parallel by another AI agent / Power user
**Goal:** Bring SLH Spark to "perfect launch" state for next week

---

## 🎯 Current State Snapshot (after my session today)

| System | Status | Notes |
|--------|--------|-------|
| Website slh-nft.com | 🟢 Live | All pages 200, dashboard fixed |
| Railway API | 🟢 Live | 60+ endpoints, ZVK rebrand done |
| Postgres (local + Railway) | 🟢 Healthy | sync needed periodically |
| Docker bots | 🟢 25 running | 23 verified, 1 known issue (userinfo aiogram 3.7) |
| Genesis 49 flow | 🟢 Working | 1/49 redeemed (Shlomo P22), 48 free |
| External wallets | 🟢 Live | Bybit + Binance addresses for Osif tracked |
| Token strategy | 🟢 ZVK rebrand | SLH stays scarce premium |

### Critical issues remaining
1. **12 bots have no commands** (just /start at most) — needs content
2. **Admin panel** showing "API offline" intermittently
3. **5 users (Tsvika, King, Gal, Halit, Osif83) registered but never used coupon** — need outreach
4. **Theme switcher** exists in code but not visible in UI
5. **Wallet UI** still basic — needs major redesign

---

## 📋 PARALLEL TRACK A — Content & Bot Configuration
**Skill needed:** Telegram BotFather, Hebrew copywriting, basic JSON
**Estimated time:** 4-6 hours
**Tools:** @BotFather + text editor

### Task A1: Set bot commands for 12 empty bots
For each of these bots, go to **@BotFather → /setcommands → select bot → paste commands**:

#### @SLH_Academia_bot (CORE)
```
start - 🚀 התחלה
academy - 🎓 קורסים זמינים
mycourses - 📚 הקורסים שלי
progress - 📊 ההתקדמות שלי
leaderboard - 🏆 לוח מובילים
help - ❓ עזרה
```

#### @Grdian_bot (Guardian)
```
start - 🛡 התחלה
status - 📊 סטטוס מערכת
report - 🚨 דווח על בעיה
admin - ⚙️ פאנל ניהול
help - ❓ עזרה
```

#### @Buy_My_Shop_bot (BotShop)
```
start - 🛒 חנות הבוטים
catalog - 📦 קטלוג מוצרים
mycart - 🛒 העגלה שלי
orders - 📋 ההזמנות שלי
buy_slh - 💎 קנה SLH
help - ❓ עזרה
```

#### @SLH_Wallet_bot
```
start - 💼 ארנק SLH
balance - 💰 יתרה
deposit - 📥 הפקדה
withdraw - 📤 משיכה
history - 📜 היסטוריה
swap - 🔄 החלפת מטבעות
```

#### @SLH_community_bot (FUN)
```
start - 💬 קהילת SLH
join - 🎫 הצטרף לקהילה
events - 🎉 אירועים
faq - ❓ שאלות נפוצות
contact - 📞 צור קשר
```

#### @SLH_ton_bot
```
start - 💎 TON Network
balance - 💰 יתרה
send - 📤 שלח TON
receive - 📥 קבל TON
price - 📊 מחיר TON
```

#### @SLH_Ledger_bot
```
start - 📒 רישום מאזן
record - ✏️ רשום עסקה
report - 📊 דוח חודשי
export - 📥 ייצוא
help - ❓ עזרה
```

#### @TS_set_bot
```
start - 🎯 הגדרות
language - 🌍 שפה
notifications - 🔔 התראות
privacy - 🔒 פרטיות
about - ℹ️ אודות
```

#### @MY_NFT_SHOP_bot
```
start - 🎨 חנות NFT
browse - 👀 עיין בקטלוג
my_nfts - 🖼 ה-NFTs שלי
mint - ⚡ צור NFT חדש
sell - 💸 מכור NFT
```

#### @beynonibank_bot
```
start - 🏦 בנק בינוני
balance - 💰 יתרה
deposit - 📥 הפקדה
loan - 💳 הלוואה
support - 📞 תמיכה
```

#### @TESTinbot_bot_bot
```
start - 🧪 בדיקות
ping - 🏓 פינג
echo - 🔁 הד
debug - 🐛 דיבוג
```

#### @Chance_Pais_bot
```
start - 🎲 משחקי מזל
play - ▶️ שחק
balance - 💰 יתרה
recovery - 🆘 התאוששות מהתמכרות
help - ❓ עזרה
```

### Task A2: Set bot descriptions
For each bot, **@BotFather → /setdescription**:

```
@SLH_Academia_bot:
SLH Academia — מערכת לימוד דיגיטלית עם קורסים, משימות יומיות, ולוח מובילים.

@SLH_Wallet_bot:
ארנק SLH הרשמי — נהל את הטוקנים שלך, שלח, קבל, החלף, והפקד.

(וכן הלאה לכל בוט)
```

### Task A3: Set bot About + Profile Picture
**@BotFather → /setabouttext** ו-**/setuserpic** עם תמונה מ-`assets/img/`:
- @SLH_Academia_bot → `slh-academia.jpg`
- @SLH_Wallet_bot → לוגו SLH
- @NFTY_madness_bot → `bot-mascot.jpg`
- @SLH_community_bot → `slh-community.jpg`
- וכו'

---

## 📋 PARALLEL TRACK B — Outreach (5 users to convert)
**Skill needed:** Communication, Telegram
**Estimated time:** 30 minutes
**Tools:** Telegram

### Task B1: Personal messages to existing users
שלח באופן אישי ל-5 משתמשים אלו (כולם נכנסו ל-dashboard אבל לא הצטרפו ל-Genesis 49):

| User | First name | Suggested Hebrew message |
|------|-----------|--------------------------|
| @osifeu_prog (224223270) | Osif (אתה) | עצמך — אישור שהכל עובד |
| @Osif83 (7757102350) | Osif | "היי, הצטרפת ל-SLH אבל לא לקחת את ה-Genesis 49 שלך — יש לך 10K ZVK בחינם, רק תלחץ: https://slh-nft.com/onboarding.html?ref=224223270" |
| @KingShai1st (5940607518) | King | "King, ראיתי שנכנסת! יש לך מקום בהבטחה ל-Genesis 49 — 10,000 ZVK + NFT, חינם. רק לחיצה: https://..." |
| @Galg19 (8541466413) | Gal | "גל! הזמנתי אותך ל-Genesis 49 — מקום שמור עם 10K ZVK + NFT. https://..." |
| (6192197452) Halit | Halit | "Halit, יש לך מקום ב-49 הראשונים — 10,000 ZVK חינם, רק לחיצה: https://..." |
| @P22PPPPPP (8088324234) | שלמה | "שלמה — אתה כבר Genesis Member #1! בדוק את הקאשבק שלך: https://slh-nft.com/dashboard.html" |

### Task B2: Tsvika (Zvika) — Special outreach
Tsvika is a real crypto trader and partner — special VIP message:
> "צביקה, המערכת מוכנה. אתה השני אחרי שלמה ב-Genesis. יש לך מקום שמור + bonus מיוחד כשותף. תיכנס ב: https://slh-nft.com/onboarding.html?ref=224223270 ותקבל ZVK + NFT, ואח"כ נדבר על שיתוף הפעולה הרחב יותר."

---

## 📋 PARALLEL TRACK C — Visual / Theme Improvements
**Skill needed:** HTML/CSS, design intuition
**Estimated time:** 6-8 hours
**Tools:** Browser DevTools, code editor

### Task C1: Make theme switcher visible
**File:** `D:\SLH_ECOSYSTEM\website\dashboard.html`
**Look for:** `setTheme(` function or `slh_theme` localStorage usage
**Action:** Add a button/dropdown in the top nav of all pages:
```html
<button onclick="cycleTheme()" title="החלף ערכת נושא">🎨</button>
```
Plus implement the cycle:
```javascript
function cycleTheme() {
    const themes = ['terminal', 'crypto', 'light', 'cyberpunk', 'sunset', 'ocean', 'matrix'];
    const current = localStorage.getItem('slh_theme') || 'terminal';
    const next = themes[(themes.indexOf(current) + 1) % themes.length];
    localStorage.setItem('slh_theme', next);
    document.body.className = 'theme-' + next;
    showToast('🎨 ערכת נושא: ' + next);
}
```
Add CSS variants for each theme in `css/shared.css`.

### Task C2: Add 3 new themes
Add to `css/shared.css`:
```css
body.theme-cyberpunk {
    --bg: #0a0014;
    --accent: #ff00ff;
    --text: #00ffff;
    /* ... */
}
body.theme-sunset {
    --bg: #1a0f1f;
    --accent: #ff6b35;
    --text: #ffd700;
}
body.theme-ocean {
    --bg: #001828;
    --accent: #00d4ff;
    --text: #b8e0ff;
}
```

### Task C3: Wallet UI overhaul
**File:** `D:\SLH_ECOSYSTEM\website\wallet.html`
**Goals:**
- Replace 5-card grid with **single hero card** showing total value
- Sub-cards expandable/collapsible per token
- Animated price tickers
- Charts (Chart.js already loaded) showing portfolio history
- Better mobile layout (currently feels cramped)

### Task C4: Dashboard polish
- Add user avatar from Telegram (`currentUser.photo_url`)
- Improve notifications panel (currently empty bell)
- Add "What's New" widget showing latest commits/changes
- Welcome modal for first-time visitors

---

## 📋 PARALLEL TRACK D — Bot Improvements (per-bot deep work)
**Skill needed:** Python, Telegram Bot API
**Estimated time:** 2-4 hours per bot
**Tools:** VS Code, Docker

### Task D1: Fix slh-userinfo (aiogram 3.7 breaking change)
**File:** `D:\SLH_ECOSYSTEM\userinfo-bot\main.py`
**Status:** Code already fixed by me — needs `docker compose build userinfo-bot && docker compose up -d userinfo-bot`

### Task D2: Build "AI moderator" for community groups
Per Osif's request, integrate `@AI_SLH_bot` (or one of the empty bots) with:
- Auto-moderation (anti-spam, profanity filter)
- Welcome messages with SLH ecosystem intro
- /help command linking to dashboard
- Reaction-based polls

### Task D3: NFTY Tamagotchi enhancements
**File:** `D:\SLH_ECOSYSTEM\nfty-bot\main.py`
- Add `/marketplace` to trade pets/items
- Pet breeding system
- Daily quests with ZVK rewards (uses cashback engine!)
- Achievement badges

---

## 📋 PARALLEL TRACK E — Testing & QA
**Skill needed:** Methodical testing, bug reporting
**Estimated time:** 3 hours

### Task E1: Manual /start test on all 25 bots
Send `/start` to each bot in Telegram, document response:
| Bot | Responds? | Menu shown? | Main button works? | Notes |
|-----|-----------|-------------|-------------------|-------|
| @SLH_AIR_bot | ✅ | ✅ | ✅ | All 21 commands work |
| @SLH_Academia_bot | ❓ | ❓ | ❓ | (test) |
| ... | | | | |

### Task E2: Test Genesis 49 flow with a NEW Telegram account
1. Create new Telegram account (or use friend's)
2. Open `https://slh-nft.com/onboarding.html`
3. Click "התחל עכשיו חינם"
4. Connect Telegram
5. Verify GENESIS49 auto-fills
6. Click "אישור"
7. Verify NFT number assigned
8. Verify ZVK balance shows in wallet
9. Document any friction points

### Task E3: Test wallet end-to-end
- [ ] Connect MetaMask → balances show
- [ ] BNB on-chain visible
- [ ] USDT BSC visible
- [ ] Add Bybit external address → balance refreshes
- [ ] Send TON between two test accounts
- [ ] History shows correctly

---

## 📋 PARALLEL TRACK F — Marketing Assets
**Skill needed:** Canva / Figma / image editing
**Estimated time:** 2-3 hours

### Task F1: Social media images (1200x630)
Create variants of `assets/img/phoenix-og.jpg` for:
- Twitter card
- WhatsApp preview
- Facebook share
- LinkedIn share
- Telegram channel header

### Task F2: Reels/short videos
- 30sec intro to Genesis 49
- Wallet walkthrough screen-recording
- "How to redeem GENESIS49 in 60 seconds"

### Task F3: Email templates
For inviting partners/investors to test the system before public launch.

---

## 🎯 Priority Order (if I were doing this myself)

**Day 1 (2 hours):**
1. Track A1: Set bot commands for 12 empty bots (highest ROI)
2. Track B1: Outreach to 5 existing users
3. Track E1: /start test on 5 critical bots (@SLH_AIR_bot, @SLH_Academia_bot, @SLH_Wallet_bot, @Buy_My_Shop_bot, @MY_SUPER_ADMIN_bot)

**Day 2 (4 hours):**
4. Track C1+C2: Theme switcher + 3 new themes
5. Track A2+A3: Bot descriptions + profile pictures
6. Track E2: Genesis 49 E2E with new account

**Day 3-7:**
7. Track C3: Wallet redesign
8. Track D1: Fix userinfo bot
9. Track F1: Social media images
10. Track D2: AI moderator for groups

---

## 🚨 BLOCKER ITEMS (need Osif personally)

1. **Token rotations** — only Osif can revoke + paste new tokens via @BotFather
2. **Bot ownership** — Osif owns all 25 bots in @BotFather, agent can't access
3. **Railway deploys** — needs Osif's GitHub access (already configured for slh-api repo)
4. **Domain DNS** — slh-nft.com is GitHub Pages, configured by Osif
5. **Payment approvals** — admin manually approves payments via @MY_SUPER_ADMIN_bot
6. **Real money decisions** — pricing, partnerships, exchange listings

---

## 💬 How to brief a parallel AI agent

If you spawn an agent (PowerShell/Power Apps/Cursor/Cline), give them this exact prompt:

```
You are working on SLH Spark — an Israeli crypto investment platform.

Repo locations:
- Website: D:\SLH_ECOSYSTEM\website (git remote: github.com/osifeu-prog/osifeu-prog.github.io)
- API: D:\SLH_ECOSYSTEM\api (git remote: github.com/osifeu-prog/slh-api → auto-deploys to Railway)
- Bots: D:\SLH_ECOSYSTEM\{airdrop,wallet,factory,nfty-bot,userinfo-bot,...}

Current state report: D:\SLH_ECOSYSTEM\ops\PARALLEL_AGENT_WORKPLAN_20260411.md

Your task: Pick ONE track from the work plan and complete it. Do not touch anything else. Always git pull before starting, git push after committing. Do NOT modify .env. Do NOT touch token rotation. Do NOT delete files without asking.

Stack:
- Frontend: Vanilla HTML/CSS/JS (no framework), GitHub Pages auto-deploy
- Backend: FastAPI on Railway (postgres + redis)
- Bots: aiogram 3.x in Docker (docker-compose.yml)

Verification after changes:
- Website: curl https://slh-nft.com/{page}.html (should be 200)
- API: curl https://slh-api-production.up.railway.app/api/health
- Bots: docker logs slh-{name} --tail 10
```

---

## 📞 Status check command (for any agent to run)

```bash
# Quick health check
curl https://slh-api-production.up.railway.app/api/health
curl https://slh-api-production.up.railway.app/api/beta/status
curl https://slh-api-production.up.railway.app/api/external-wallets/224223270
docker ps --filter "name=slh-" --format "{{.Names}} {{.Status}}" | sort
```

If all return 200/healthy and 25 containers up — system is GO.

---

*Generated by Claude Opus 4.6 on 2026-04-11*
*Last commit: website 96042c5, api 5f80f52*
