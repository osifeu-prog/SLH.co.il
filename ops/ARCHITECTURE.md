# SLH System Architecture

```
                    USERS (Telegram + Web)
                           |
              +------------+------------+
              |                         |
    [slh-nft.com]              [Telegram Bots x25]
    GitHub Pages                Docker Compose
    17 HTML pages               polling mode
              |                         |
              +----> [Railway API] <----+
                     FastAPI 0.115
                     30+ endpoints
                           |
              +------------+------------+
              |                         |
    [PostgreSQL 15]              [Redis 7]
    5 databases:                 3 databases:
    - slh_main                   - 0: core
    - slh_guardian               - 1: guardian
    - slh_botshop                - 2: airdrop
    - slh_wallet                 Streams: slh:*
    - slh_factory
```

## Database Schema (slh_main)

### Core Tables
| Table | Purpose | Key Columns |
|-------|---------|-------------|
| web_users | Website users | telegram_id, first_name, is_registered, registered_at |
| premium_users | Paid registrations | user_id, bot_name, payment_status, tx_hash |
| token_balances | Token holdings | user_id, token, available, locked |
| token_transfers | Transfer history | from_user, to_user, amount, token, tx_type |
| referrals | Referral tree | user_id, referrer_id, depth |
| referral_commissions | Commission log | user_id, from_user, amount, source_type |
| staking_positions | Active stakes | user_id, plan_key, amount, token, status |
| community_posts | Forum posts | user_id, content, category, likes |
| community_comments | Post comments | post_id, user_id, content |
| deposits | Payment records | user_id, amount, currency, tx_hash, status |
| analytics_events | Tracking events | user_id, event_type, page, timestamp |

## Bot Service Map (Docker)

### Tier 1: Core (DB-connected)
| Service | Container | Port | Database |
|---------|-----------|------|----------|
| core-bot | slh-core-bot | - | slh_main |
| guardian-bot | slh-guardian-bot | 8001 | slh_guardian |
| botshop | slh-botshop | - | slh_botshop |
| wallet-bot | slh-wallet | - | slh_wallet |
| factory-bot | slh-factory | - | slh_factory |
| fun-bot | slh-fun | 8002 | - |
| airdrop-bot | slh-airdrop | - | slh_main |

### Tier 2: Commerce Template Bots
slh-ton, slh-ledger, slh-nft-shop, slh-beynonibank,
slh-selha, slh-ts-set, slh-nifti, slh-nfty

### Tier 3: Specialized
slh-campaign, slh-game, slh-ton-mnh, slh-osif-shop (port 8080),
slh-admin, slh-expertnet, slh-userinfo, slh-test-bot

### Standalone (outside Docker)
| Bot | Location | DB | Framework |
|-----|----------|----|-----------|
| NFTY Tamagotchi | D:\SLH_BOTS\ | SQLite | aiogram |
| Guardian Enterprise | D:\telegram-guardian-...\ | PostgreSQL | python-telegram-bot |

## Deployment Pipeline

### Website (slh-nft.com)
```
git push origin main → GitHub Pages auto-deploy (1-2 min)
```

### API (Railway)
```
git push origin master → Railway auto-build Docker → deploy (~3 min)
```

### Docker Bots (Local)
```
docker compose up -d [service] → immediate
docker compose restart [service] → ~10s
```
