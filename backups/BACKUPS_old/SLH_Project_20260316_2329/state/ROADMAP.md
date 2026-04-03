# SLH_PROJECT_V2 :: ROADMAP

## Phase 0 :: Immediate stabilization
- [x] Commerce engine working end-to-end
- [x] Audit events working
- [x] Railway deployment path exists
- [x] i18n base added
- [x] Inline store UI patch committed
- [ ] Confirm Railway serves the inline store UI in production
- [ ] Confirm worker and webhook are aligned on the intended release
- [ ] Freeze code churn until production behavior matches expected patch

## Phase 1 :: Production hardening
- [ ] Create failover-status PowerShell tooling
- [ ] Create local-PC emergency runtime start/stop scripts
- [ ] Create Telegram webhook switch scripts:
  - [ ] set-webhook-railway.ps1
  - [ ] set-webhook-local.ps1
- [ ] Create operational health verification checklist
- [ ] Add incident handling steps for platform deploy slowness
- [ ] Add explicit production validation checklist after each deploy

## Phase 2 :: Local emergency fallback
- [ ] Prepare local PC as emergency fallback runtime
- [ ] Keep venv, repo, worker, webhook, redis, and tunnel path ready
- [ ] Validate local runtime against the shared source of truth
- [ ] Test manual failover from Railway to local webhook target
- [ ] Test failback from local runtime to Railway

## Phase 3 :: Secondary provider standby
- [ ] Add secondary provider standby environment
- [ ] Do not reuse dev-local DATABASE_URL / REDIS_URL on secondary cloud runtime
- [ ] Use externally reachable production-grade DB/Redis if multi-provider active standby is required
- [ ] Validate secondary standby boot, health, and controlled activation flow

## Phase 4 :: Secondary bot strategy
- [ ] Decide whether to add a second Telegram bot token
- [ ] Candidate uses:
  - [ ] operations / status bot
  - [ ] maintenance fallback bot
  - [ ] admin-only backup bot
- [ ] Keep primary commerce bot isolated and stable

## Phase 5 :: Commerce UX phase 2
- [ ] Product images
- [ ] Featured section improvements
- [ ] Better confirmation messages
- [ ] Product detail polish
- [ ] Pagination refinement
- [ ] Multi-language rendering improvements

## Phase 6 :: Commerce automation
- [ ] Auto-fulfillment for eligible digital products
- [ ] Admin revenue commands
- [ ] Revenue dashboard summary
- [ ] Affiliate / referral monetization flow
- [ ] Optional WebApp storefront later