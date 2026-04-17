# 🚨 REGRESSIONS FLAGGED — 2026-04-17 morning closure

> **Do NOT blind-commit these two files. They are major simplifications (possibly accidental) from the original.**

## 1. `docker-compose.yml` — went from 25 services → 3

**Before (HEAD):** full stack — core-bot, guardian, botshop, wallet, factory, fun, admin, expertnet, airdrop, campaign, game, ton-mnh, slh-ton, ledger, osif-shop, nifti, chance, nfty, selha, userinfo, ts-set, crazy-panel, nft-shop, beynonibank, test-bot + postgres + redis. Total ~445 lines.

**Now (working tree):** only `postgres`, `redis`, `ledger-bot`, `nfty-bot`, `device-registry`. 58 lines.

**Risk:** committing this blows away the deployment topology for 23 bots. If intentional, it's a Phase-2 simplification that needs a dedicated commit + migration note. If accidental, it's a disaster.

**Action required from Osif:** decide — revert, keep, or split into a "phase-2 minimal compose" and restore the full compose as `docker-compose.full.yml`.

## 2. `shared/bot_template.py` — went from 241 lines → 52

**Before (HEAD):** generic bot template with payment gate, pricing, promo engine, referral engine, `/start`, `/status`, `/premium`, `/deals`, `/mylink`, `/referral`, `/help`. Driven by `BOT_KEY` + `BOT_DISPLAY_NAME` env vars.

**Now (working tree):** ledger-only bot — `/start`, `/register`, `/verify`. Hardcoded to `SLH_LEDGER_TOKEN`. No payment, no referral, no promo, no premium.

**Bugs detected:**
- Line 41: `"Device OK\`nToken: "` — that's a PowerShell escape, not Python. Should be `\n` (actual newline). As-is it prints a literal backtick-n.
- Hardcoded `SLH_LEDGER_TOKEN` means this template can no longer be used generically by other bots — every bot that sources this will now be ledger-bot.

**Risk:** if any other bot uses `shared/bot_template.py` as its entrypoint, they will either crash (no SLH_LEDGER_TOKEN) or all answer as ledger-bot (token collision).

**Action required from Osif:** either
- (a) restore the old `shared/bot_template.py` and put this new code in a new file like `ledger-bot/bot.py`, or
- (b) confirm that the new minimal version is the intended new baseline and no other bot uses it.

## Recommendation
Leave both modified files uncommitted in the working tree until Osif decides. Gitignore is NOT the answer here (the file needs to stay tracked), just don't `git add` them in the closure commit.
