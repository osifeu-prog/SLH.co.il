# SLH Ecosystem - Security Fix Plan
**Date:** 2026-04-27
**Author:** Claude (Cowork mode session)
**Status:** P0 fixes started, awaiting user action for Railway env vars

---

## Executive Summary

Full scan revealed **3 CRITICAL** issues, **6 HIGH** issues, and several P2/P3 cleanup items.
The single most important issue: **Railway env vars `JWT_SECRET` and `ADMIN_API_KEYS` are MISSING**.
Without them, the deployed API runs with insecure default values, allowing anyone with read access
to the codebase to forge admin JWTs.

---

## ✅ Completed in this session

### 1. Removed hardcoded `slh_ceo_2026` password (main.py:8471)
**Before:**
```python
""", 7757102350, "tzvika", hash_admin_password("slh_ceo_2026"), "Tzvika Kaufman", "ceo", 224223270)
```
**After:**
```python
""", 7757102350, "tzvika", hash_admin_password(os.getenv("INITIAL_TZVIKA_PASSWORD", "change_me_on_first_login_" + secrets.token_hex(4))), "Tzvika Kaufman", "ceo", 224223270)
```
Now matches the pattern used for Osif on line 8465. Tzvika will get a random one-time password on first DB seed unless `INITIAL_TZVIKA_PASSWORD` env var is set.

### 2. Fixed docker-compose nfty-bot DB password (line 358)
**Before:**
```yaml
DATABASE_URL: postgresql://postgres:slh_secure_2026@postgres:5432/slh_main
```
**After:**
```yaml
DATABASE_URL: postgresql://postgres:${DB_PASSWORD:-slh_secure_2026}@postgres:5432/slh_main
```
Now consistent with all other bot services in the file.

---

## 🔴 P0 - CRITICAL (User action required)

### A. Add missing Railway environment variables

**Service: SLH.co.il** (project `diligent-radiance` / `production`)
Currently has only 5 vars: `DATABASE_URL`, `DATABASE_PUBLIC_URL`, `REDIS_URL`, `REDIS_PUBLIC_URL`, `OPENAI_API_KEY`

**Add these:**
```
JWT_SECRET=<generate with: python -c "import secrets; print(secrets.token_hex(32))">
ADMIN_API_KEYS=<comma-separated list of strong keys, e.g. 'key1,key2'>
ENCRYPTION_KEY=<generate with: python -c "import secrets; print(secrets.token_hex(32))">
ADMIN_BROADCAST_KEY=<generate with: python -c "import secrets; print(secrets.token_urlsafe(32))">
INITIAL_ADMIN_PASSWORD=<strong password for Osif on first DB seed>
INITIAL_TZVIKA_PASSWORD=<strong password for Tzvika on first DB seed>
ADMIN_USER_ID=224223270
```

**How to add (Railway dashboard):**
1. Open https://railway.com/project/97070988-27f9-4e0f-b76c-a75b5a7c9673/service/63471580-d05a-41fc-a7bb-d90ac488abfd/variables
2. Click "New Variable" for each
3. After adding all, the service will auto-redeploy

**Verify after deploy:**
```bash
curl https://slhcoil-production.up.railway.app/api/health
curl -X POST https://slhcoil-production.up.railway.app/api/admin/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"osif","password":"<INITIAL_ADMIN_PASSWORD>"}'
```

### B. Rotate the 31 exposed Telegram bot tokens

The `.env` file currently in `D:\SLH_ECOSYSTEM\` contains 20+ live bot tokens.
Per CLAUDE.md, only 1/31 has been rotated (GAME_BOT_TOKEN, 2026-04-17).

**Process per bot:**
1. Open Telegram, message @BotFather → `/mybots` → select bot → "API Token" → "Revoke current token"
2. Get new token
3. Update `.env` with new value
4. Restart the bot: `docker compose restart <bot-service-name>`
5. Update Railway env vars if the bot uses any

**Bots needing rotation (per `.env`):**
- CORE_BOT_TOKEN, GUARDIAN_BOT_TOKEN, BOTSHOP_BOT_TOKEN, WALLET_BOT_TOKEN, FACTORY_BOT_TOKEN
- FUN_BOT_TOKEN, ADMIN_BOT_TOKEN, AIRDROP_BOT_TOKEN, CAMPAIGN_BOT_TOKEN
- TON_MNH_TOKEN, SLH_TON_TOKEN, LEDGER_BOT_TOKEN, OSIF_SHOP_TOKEN
- NIFTI_BOT_TOKEN, CHANCE_BOT_TOKEN, NFTY_MADNESS_TOKEN, TS_SET_TOKEN
- CRAZY_PANEL_TOKEN, NFT_SHOP_TOKEN, BEYNONIBANK_TOKEN, TEST_BOT_TOKEN, etc.

### C. Rotate Binance Exchange API keys

**.env contains LIVE Binance trading credentials:**
```
EXCHANGE_API_KEY=g0XGwqsVsj1JOvRokmJfriFxsJZJd1OWh9qKOQgQiqqn53amHqTWaUNvgndd2QDi
EXCHANGE_SECRET=uigqCBobRvv9LHoPR6u5OA49TQABDwxdJylbGmYgn2ZWZwtES8ttlWAhVfYCLrPI
```

**Action:** Login to Binance → API Management → Delete this key → Create new one with IP restriction → Update .env.

---

## 🟠 P1 - HIGH (Code-level fixes - need decision before applying)

### D. Add JWT auth to 3 sensitive endpoints
**Currently unauthenticated** (anyone with a telegram_id can query):

| Line | Endpoint | What it returns |
|------|----------|-----------------|
| 2626 | `GET /api/user/wallet/{user_id}` | Linked Web3 wallet address |
| 2767 | `GET /api/user/{telegram_id}` | Profile + balances + deposits |
| 4653 | `GET /api/user/full/{telegram_id}` | EVERYTHING (most sensitive) |

**Recommended fix** (using existing `get_current_user_id` at line 838):
```python
@app.get("/api/user/full/{telegram_id}")
async def get_user_full(telegram_id: int, current_user: int = Depends(get_current_user_id)):
    if current_user != telegram_id:
        raise HTTPException(403, "Cannot access another user's data")
    # ... existing code
```

**⚠️ WHY NOT APPLIED YET:** Adding required auth could break the website if any frontend page calls these endpoints without an `Authorization: Bearer <jwt>` header. Need to:
1. Audit website JS for all calls to `/api/user/`
2. Update those calls to include the JWT from `localStorage.slh_user_jwt`
3. THEN apply the auth requirement

**Audit command:**
```bash
grep -rn "/api/user/" D:\SLH_ECOSYSTEM\website\
```

### E. Remove `.env` backup files from project root

```
.env.backup-20260416-192749
.env.backup.20260417_004938
.env.bak_20260422_160522
.env.corrupted_20260417_020926
```

These could contain old secrets. If any was ever committed to git, those secrets need rotation too.

**Action (PowerShell):**
```powershell
cd D:\SLH_ECOSYSTEM
git log --all --full-history -- ".env*" | Select-String "commit"
# If any commits show up, those secrets WERE pushed → rotate everything in them
Remove-Item .env.backup-20260416-192749, .env.backup.20260417_004938, .env.bak_20260422_160522, .env.corrupted_20260417_020926
```

### F. Remove test/demo code from production website

- `D:\SLH_ECOSYSTEM\website\admin\reality.html` - contains `test_or_fake`, `founder_self_test` references
- `D:\SLH_ECOSYSTEM\website\encryption.html` - contains `demoFix`, `demoLoad`, `demoScramble` functions
- `D:\SLH_ECOSYSTEM\website\admin.html:531` - TODO marker for `LLOYDS_INSURANCE`

These should be moved behind a `?debug=1` query param check or deleted entirely.

---

## 🟡 P2 - Tech Debt

### G. Update CLAUDE.md with corrected facts
**Outdated in CLAUDE.md:**
- "API Version: 1.1.0 (113 endpoints)" → actually **~230 endpoints**
- "main.py ~7000 lines" → actually **11,765 lines**
- "Pages: 43 HTML" → actually **140+ HTML pages** (60 in root + subdirectories)
- "2 git repos" → actually **3 repos**: slh-api, SLH.co.il, osifeu-prog.github.io
- API URL `slh-api-production.up.railway.app` → Railway is now connected to `osifeu-prog/SLH.co.il` repo, deployed to `slhcoil-production.up.railway.app` and `www.slh.co.il`

### H. Clean up backup files cluttering root

```
docker-compose.yml.backup-20260416-192200
docker-compose.yml.backup-20260416-220545
docker-compose.yml.backup.20260417_004938
docker-compose.yml.bak-secure-fix
docker-compose.yml.before-fix
docker-compose.yml.regressed-58lines.bak
main.py.bak_20260422_162309
website/js/shared.js.backup_20260425_220656
website/js/shared.js.backup_20260425_130658
```

Move all to `_backups/` subfolder which already exists.

### I. Migrate bots from polling to webhooks
All 22 bots currently use `MODE=polling`. Webhooks reduce latency and Telegram API load. Plan in `ops/` already exists for this.

### J. Theme switcher and i18n coverage
- Theme switcher: 31/140 pages (22%) - target 100%
- i18n: 57/140 pages (40%) - target 100%

---

## 📋 False Positives Cleared

These were flagged by initial scan but are NOT actual issues:

1. **main.py:9611** - `f"UPDATE expert_domains SET {col} = {col} + 1"` - **whitelisted**: `col` is constrained to either `'votes_for'` or `'votes_against'` (line 9610), and the comment `# SECURITY: whitelisted — 'col' is chosen between two hardcoded literals` confirms it was already audited.

2. **main.py lines 366-372** - `if os.getenv("ADMIN_API_KEY", "slh_admin_2026") == "slh_admin_2026":` - these are **defensive checks** that warn when default values are still in use. This is GOOD code, not a vulnerability.

3. **main.py lines 1101, 1216, 1223, 1225, 2518, 2520** - These all check `if admin_key == "slh_admin_2026"` and **REJECT** that value. Good defensive code.

4. **main.py:5707** - It's a comment listing legacy keys for documentation, not a hardcoded password.

---

## 🚀 Recommended order of operations

1. **TODAY (Osif):** Add Railway env vars (Section A) - 10 minutes, biggest security win
2. **TODAY (Osif):** Run the audit command in Section D to see if frontend uses unauthenticated endpoints
3. **TOMORROW:** Rotate Binance API keys (Section C) - 5 minutes
4. **THIS WEEK:** Rotate the 30 remaining bot tokens (Section B) - one per day is fine
5. **NEXT SESSION:** I can apply auth to the 3 endpoints (Section D) once we know what the frontend does
6. **NEXT SESSION:** Cleanup backups (Section H) and update CLAUDE.md (Section G)

---

## Git commit message for the changes I made

```
security: remove hardcoded passwords + standardize docker-compose

- main.py: replace `slh_ceo_2026` for Tzvika seed with INITIAL_TZVIKA_PASSWORD env var
  (matches existing pattern for Osif at line 8465)
- docker-compose.yml: nfty-bot DATABASE_URL now uses ${DB_PASSWORD:-...} fallback
  for consistency with all other bot services
- ops/SECURITY_FIX_PLAN_2026-04-27.md: full security audit + remediation plan
```

**Run from PowerShell:**
```powershell
cd D:\SLH_ECOSYSTEM
cp api/main.py main.py  # if you also edited api/main.py separately
git add main.py docker-compose.yml ops/SECURITY_FIX_PLAN_2026-04-27.md
git commit -m "security: remove hardcoded passwords + standardize docker-compose"
git push origin master  # or 'main' depending on which repo you're targeting
```

**⚠️ IMPORTANT:** I edited `D:\SLH_ECOSYSTEM\main.py` (root). Per CLAUDE.md the API also has `D:\SLH_ECOSYSTEM\api\main.py`. Verify they're synced:
```powershell
fc D:\SLH_ECOSYSTEM\main.py D:\SLH_ECOSYSTEM\api\main.py
# If different, run: cp D:\SLH_ECOSYSTEM\main.py D:\SLH_ECOSYSTEM\api\main.py
```
