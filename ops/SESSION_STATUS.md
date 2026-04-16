# SLH ECOSYSTEM — LIVE SESSION STATUS
> **Single Source of Truth.** Every agent updates this before ending a session.

**Last update:** 2026-04-17 01:45 by Claude Opus 4.6
**Owner:** Osif Ungar (TG 224223270)

---

## ✅ Resolved since last session
- **Bug debug system live** — `/bug-report.html` + `/admin-bugs.html` + Telegram alerts to admin on every new bug + PATCH `/api/admin/bugs/{id}/status` + auto-capture JS errors via `shared.js`
- **Git remote repaired** — root repo now `github.com/osifeu-prog/slh-api.git` (was placeholder)
- **Both repos pushed:**
  - root: `39f490f` (ops docs + gitignore) + `74cdcb7` (bug system API)
  - website: `cd54d24` (admin-bugs + FAB + auto-capture)
- **.gitignore expanded** — backups/secrets excluded (131 → 56 untracked)
- **.claude/settings.json** — 29 read-only tools auto-approved
- **ledger-bot** — responding to /start, /deals, /promo, /premium (token fixed by user)
- **Admin key rotation prepared** — new key generated + saved locally (not yet deployed to Railway)

## 🔴 Active blockers

### 1. Bot command collision (CRITICAL — UX bug)
Multiple bots answering the same `/start@Campaign_SLH_bot` message. `SLH_AIR` responds "פקודה לא מוכרת" to commands explicitly addressed to `Campaign_SLH_bot`. **Each bot must check `@botname` suffix and ignore commands not addressed to it.**

**Where:** all bot handlers using aiogram 3.x `Command()` filter — add `prefix="/"` + explicit bot-username check.

### 2. Campaign bot command naming inconsistency
- `/new_survey` vs `/newsurvey` (help shows one, works with another)
- `/contacts` vs `/addcontact` vs `/add_contact`

**Action:** standardize on `/snake_case` across all bots (matches Telegram convention).

### 3. ESP32 register/verify flow
`/register ESP001 0501234567` and `/verify ESP001 242641` — no bot response seen in Telegram transcripts. Either:
- Handler not registered in bot
- Bot not receiving from BotFather (wrong token)
- Duplicated message ("/verify ESP001 242641/verify ESP001 242641") suggests keyboard/typing issue

**Next:** check which bot should handle ESP registration (device-registry service runs on :8090).

### 4. Admin key still on default
Railway env `ADMIN_API_KEYS` = `slh2026admin` (known from public chat history). **New key ready:** `slh_admin_hgaBj2T9k8T8Hmm5pC_794J-4UaDG6ce` saved at `~/.claude/slh-secrets.json`. Needs:
1. Add to Railway Variables → `ADMIN_API_KEYS=slh_admin_hgaBj2T9k8T8Hmm5pC_794J-4UaDG6ce,slh2026admin` (dual, rotate grace period)
2. Update localStorage in browser: open `/admin.html` → logout → login with new key
3. Remove old `slh2026admin` from Railway after 24h

### 5. Still 56 uncommitted files in root repo
See `ops/TRIAGE_REPORT.md` for full categorization.

## 🟡 Known issues (not blocking)
- `docker-compose.yml` modified (uncommitted) — check intent before commit
- `shared/bot_template.py` modified (uncommitted) — probably related to ledger-bot fix
- `backups/_restore/` submodules showing as modified (safe to ignore)

## 🎯 Next priorities (in order)
1. **Fix bot command collision** — single bot responds to `/cmd@this_bot` only
2. **Rotate admin key** (3 steps above)
3. **Commit bot code batches** (expertnet-bot/, match-bot/, nfty-bot/, campaign-bot/, wellness-bot/, tonmnh-bot/, osif-shop/, userinfo-bot/)
4. **Commit API routes/** and `shared/` payment modules
5. **ESP32 flow** — wire up device-registry to whichever bot handles registration

## 📡 Live System Health
| Component | Status | Evidence |
|-----------|--------|----------|
| API | ✅ OK | `/api/health` → `{"status":"ok","db":"connected","version":"1.0.0"}` |
| Website | ✅ OK | slh-nft.com loading, FAB button mounted |
| ledger-bot | ✅ OK | /start + /premium flow working |
| Campaign bot | 🟡 Live but buggy | Conflicts with SLH_AIR on same messages |
| ESP32 flow | 🔴 Unknown | No response seen to /register /verify |

## 🔑 Active sessions / agents
- **Claude Opus 4.6** (this) — web + API + infra + docs
- **SLH Core Assistant** (other session, Telegram) — code-generation helper, diagnostics
- **Giga Store (Osif)** — ESP32 + Docker operator
