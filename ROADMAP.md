# SLH SPARK SYSTEM - Roadmap

> Last verified: 2026-04-18 (AI-verified against live API, website, docker, git)
> Full status report: [TASKS_STATUS_2026-04-18.md](TASKS_STATUS_2026-04-18.md)

## Phase 1: Foundation (DONE)
- [x] Clean C: drive (0GB -> 108GB free)
- [x] Move Docker to D:\DockerData
- [x] Unified docker-compose.yml
- [x] All 6 bots running in polling mode
- [x] Shared Postgres + Redis infrastructure
- [x] PowerShell profile with SLH branding
- [x] Windows lock screen: SLH SPARK SYSTEM

## Phase 2: Stabilize & Connect
- [x] Fix Academia bot token (BotFather) — AIRDROP_BOT_TOKEN unique, EXPERTNET/SELHA legacy disabled 2026-04-14
- [ ] **BLOCKED (Osif):** Fix GitHub remote for Guardian — code moved from `D:\telegram-guardian-DOCKER-COMPOSE-ENTERPRISE`, guardian/ only has LOCATION.txt. Decide: new repo or merge to slh-api
- [x] Push all repos to GitHub — slh-api + website both live, guardian part of slh-api
- [x] Add health monitoring dashboard — `website/ops-dashboard.html` + `website/system-health.html` live
- [x] Connect bots to shared user database (SSO across bots) — all 24 Docker bots share PostgreSQL (22 DATABASE_URL refs in compose)
- [x] Unified admin panel — `website/admin.html` with 19 sidebar pages + `/api/admin/*` endpoints

## Phase 3: Production Deployment
- [x] ~~Cloudflare Tunnel~~ — N/A: Railway handles ingress
- [x] ~~Nginx reverse proxy~~ — N/A: Railway provides
- [x] SSL certificates — Railway auto-provides HTTPS (slh-api-production.up.railway.app, slh-nft.com)
- [x] Auto-restart on crash — 24 `restart:` policies in docker-compose.yml
- [ ] Log aggregation (centralized logging) — no logstash/fluentd/loki. Use `docker logs` for now
- [ ] Backup strategy (pg_dump cron job) — no backup script found in `scripts/`

## Phase 4: Cross-Bot Economy
- [x] Shared SLH token across all bots — live on BSC `0xACb0A09414CEA1C879c67bB7A877E4e19480f022`
- [ ] Wallet bot as central treasury — `/api/treasury/*` endpoints live but bot-level integration incomplete
- [x] Cross-bot referral system — `/api/referral/{link,stats,tree,register,leaderboard}` live
- [x] Unified leaderboard — `/api/leaderboard` + `/api/rep/leaderboard` + `/api/sudoku/leaderboard` live
- [x] P2P trading between users — `/api/p2p/*` + `/api/p2p/v2/*` (create/fill/cancel order) live
- [x] BSC/TON bridge integration — PancakeSwap stats endpoint + `/api/payment/ton/auto-verify` + `/api/payment/bsc/auto-verify` live

## Phase 5: Scale
- [ ] React Native app (D:\SLH_APP) connected to all bots — app exists, bot connection not verified
- [x] Website as landing page — 83 HTML pages (up from 43!) on slh-nft.com
- [x] Multi-language support (Hebrew, English, Arabic) — hreflang HE/EN/RU/AR/FR + `website/js/translations.js` (37% page coverage — ongoing)
- [ ] Bot Factory: let users create their own bots — not implemented
- [ ] ExpertNet: AI expert network integration — `/api/experts/*` endpoints exist, Zvika franchise bot not built
- [x] Campaign bot for marketing automation — `slh-campaign` container running + `/api/campaign/*` live

## Bot Inventory (25 active)

### Docker containers running (24 services)
| Bot | Status |
|-----|--------|
| @Grdian_bot | Up 3h (slh-guardian-bot) |
| @Buy_My_Shop_bot | Up 3h (slh-botshop) |
| @SLH_Wallet_bot | Up 3h (slh-wallet) |
| @Osifs_Factory_bot | Up 3h (slh-factory) |
| @SLH_community_bot | Up 3h (slh-core-bot) |
| @NIFTI_Publisher_Bot | Up 3h (slh-nifti, slh-nfty) |
| @Campaign_SLH_bot | Up 3h (slh-campaign) |
| @G4meb0t_bot_bot | Up 3h (slh-game) |
| @SLH_Ledger_bot | Up 3h (slh-ledger) |
| @ts_set_bot | Up 3h (slh-ts-set) |
| @SLH_ton_bot | Up 3h (slh-ton) |
| @OsifShop_bot | Up 3h (slh-osif-shop) |
| @My_crazy_panel_bot | Up 3h (slh-crazy-panel) |
| @Chance_Pais_bot | Up 3h (slh-chance) |
| @TON_MNH_bot | Up 3h (slh-ton-mnh) |
| @MY_SUPER_ADMIN_bot | Up 3h (slh-admin) |
| @SLH_Fun_bot | Up 3h (slh-fun) |
| @AIRDROP_bot | Up 3h (slh-airdrop) |
| @NFT_shop_bot | Up 3h (slh-nft-shop) |
| @BeynoniBank_bot | Up 3h (slh-beynonibank) |
| @test_bot | Up 3h (slh-test-bot) |
| postgres | Up 3h (healthy) |
| redis | Up 3h (healthy) |

### Pending (on BotFather, awaiting deployment)
- @WEWORK_teamviwer_bot — token stored in .env (2026-04-18)
