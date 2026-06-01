# NFTY Bot (@NFTY_madness_bot) - Full Scan Report
> Bot ID: 7998856873 | Location: D:\SLH_BOTS\
> Framework: aiogram 3.6 | DB: SQLite (tamagotchi.db)

## Current Status: NEEDS UPGRADE

### Critical Bug: database is locked
**Root Cause**: Synchronous sqlite3 calls in async aiogram environment.
**Fix**: Migrate all DB calls to aiosqlite (async wrapper).
**Impact**: Bot crashes under concurrent load.

## Database Schema (9 tables)

1. **tamagotchi** - Main pet data (user_id, pet_name, pet_type, hunger, happiness, energy, health, age, stage, xp, level, coins, death_date)
2. **guess_leaderboard** - Number guessing stats
3. **user_settings** - Alert preferences, reminder intervals
4. **shop_items** - 6 items (apple, chicken, potion, battery, teddy, star)
5. **user_inventory** - Owned items per user
6. **tricks** - 5 learnable tricks (paw, tail spin, roar, roll, wink)
7. **learned_tricks** - User trick progress
8. **learning_points** - LP currency per user
9. **cuteness_battles** - 1v1 battle history

## All Commands

| Command | Handler | Status | Description |
|---------|---------|--------|-------------|
| /start | cmd_start | Working | Create pet or resume |
| /feed | cmd_feed | Working | Feed pet (+hunger, +XP) |
| /play | cmd_play | Working | Play (+happiness, -energy) |
| /heal | cmd_heal | Working | Heal (+health, cures sickness) |
| /sleep | cmd_sleep | Working | Toggle sleep mode |
| /status | cmd_status | Working | Show pet stats |
| /guess | cmd_guess_number | Working | Number guessing game |
| /report | cmd_report | Working | Daily mood report |
| /teach | cmd_teach | Working | Learn tricks with LP |
| /cuteness | cmd_cuteness | Working | View cuteness rating |
| /cuteness_battle | cmd_cuteness_battle | Working | Challenge 1v1 |
| /shop | cmd_shop | Working | Browse store |
| /advice | cmd_advice | Working | AI advice (OpenAI) |
| /leaderboard | leaderboard_xp | Working | Top 10 XP |
| /longevity | leaderboard_longevity | Working | Top survivors |
| /guide | cmd_guide | Working | Help text |
| /group | cmd_group | Working | Community link |
| /settings | cmd_settings | Working | Alert settings |
| /talk | cmd_talk | STUB | Not implemented |
| /admin_stats | cmd_admin_stats | Working | Admin only |
| /reset_pet | cmd_reset_pet | Working | Admin only |

## Pet Types (6)
- Dog (balanced, 12yr lifespan)
- Cat (low hunger, high happiness, 15yr)
- Dino (high hunger, high XP, 20yr)
- Panda (low stats, 20yr)
- Lion (high hunger, high XP, 15yr)
- Elephant (very high hunger, 60yr)

## NOT Implemented (Planned)
- Daily Quests system
- Gift system (/gift <user> <item>)
- Achievements/Badges
- CBT breathing/mindfulness exercises
- Pet breeding
- SLH token integration
- Telegram wallet guide

## Upgrade Plan
1. Fix: Migrate sqlite3 -> aiosqlite (CRITICAL)
2. Fix: Move token to env var (SECURITY)
3. Add: Daily quests (5 daily challenges)
4. Add: CBT breathing exercises
5. Add: Achievement system
6. Add: Gift/sharing system
7. Add: SLH economy integration
8. Improve: Error handling throughout
