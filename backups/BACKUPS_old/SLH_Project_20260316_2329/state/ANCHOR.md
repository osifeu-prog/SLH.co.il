# SLH_PROJECT_V2 :: ANCHOR

## Current operational truth
- Railway remains the current primary runtime.
- Telegram webhook points to Railway production webhook.
- Public health and healthz endpoints respond successfully.
- The bot is alive and answers /start, /buy, /my_orders.
- However, /buy still showed the legacy store text during validation after the inline UI patch was pushed.
- Therefore the working hypothesis is still partial deployment alignment / worker mismatch during the Railway incident window, not a source-code failure.

## Last confirmed git state
- HEAD commit expected on primary branch:
  - a31033c :: Add Telegram store inline UI and product detail flow
- i18n base exists and compiles.
- purchases handler with inline store flow exists and compiles.
- worker.py and webhook_server.py compile.

## Immediate priority
1. Reconfirm Railway worker + webhook are aligned on the intended deployment after platform stabilization.
2. Re-test in Telegram until the new inline /buy UX is visible.
3. Freeze further UX changes until this is verified.
4. Then move to failover kit and secondary provider planning.

## Telegram functional status
- /start responds
- /buy responds
- /my_orders responds
- Current /buy response still reflects legacy text rendering, not the new inline store UX
- This means runtime is alive, but deployed behavior is not yet the desired patched behavior

## Operational direction
- Primary: Railway
- Emergency fallback: local PC runtime with tunnel + webhook switch
- Future secondary provider: Koyeb or equivalent
- Future secondary bot token: optional operational backup bot, separate from primary commerce bot

## Rules from this point
- Do not add more store UX patches until Railway visibly serves the inline store version
- Keep one clear source of truth for database
- Use Redis/runtime failover carefully; avoid split-brain patterns
- Document every operational step in state files before expanding architecture