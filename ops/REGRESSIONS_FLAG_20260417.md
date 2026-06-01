# 🚨 REGRESSIONS FLAGGED — 2026-04-17 morning closure

> **UPDATE 2026-04-17 evening:** `docker-compose.yml` regression is RESOLVED.
> Current working tree matches HEAD — 454 lines, 24 bot services. Safe to use.

## 1. `docker-compose.yml` — ✅ RESOLVED

**Morning state:** working tree was reduced to 58 lines (postgres, redis, ledger, nfty, device-registry only).
**Evening state:** working tree is back to 454 lines with all 24 bot services. `git diff HEAD -- docker-compose.yml` is clean.

**Osif decision:** No action needed — the full compose is the active working file.

If you ever need to restore a minimal compose again: `git show HEAD:docker-compose.yml > docker-compose.full.yml` then edit as needed.

## 2. `shared/bot_template.py` — ⚠ STILL OPEN

Still 52 lines (ledger-only, hardcoded `SLH_LEDGER_TOKEN`) instead of the generic 241-line template.

**Bugs detected:**
- Line 41: `"Device OK\`nToken: "` — PowerShell escape, not Python. As-is prints a literal backtick-n.
- Hardcoded `SLH_LEDGER_TOKEN` means this template can no longer be used generically by other bots.

**Osif decision still required:** either
- (a) restore the old `shared/bot_template.py` and put this new code in `ledger-bot/bot.py`, or
- (b) confirm that the new minimal version is the intended new baseline and no other bot uses it.

## Recommendation
`docker-compose.yml` — closed. `shared/bot_template.py` — still don't `git add` in the closure commit.
