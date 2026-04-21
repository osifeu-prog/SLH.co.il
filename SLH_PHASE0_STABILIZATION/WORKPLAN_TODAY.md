# SLH PHASE 0 - TODAY WORKPLAN

## Confirmed findings
1. Railway API health works.
2. Admin endpoints return "Admin authentication required".
3. Local container slh-ledger is crashing.
4. Crash root cause is likely TOKEN/BOT_TOKEN mismatch:
   - container has BOT_TOKEN
   - app log shows Bot(token=TOKEN) with TOKEN=None

## Goals for today
1. Stabilize slh-ledger locally.
2. Verify exact admin auth contract against Railway.
3. Prepare clean env/template files.
4. Save a handoff so next chat continues from the exact same point.

## Execution order
1. Run inspect-ledger.ps1
2. Run test-admin-api.ps1
3. Fill .env.template with real values
4. If needed, patch compose/env so TOKEN and BOT_TOKEN are aligned
5. Restart ledger and verify healthy logs
