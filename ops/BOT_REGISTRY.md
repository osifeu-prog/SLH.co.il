# SLH Bot Registry — Single Source of Truth
# Updated: 2026-04-14 (Session 12)
# 23 active bots + 2 infrastructure services

## ACTIVE BOTS (23)

| # | Container | Telegram Handle | Bot ID | Token Env Var | Category | Status | Code Path |
|---|-----------|----------------|--------|---------------|----------|--------|-----------|
| 1 | slh-core-bot | @SLH_Core_bot | 8351227223 | CORE_BOT_TOKEN | Core | LIVE | core/ (external) |
| 2 | slh-guardian-bot | @SLH_Guardian_bot | 8521882513 | GUARDIAN_BOT_TOKEN | Security | LIVE | guardian/ (external) |
| 3 | slh-admin | @MY_SUPER_ADMIN_bot | 7644371589 | ADMIN_BOT_TOKEN | Admin | LIVE | admin-bot/ |
| 4 | slh-airdrop | @SLH_Airdrop_bot | 8530795944 | AIRDROP_BOT_TOKEN | Distribution | LIVE | airdrop/ |
| 5 | slh-campaign | @SLH_Campaign_bot | 8075933581 | CAMPAIGN_TOKEN | CRM | LIVE | campaign-bot/ |
| 6 | slh-game | @SLH_Game_bot | 8298897331 | GAME_BOT_TOKEN | Gaming | LIVE | match-bot/ |
| 7 | slh-wallet | @SLH_Wallet_bot | 8729004785 | WALLET_BOT_TOKEN | Wallet | LIVE (issues) | wallet/ |
| 8 | slh-factory | @Osifs_Factory_bot | 8216202784 | FACTORY_BOT_TOKEN | Factory | LIVE (Redis err) | factory/ |
| 9 | slh-fun | @SLH_Fun_bot | 8554485332 | FUN_BOT_TOKEN | Entertainment | LIVE (InputFile err) | fun/ |
| 10 | slh-osif-shop | @OsifShop_bot | 8106987443 | OSIF_SHOP_TOKEN | E-Commerce | LIVE | osif-shop/ |
| 11 | slh-nfty | @NFTY_madness_bot | 7998856873 | NFTY_MADNESS_TOKEN | Marketplace | LIVE (encoding fixed) | nfty-bot/ |
| 12 | slh-nifti | @NIFTI_Publisher_Bot | 8478252455 | NIFTI_PUBLISHER_TOKEN | Wellness | LIVE | nfty-bot/ (shared) |
| 13 | slh-ton | @SLH_TON_bot | 8172123240 | SLH_TON_TOKEN | TON | LIVE | template |
| 14 | slh-ton-mnh | @TON_MNH_bot | 8508943909 | TON_MNH_TOKEN | TON | LIVE (tasklist err) | tonmnh-bot/ |
| 15 | slh-ledger | @SLH_Ledger_bot | 8494620699 | SLH_LEDGER_TOKEN | IoT | LIVE (no ESP32) | template |
| 16 | slh-chance | @Chance_Pais_bot | 8415305046 | CHANCE_PAIS_TOKEN | Recovery | LIVE | template |
| 17 | slh-botshop | @SLH_BotShop_bot | 8288632241 | BOTSHOP_BOT_TOKEN | Shop | LIVE | botshop/ |
| 18 | slh-ts-set | @ts_set_bot | 8692123720 | TS_SET_TOKEN | Trading | LIVE | template |
| 19 | slh-crazy-panel | @crazy_panel_bot | 8238076648 | CRAZY_PANEL_TOKEN | Admin | LIVE | template |
| 20 | slh-nft-shop | @Buy_My_Shop_bot | 8394483424 | MY_NFT_SHOP_TOKEN | NFT | LIVE | template |
| 21 | slh-beynonibank | @beynonibank_bot | 8384883433 | BEYNONIBANK_TOKEN | Banking | LIVE | template |
| 22 | slh-test-bot | @SLH_test_bot | 8522542493 | TEST_BOT_TOKEN | Testing | LIVE | template |
| 23 | slh-airdrop | @SLH_Airdrop_bot | 8530795944 | AIRDROP_BOT_TOKEN | Airdrop | LIVE | airdrop/ |

## INFRASTRUCTURE (2)

| Container | Type | Status |
|-----------|------|--------|
| slh-postgres | PostgreSQL 15 | Healthy |
| slh-redis | Redis 7 | Healthy |

## REMOVED / LEGACY (3)

| Container | Reason | Date Removed |
|-----------|--------|-------------|
| slh-expertnet | Token collision with selha, disabled as LEGACY | 2026-04-14 |
| slh-selha | Dummy placeholder, shared token | 2026-04-14 |
| slh-userinfo | Dummy placeholder, shared token | 2026-04-14 |

## KNOWN ISSUES

| Bot | Issue | Priority |
|-----|-------|----------|
| slh-wallet | Shows localhost URLs | P1 |
| slh-factory | Redis connection error on /start | P2 |
| slh-fun | InputFile abstract class error | P2 |
| slh-ton-mnh | Uses `tasklist` (Windows) in Linux Docker | P2 |
| slh-nifti | Shares code with nfty-bot | P2 |
| slh-ledger | ESP32 hardware not connected | P3 |
| slh-chance | Template only, pivoting to gambling recovery | P3 |
| slh-nft-shop | Template only, needs NFT functionality | P3 |
| slh-botshop | Lost NFT/smart contract features | P3 |

## EXTERNAL BOTS (not in Docker)

| Bot | Platform | Status |
|-----|----------|--------|
| @SLH_AIR_bot | Railway (API-integrated) | SOURCE OF TRUTH |
| @SLH_Academia_bot | Legacy (SLH_PROJECT_V2) | Needs migration |

## TOKEN SECURITY NOTES

- All tokens were exposed in chat history on 2026-04-09 and 2026-04-13
- SECURITY_TOKEN_ROTATION.md documents the rotation plan
- Rotation requires: @BotFather → /revoke → update .env → restart containers
- **DO NOT paste tokens in chat or commit to git**
