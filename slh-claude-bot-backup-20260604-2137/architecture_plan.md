# Architecture Plan  SLH Spark AI v3.4 (proposed)

## Directory Structure
# Architecture Plan – SLH Spark AI v3.4 (proposed)

## Directory Structure
slh-bot/
├── core/
│ ├── db.py # asyncpg connection pool, table creation
│ ├── config.py # load environment variables
│ ├── router.py # command map + callback map
│ └── logger.py # logging setup
├── services/
│ ├── groq_service.py # Groq AI chat (fallback)
│ └── ton_service.py # TON payment verification (webhook)
├── features/
│ ├── users/ # register, identity, profile, myid, myidentity
│ ├── tasks/ # checkin, points, leaderboard, tap, tasks, done
│ ├── wallet/ # wallet, deposit, transfer, upgrade, paid
│ ├── referral/ # referral, invite
│ ├── crm/ # addcustomer, customers, addnote, notes
│ ├── store/ # store, add_product, products, buy
│ ├── oracle_peace/ # oracle, peace (with sub‑callbacks)
│ └── admin/ # admin, users, broadcast, morning, doctor, statusapi, setreminder, backup, crm, stats, events, segments
├── shared/
│ ├── keyboards.py # main_menu, admin_menu
│ └── utils.py # fix_hebrew, get_multiplier, update_energy
└── main.py # init_db, register all features, start polling

text

## Phased Migration (do not change production)

1. **Phase 0:** Create the new directory structure (empty).
2. **Phase 1:** Implement core/ and shared/ – no features yet.
3. **Phase 2:** Migrate eatures/users/ – test after each.
4. **Phase 3:** Migrate eatures/tasks/.
5. **Phase 4:** Migrate eatures/wallet/, eatures/referral/.
6. **Phase 5:** Migrate eatures/crm/, eatures/store/, eatures/oracle_peace/.
7. **Phase 6:** Migrate eatures/admin/.
8. **Phase 7:** Replace ot.py with main.py (entry point).

## Dependencies Map
- core/db.py – no internal dependencies.
- eatures/* – depend on core/db.py and shared/* only.
- services/* – called by features via core/config.py.
- No circular imports allowed.

## Validation after each phase
- Local test: python main.py (with test database).
- Production: ailway up --detach only after full migration.
