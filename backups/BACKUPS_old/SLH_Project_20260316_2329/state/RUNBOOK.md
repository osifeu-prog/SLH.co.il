# SLH_PROJECT_V2 :: RUNBOOK

## Primary production path
- Telegram webhook target should point to Railway production webhook
- Railway is the current primary runtime
- Validate:
  - getWebhookInfo
  - /health
  - /healthz
  - Telegram /start
  - Telegram /buy
  - Telegram /my_orders

## Deploy validation
After every deploy:
1. Confirm git commit is pushed
2. Confirm Railway deployment finished for all relevant services
3. Confirm /health and /healthz respond
4. Confirm Telegram webhook target is correct
5. Confirm visible bot behavior matches the expected patch
6. Do not assume success from health alone

## Worker mismatch suspicion pattern
Symptoms:
- /health is OK
- Telegram webhook target is correct
- Bot responds
- But user-visible behavior is still old

Interpretation:
- Likely worker/webhook mismatch or partial rollout during incident/deploy window
- Treat as deployment alignment issue first, not code failure

## Platform incident handling
If provider shows deploy slowness / paused deploys:
1. Stop pushing more commits
2. Preserve current state snapshot
3. Validate runtime availability separately from deployment availability
4. Wait for provider stabilization
5. Re-run production validation after service alignment

## Emergency local fallback concept
Goal:
- Keep local PC ready as manual failover path

Required pieces:
- repo up to date
- venv ready
- local redis ready
- worker.py ready
- webhook_server.py ready
- public tunnel ready
- Telegram setWebhook switch script ready

## Failover principles
- Use one database source of truth
- Avoid two active uncontrolled runtimes consuming different queues
- Do not split a single production bot across uncontrolled environments
- If using a second Telegram bot token, isolate its role clearly

## Current freeze rule
Until Railway visibly serves the new inline /buy UI:
- No further store UX patches
- No additional commerce feature churn
- Focus on deployment alignment, validation, and operational hardening