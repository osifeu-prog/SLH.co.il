# Post-Deploy Broadcast Plan — 12 April 2026

## When to send
After ALL of the following are complete:
1. earn.html fixes deployed
2. Wallet UX improvements deployed
3. PancakeSwap links fixed
4. system-health.html shows 30/30

## How to send

### Option A: Via broadcast-composer.html (easiest)
1. Open https://slh-nft.com/broadcast-composer.html
2. Click "🚀 Major Update (post-deploy)" template
3. Admin Key: slh2026admin
4. Target: "All users" (6 users)
5. Dry Run first → verify 6 recipients
6. Send for Real

⚠️ Requires SLH_AIR_TOKEN env var set on Railway!

### Option B: Via curl (if env var is set)
```bash
curl -X POST https://slh-api-production.up.railway.app/api/broadcast/send \
  -H "Content-Type: application/json" \
  -d '{
    "message": "🚀 עדכון גדול ב-SLH Spark!\n\n...(full template text)...",
    "target": "all",
    "admin_key": "slh2026admin",
    "dry_run": false
  }'
```

## Prerequisites
- [ ] SLH_AIR_TOKEN set on Railway
- [ ] All 3 agents completed
- [ ] All changes committed + pushed
- [ ] system-health.html shows 30/30
- [ ] earn.html no longer shows fake data
- [ ] wallet.html shows helpful connect instructions on mobile
