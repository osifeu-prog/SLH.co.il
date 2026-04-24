# Post-Mortem — 2026-04-24 Session

**Session:** `D:\SLH.co.il\` takeover + hardening by Claude (Opus 4.7)
**Duration:** ~2:00 local (start) → ~23:59 (end of 24.4) → carrying into 25.4
**Outcome:** 8 commits shipped, bot operable, landing page live. Along the way: **3 regressions** I created and caught late. This doc is so next agent / next session doesn't repeat them.

---

## Regression 1 — `www.slh.co.il` down for ~40 minutes

### What happened
- Commit `0d05f09` removed `healthcheckPath: "/health"` from `railway.json`.
- **Rationale at time:** `bot.py` has no HTTP server, so `/health` always failed, meaning every deploy was failing the check and Railway was rolling back to the last working image.
- **What I missed:** the rollback was serving as an accidental safety net. The Railway project has 3 Python services (`monitor.slh`, `slh-bot`, `SLH.co.il`) that all build from `railway.json`. The `SLH.co.il` service has **no `TELEGRAM_BOT_TOKEN`** env var (it's supposed to serve static HTML, not run the bot).
- When healthcheck was active: `bot.py` exited 1 on missing token → healthcheck failed → rollback → old working image kept serving www.slh.co.il.
- When I removed healthcheck: the broken container became the "active" deploy, Railway returned 502 to visitors.

### Evidence
- Commit: `0d05f09` (railway.json change)
- User report: screenshot of Railway 502 "Application failed to respond"
- Fix: commit `50ece9e` — `bot.py` now falls back to `http.server` serving `docs/` when `TELEGRAM_BOT_TOKEN` is missing.

### Root cause
Single `railway.json` shared by 3 services with different responsibilities. The `startCommand: python bot.py` was correct only for 2 of them.

### Prevention
1. **Architectural fix (not done yet):** each service should have its own Custom Start Command in Railway dashboard (overrides `railway.json`). `SLH.co.il` service start command should be `python -m http.server $PORT --directory docs`.
2. **Process fix:** before changing `railway.json`, list all services that consume it (`railway status --json`). Map the effect on each.
3. **Detection fix:** `ops/verify.ps1` now curls the website explicitly — will catch this class of regression immediately after any deploy.

---

## Regression 2 — bot token leaked in chat, 3 rotation cycles

### What happened
- Session start: user pasted full TELEGRAM_BOT_TOKEN into chat (policy violation per `feedback_never_paste_secrets.md`).
- I flagged it, recommended rotation.
- User rotated at BotFather, but then **pasted the new token into chat too** to show me what to put in Railway.
- I flagged again, recommended rotation again.
- Separately, user pasted an OpenAI `sk-proj-...` key.

### Evidence
- 3 separate tokens visible in the conversation transcript
- Each one required its own `@BotFather` revoke + `@platform.openai.com/api-keys` delete

### Root cause
Helpful user muscle memory: when answering "should I put it here or there?" they pasted the actual value so I could confirm "yes, that one". But any value pasted is already compromised.

### Prevention
1. `.githooks/pre-commit` (commit `0c82bce`) now blocks any commit containing a token pattern. First line of defense against accidental commits.
2. Going forward, when asking "should I put token X in service Y?" — **never** include the value. Describe: "the token I got from BotFather 30 minutes ago" or "the one with bot_id 8724910039".
3. `ops/rotate-token.md` (commit `215335f`) explicitly lists the "never paste" rule as step 0.

### Still-outstanding exposure
- Transcript still contains 3 tokens (can't retroactively scrub Claude conversation history).
- The rotations revoked the tokens at their source, so the leaked values are inert — but this only works because user DID rotate. If the chat is viewed later by someone assuming the tokens are live, no harm.

---

## Regression 3 — Markdown ate `_` in bot commands

### What happened
- All commands listed in bot message responses used `parse_mode='Markdown'`.
- Telegram legacy Markdown treats `_text_` as italic.
- Commands like `/add_roi`, `/last_roi`, `/feedback_ai`, `/summary_today` contain one underscore.
- In the rendered message, `_roi [amount]\n/last_` pair matches italic rules → visible text became `/addroi`, `/lastroi`, `/feedbackai`, `/summarytoday`.
- User tapped the rendered command → sent `/addroi` → bot has no handler for that → silent no-op.
- Symptom: user hit `/menu → ROI → /addroi`, got nothing, assumed bot dead. Bot was fine — Markdown was corrupting the links.

### Evidence
- Transcript of user's test session 14:10-14:11 — multiple commands sent, no response.
- `/docs` output showing commands without underscores.

### Root cause
Mixing unescaped underscores with Markdown parse_mode is a known Telegram bot pitfall. Not project-specific, not a new bug — just one I didn't foresee.

### Fix + prevention
- Commit `d69ed37`: wrap every command in backticks `` `/add_roi` ``. Code spans don't parse Markdown, so underscores survive. Telegram still auto-linkifies `/commands` inside code spans.
- Better long-term: move to `parse_mode='HTML'` with `<code>/add_roi</code>` — HTML escaping is more predictable than legacy Markdown. Not done this session (no need; current fix works).
- Detection: any command-containing message should go through a linter step. Can be added to `ops/verify.ps1` in a future pass.

---

## Lessons beyond these 3

### Process
1. **Never say "system ready" without end-to-end UX test.** The `FINAL_STATUS_20260424.md` written mid-session was premature — it listed "all four checks passed" but only covered infrastructure layer, not UX. User rightly called this a false positive.
2. **Verify handoff claims against live state before coding.** `project_slh_co_il` memory saved this session documents: handoff claimed the bug was `registered_at` → `first_seen`, but the actual prod schema had more divergence (`first_name` missing, `feedback.created_at` renamed to `timestamp`, `user_id` TEXT in feedback). Only caught by running `information_schema.columns` against prod first.
3. **Match action to authorization.** User explicitly bounded me to `D:\SLH.co.il\`. I respected that. Crossing the line (to fix FAB overlap on slh-nft.com, to wire telegram_gateway.py, to build a cross-project control center) requires explicit re-authorization per task, not just implicit "trust you".

### Tactical
1. Housekeeping: no `.gitignore` existed at session start. Created one; also added `.env.example`. Dev-only files (`fix_db.py`, `fix_user_id_type.py`) now ignored — won't accidentally get committed with hardcoded credentials.
2. Git attribution: local `git config` is still placeholder (`Your Name <your.email@example.com>`). Every commit this session used env-var override to attribute to `Osif Kaufman Ungar`. Mentioned in memory but still a persistent config that should be fixed globally.
3. Logs leak tokens: Python httpx default logging prints request URLs, which for Telegram includes the bot token. Every log line for every getUpdates has the full token. Not addressed this session — deferred for a future pass (log filter or quiet httpx).

---

## Commits index for this post-mortem

| Commit | Role |
|--------|------|
| `0d05f09` | The regression (removed healthcheck) |
| `50ece9e` | The fix (static fallback in bot.py) |
| `d69ed37` | Markdown underscore fix |
| `215335f` | Runbook + rotate-token docs |
| `0c82bce` | Pre-commit secret hook |

Next session hand-off: `ops/DISPATCH_20260425.md` (status + routing).
