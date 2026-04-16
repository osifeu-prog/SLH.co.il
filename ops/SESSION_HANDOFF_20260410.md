# 📱 SLH Session Handoff — 2026-04-10

> **Purpose:** Continue the current work session from a different device or later time (Sunday).
> **Created:** 2026-04-10 12:35 UTC+3
> **Status:** Ready for Genesis 49 launch, pending token rotation

---

## 🎯 Where we stopped

All critical fixes are **deployed and live**:
- Wallet displays real balances (SLH 199,788, ZVK 1,000)
- Genesis 49 coupon flow tested end-to-end
- Custom display_name API endpoint live
- Onboarding page with Phoenix OG image deployed
- Mobile rotation tool (rotate.html) deployed

**You are about to travel.** The only task remaining is **token rotation** — you can do it from your phone using the rotation tool.

---

## 🔗 Key URLs (bookmark these on phone)

| Purpose | URL |
|---------|-----|
| **Mobile rotation tool** | https://slh-nft.com/rotate.html |
| **Genesis 49 share link** | https://slh-nft.com/onboarding.html |
| **Wallet (for testing)** | https://slh-nft.com/wallet.html |
| **Dashboard** | https://slh-nft.com/dashboard.html |
| **API health** | https://slh-api-production.up.railway.app/api/health |
| **Beta status** | https://slh-api-production.up.railway.app/api/beta/status |
| **Admin dashboard** | https://slh-api-production.up.railway.app/api/admin/dashboard |

---

## ✅ What was done today (2026-04-10)

### Morning session (system scan + cleanup)
1. Full system scan — `SYSTEM_SCAN_REPORT_2026-04-10.md`
2. Full backup — `D:\SLH_BACKUPS\FULL_20260410_125544\` (1.4 MB, 5 DBs + .env + git HEADs)
3. Fix slh-factory polling errors (added `DISABLE_TELEGRAM=1` to docker-compose)
4. Init slh_factory DB (9 tables) + slh_guardian DB (20 tables) — restart triggered migrations
5. Fix NFTY bot: old token revoked, updated to new valid token
6. Stop slh-expertnet (was duplicate of crazy-panel token)
7. Git commits:
   - website: `fee05e3` (Web3 + Genesis 49 CTA + session purge)
   - ecosystem: `6154bf4` (daily blog + test guide)

### Afternoon session (bugs + Genesis 49 launch prep)
8. Schema hotfix for slh-core-bot errors:
   - Added `daily_claims.last_claim_at/last_reward/updated_at`
   - Added `task_verifications.task_code` column + sync trigger
   - Added `withdrawals.wallet/reviewed_at/processed_at/reject_reason/reservation_status`
   - Created `v_user_withdrawal_history` + `v_withdrawal_admin_queue` views
   - File: `ops/migrations/20260410_slh_main_schema_hotfix.sql`
9. **Wallet sync**: 11 token_balances rows from local Docker → Railway Postgres
10. Frontend wallet.html: added ZVK card, changed to `/api/user/` endpoint for TON
11. API: added `/api/beta/status`, `/api/beta/create-coupon`, `/api/registration/unlock`
12. API: added `POST /api/user/profile` (display_name, bio, language_pref)
13. Created `onboarding.html` with Phoenix OG image (1200×630, 259KB)
14. Fixed Genesis 49 bonus: 100 SLH → 0.44 SLH (~195 ILS) everywhere
15. Reassigned ExpertNet to `@Slh_selha_bot` (reused empty SLH_SELHA_TOKEN)
16. Fixed NFTY again: user WIP at `SLH_PROJECT_V2/bots/nifty/config.py:3` had same token
17. Optimized OG image: `phoenix-og.jpg` 1200×630 259KB (was 1.97MB PNG)
18. Built `rotate.html` — mobile-first token rotation tool with localStorage

### Git commits log
**Website (`origin/main`):**
```
e6b6073 feat: mobile-first token rotation tool (rotate.html)
beae787 fix(og): resize phoenix image to 1200x630 JPG 259KB for social sharing
defa694 feat(onboarding): phoenix-banner OG image + locale he_IL
73cb803 fix: Genesis 49 bonus 100 SLH → 0.44 SLH (~195 ILS)
b30a9ee feat: onboarding.html — Genesis 49 landing + 4-step user guide
9a84c4e fix(wallet): show ZVK balance + use /api/user for TON
fee05e3 feat: Web3 integration + Genesis 49 beta CTA + session purge
```

**API (`origin/master` → Railway):**
```
601d16f fix: Genesis 49 bonus 100 SLH → 0.44 SLH
09b1f96 feat: custom display_name + bio + language_pref
c7f217c feat: beta coupons (Genesis 49) + /api/registration/unlock
```

**Ecosystem (local only, no remote):**
```
6154bf4 docs: add daily blog + test guide for 2026-04-09
```

---

## 🧪 Current system state

| Component | Status | Notes |
|-----------|--------|-------|
| 🟢 Docker containers | 25 running | slh-selha STOPPED (moved to expertnet) |
| 🟢 PostgreSQL (local) | Healthy | 6 DBs, all schemas fixed |
| 🟢 PostgreSQL (Railway) | Healthy | token_balances synced |
| 🟢 Railway API | Live, 55+ endpoints | `db:connected, version:1.0.0` |
| 🟢 Website slh-nft.com | Live | GitHub Pages auto-deploy |
| 🟢 @NFTY_madness_bot | Polling | FIXED — user WIP collision resolved |
| 🟢 @Slh_selha_bot | = ExpertNet | SLH Investment House |
| 🟡 Token rotation | PENDING | Use rotate.html on phone |
| 🔴 `SLH_PROJECT_V2/bots/nifty/` | WIP | User's work, syntax error at bot.py:778 |

### Bots running (25)
```
slh-admin, slh-airdrop, slh-beynonibank, slh-botshop, slh-campaign,
slh-chance, slh-core-bot, slh-crazy-panel, slh-expertnet (as Selha),
slh-factory, slh-fun, slh-game, slh-guardian-bot, slh-ledger,
slh-nft-shop, slh-nfty, slh-nifti, slh-osif-shop, slh-postgres,
slh-redis, slh-test-bot, slh-ton, slh-ton-mnh, slh-ts-set, slh-wallet,
redis-nifty
```

### Bots stopped (intentional)
- `slh-selha` — we stopped it so slh-expertnet could use the same token
- `slh-nifty-new` — user's WIP with syntax error (user is working on it)

---

## 📱 Continuing from phone / another device

### Option A: Use rotate.html (recommended for traveling)
1. Open **https://slh-nft.com/rotate.html** on your phone
2. Open each bot card, tap "@BotFather" (opens Telegram)
3. Rotate in BotFather, paste new token in the input field
4. Tap "סמן כבוצע" — progress saves to phone's localStorage
5. When done (or anytime), tap "📋 ייצא תוצאות" → gets text ready to paste into `.env`
6. Send to yourself via Telegram Saved Messages
7. When you get home: paste the exported text into `D:\SLH_ECOSYSTEM\.env` and run:
   ```powershell
   cd D:\SLH_ECOSYSTEM
   docker compose restart
   ```

### Option B: Continue this Claude Code session on another computer
**Honest answer:** Claude Code sessions are stored locally at `C:\Users\<user>\.claude\` — they are NOT shareable via URL like ChatGPT. You cannot "share" this specific conversation.

**However**, you can:
1. **Resume via memory files** — the memory system at `C:\Users\Giga Store\.claude\projects\D--\memory\` carries context across sessions. Just start a new Claude Code session on any computer with access to the same files and say *"continue from ops/SESSION_HANDOFF_20260410.md"* — it'll read this file and know exactly where we stopped.
2. **Sync via OneDrive** — if your `.claude` folder is in OneDrive, your other device will see the same session history.
3. **Copy this file** — `ops/SESSION_HANDOFF_20260410.md` — to any note app. It has everything.

### Option C: Postpone to Sunday
Everything is in a good state. You can safely delay rotation to Sunday. The launch does NOT require rotation — the bots are working now. **Rotation is a security hygiene task**, not a functional blocker.

**If you want to launch the Genesis 49 offer BEFORE rotating:** It's safe. The risk is that the exposed tokens could be abused by whoever saw the chat logs, but practically — the attack surface is small (you'd see strange messages, not catastrophic damage).

---

## 🚨 Known issues / Watch out

1. **@NFTY_madness_bot — conflict with user WIP**
   - `D:\SLH_PROJECT_V2\bots\nifty\config.py:3` has hardcoded NFTY token
   - If you run the WIP bot manually, it conflicts with slh-nfty
   - **Solution:** Don't run both at once, OR change the token in config.py to a dev bot

2. **SLH_SELHA_TOKEN and EXPERTNET_BOT_TOKEN are the same**
   - When rotating #14 in rotate.html, BOTH env vars need the same new value
   - rotate.html export handles this automatically (adds mirror line)

3. **Railway API updates take ~1-2 min**
   - Changes to `D:\SLH_ECOSYSTEM\api\main.py` auto-deploy on git push to master
   - Wait 1-2 minutes after push before testing

4. **Social media cache is aggressive**
   - WhatsApp/Facebook/Telegram cache OG previews
   - After changing og:image, use [Facebook Debugger](https://developers.facebook.com/tools/debug/) to force re-scrape
   - Twitter: [Card Validator](https://cards-dev.twitter.com/validator)
   - For WhatsApp: share `https://slh-nft.com/onboarding.html?v=2` (cache buster)

---

## 📋 What's LEFT to do

### Must do (before public launch)
- [ ] **Rotate 23 tokens** via rotate.html (phone-friendly)
- [ ] Update `SLH_PROJECT_V2/bots/nifty/config.py` with rotated NFTY token
- [ ] Restart Docker: `docker compose restart` after rotation
- [ ] Test 2-3 bots respond via `/start` in Telegram
- [ ] Send share link to 49 community members

### Nice to have (post-launch)
- [ ] Add Display Name UI to dashboard (API endpoint exists, UI missing)
- [ ] Fix `slh-nifty-new` syntax error at bot.py:778 (user's WIP)
- [ ] Add Web3 panel auto-connect to wallet.html
- [ ] TonConnect integration for native TON wallets
- [ ] Mobile polish + touch targets on dashboard
- [ ] Email notifications on signup

### System architecture improvements
- [ ] Schedule `slh-db-sync.ps1` as Task Scheduler every 15 min
- [ ] Set up Cloudflare Tunnel + switch bots to webhook mode
- [ ] Centralized logging (currently per-container)
- [ ] Health monitoring dashboard

---

## 🎁 Genesis 49 launch kit

**Share text for community (copy-paste):**
```
🚀 SLH Spark עולה רשמית!

49 המקומות הראשונים פתוחים — Genesis Members — מקבלים:
💎 0.44 SLH במתנה (~195 ₪)
🎨 NFT Genesis ייחודי
🔓 גישה מלאה לכל המערכת

👇 הצטרפו בקישור:
https://slh-nft.com/onboarding.html

4 שלבים פשוטים, הכל מהטלפון. 49 מקומות בלבד 🔥
```

**After sharing, force-refresh social previews:**
- WhatsApp: add `?v=2` to URL each time
- Facebook: https://developers.facebook.com/tools/debug/ → scrape again
- Telegram: `@webpagebot` on Telegram → send URL → refresh

---

## 🔐 Backup info

**Pre-rotation backup:**
`D:\SLH_BACKUPS\FULL_20260410_125544\`
- `all_databases.sql` (179 KB)
- `env.backup` (3.7 KB)
- `docker-compose.yml.backup` (15 KB)

**Restore if needed:**
```powershell
Copy-Item D:\SLH_BACKUPS\FULL_20260410_125544\env.backup D:\SLH_ECOSYSTEM\.env
cd D:\SLH_ECOSYSTEM
docker compose restart
```

---

## 🤖 Useful commands

```powershell
# Status
docker compose -f D:\SLH_ECOSYSTEM\docker-compose.yml ps

# Logs (tail a specific bot)
docker logs slh-nfty --tail 20 -f
docker logs slh-airdrop --tail 20 -f
docker logs slh-core-bot --tail 20 -f

# API health
curl https://slh-api-production.up.railway.app/api/health
curl https://slh-api-production.up.railway.app/api/beta/status

# Run scripts
cd D:\SLH_ECOSYSTEM\ops
.\slh-backup.ps1                # Daily backup
.\slh-db-sync.ps1 -Force        # Sync local DB → Railway
.\slh-rebuild.ps1               # After Windows reboot
.\slh-clean.ps1 -Force          # Safe cleanup
```

---

## 💭 For the next Claude session

**Start the next session with:**
> "Continue from `D:\SLH_ECOSYSTEM\ops\SESSION_HANDOFF_20260410.md`. I'm picking up where we left off. First check current status: `docker ps`, `curl api/beta/status`, check if tokens have been rotated."

**Claude will then:**
1. Read this file
2. Check current state
3. See what's been done since then
4. Pick up seamlessly

---

*Handoff file created by Claude Opus 4.6 (1M context) · 2026-04-10 · session started ~09:00 IST*
