# 📦 Uncommitted Files Triage — 2026-04-17

> **56 files remaining after gitignore expansion.**
> Categorized by risk + batch-commit readiness.

## ✅ BATCH 1: New code — bot directories (ready to commit)
```
campaign-bot/      ← Campaign SaaS bot (@Campaign_SLH_bot)
device-registry/   ← ESP32 registration service (port 8090)
expertnet-bot/     ← ExpertNet premium
match-bot/         ← Match/dating bot
nfty-bot/          ← NFTY bot
tonmnh-bot/        ← TON-MNH bridge bot
userinfo-bot/      ← User info bot
wellness-bot/      ← Wellness bot
osif-shop/         ← Shop bot
```
**Suggested commit:** `feat(bots): add campaign/device-registry/expertnet/match/nfty/tonmnh/userinfo/wellness/osif-shop bot codebases`

**BEFORE committing — verify:**
- No `.env` or hardcoded tokens inside
- Dockerfile references match dockerfiles/ entries
- Each has its own Dockerfile or uses shared template

## ✅ BATCH 2: New API routes + infra
```
api/Dockerfile
api/Procfile
api/railway.json
api/requirements.txt
api/routes/                             ← new routes dir
api/patch_wallet_security.py
api/secure_wallet.py
api/run_tamagotchi_advanced.py
api/community_backend_scan.txt          ← scan output, probably gitignore
```
**Suggested commit:** `feat(api): deployment configs + security routes + new modules`

## ✅ BATCH 3: Shared payment/wallet modules
```
shared/__init__.py
shared/community_api.py
shared/register_api.py
shared/slh_payments/ledger.py
shared/slh_payments/promotions.py
shared/slh_payments/referrals.py
shared/slh_token_abi.json
shared/wallet_api.py
shared/wallet_engine.py
admin-bot/shared/slh_payments/ledger.py  ← duplicate of above?
```
**Suggested commit:** `feat(shared): payments + wallet + community/register modules`

**Verify:** `admin-bot/shared/slh_payments/ledger.py` is it a duplicate or extension of `shared/slh_payments/ledger.py`?

## ✅ BATCH 4: Dockerfile variants per bot
```
dockerfiles/Dockerfile.airdrop
dockerfiles/Dockerfile.campaign
dockerfiles/Dockerfile.expertnet
dockerfiles/Dockerfile.match
dockerfiles/Dockerfile.nfty
dockerfiles/Dockerfile.osifshop
dockerfiles/Dockerfile.tonmnh
dockerfiles/Dockerfile.wellness
```
**Suggested commit:** `feat(docker): per-bot Dockerfiles (airdrop/campaign/expertnet/match/nfty/osifshop/tonmnh/wellness)`

## ✅ BATCH 5: Setup scripts
```
repair-and-upgrade-nfty.ps1
setup-nfty-bot.ps1
```
**Suggested commit:** `chore(scripts): nfty bot setup + repair scripts`

## ⚠️ BATCH 6: Root docs (reports/plans — probably safe)
```
CLEANUP_REPORT_2026-04-10.md
PROJECT_MAP.md
STATUS_REPORT.md
SYSTEM_SCAN_REPORT_2026-04-10.md
TEAM_TASKS.md              ← NEW, created this session
TESTING_PLAN.md
TOKEN_AUDIT.md             ← ⚠️ check — might have live tokens
```
**Suggested commit:** `docs: root-level project plans + cleanup report`

**Verify first:** open TOKEN_AUDIT.md — if real tokens listed, gitignore it instead.

## ⚠️ BATCH 7: Assets
```
assets/app/
assets/ascii_branding.txt
assets/banners/
assets/esp32/
assets/promo/
```
**Decision needed:** Are these binary/large files (images)? Suggest moving to CDN or keeping if <5MB total.

## 🔴 MODIFIED — needs review (don't auto-commit)
```
M docker-compose.yml      ← likely contains real changes (services config)
M shared/bot_template.py  ← related to ledger-bot fix earlier today
```
**Action:** `git diff docker-compose.yml` and `git diff shared/bot_template.py` — verify changes are intentional.

## ❌ IGNORE (submodule drift, safe to leave)
```
 m backups/_restore/20260322_074442/SLH_PROJECT_V2
 m backups/_restore/20260322_074442/TerminalCommandCenter
 m botshop
```
Submodules showing drift. Not blocking. Can be updated with `git submodule update --remote` if desired.

## 🎯 Recommended execution order
1. **Verify TOKEN_AUDIT.md** — if safe, proceed
2. **Run `git diff` on 2 modified files** — confirm intent
3. **Commit Batch 4** (Dockerfiles) — low risk, high signal
4. **Commit Batch 2** (API infra) — Railway needs these
5. **Commit Batch 3** (shared modules) — other bots depend
6. **Commit Batch 1** (bot directories) — big batch, biggest payoff
7. **Commit Batch 5 + 6 + 7** — docs + scripts + assets

Total commits expected: 7 clean commits.
Estimated time: 10 minutes with verifications.
