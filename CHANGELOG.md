# SLH Spark · Changelog

All notable changes per release. Dates in UTC. Append-only.

---

## [0.9.0-alpha] — 2026-04-19 · "Transparent Alpha"

First tagged alpha release. Full E2E revenue loop demonstrated with receipt #SLH-20260417-000001 on 0.0005 BNB to Genesis wallet.

### Added — Track 7 · Creator Economy (NEW)
- `routes/creator_economy.py` — 6 endpoints at `/api/creator/*`:
  - `GET  /xp/{user_id}` — per-user XP (ROI ratio) with breakdown
  - `GET  /slh-index` — global median XP (SLH Index metric)
  - `GET  /shop/{user_id}` — personal shop with listings + sales + XP
  - `POST /purchase/complete` — records marketplace sale, credits seller, refreshes XP
  - `POST /roi/snapshot` — admin; refresh one user
  - `POST /roi/snapshot/all` — admin; cron batch refresh
- `sell.html` — upload form for NFTs/courses (image drop, story, price in 4 currencies, course-lesson toggle)
- `gallery.html` — public gallery with filter/sort/search + modal preview + buy CTA
- `shop.html` — personal creator dashboard with XP hero card, portfolio breakdown, listings grid, sales list
- `pay.html` — marketplace mode via `?product_id=X` URL params, calls `/api/creator/purchase/complete` on verify
- `js/shared.js` — `renderSLHIndexWidget()` floating pill on main public pages

### Added — Track 8 · Treasury (NEW)
- `routes/treasury.py` — 8 endpoints at `/api/treasury/*`
- Tables: `treasury_revenue`, `treasury_buybacks`, `treasury_burns`
- Policy: 2% burn rate on AIC marketplace sales, 10% buyback rate on fiat revenue
- Dead address: `0x000000000000000000000000000000000000dEaD`
- SLH burns logged manually by Osif after MetaMask TX

### Added — Infrastructure
- `slh-flip.js` — 3D flip + scramble text animations (~2kb, zero deps, `prefers-reduced-motion` aware)
- `manifest.json` + `sw.js` — PWA with install prompt, network-first HTML / cache-first assets
- `/upgrade-tracker.html` — live scan of 80 pages, meta-marker detection
- `/alpha-progress.html` — public dashboard with 7 tracks + T-minus countdown to 2026-05-03
- `/encryption.html` — SEO landing for "עברית מעוותת" + live fix demo
- `/live.html` — FB-ready landing with live stats + early-adopter bonuses
- `/receipts.html` — self-service receipt viewer with Premium/Count/Total summary
- `/prompts/` — 9 public agent prompts for external AI models

### Added — Archive
- `slh-genesis/` — append-only historical archive with README, central_agent.md, timeline.md, decisions.md (ADRs)
- `ops/ALPHA_READINESS.md` — roadmap to public beta with 7 tracks + week-by-week timeline
- `ops/AGENT_PROMPTS_READY.md` — 8 copy-paste prompts for ChatGPT/Claude/Gemini/DeepSeek
- `ops/DESIGN_SYSTEM.md` — canonical design reference

### Added — Love Tokens (Stub)
- `routes/love_tokens.py` — HUG / KISS / HANDSHAKE schema + 4 endpoints
- Disabled by default (`LOVE_TOKENS_ENABLED=0`) — pricing + UI pending

### Fixed
- **Critical:** `/api/payment/status/{user_id}` + `/api/payment/receipts/{user_id}` returned 500 on fresh DB (tables only created inside POST handlers). Fix: `_ensure_payment_tables()` called at `set_pool()` bootstrap + at start of every GET handler.
- `admin-tokens.html` prompt 404 — `raw.githubusercontent.com` (private repo) replaced with public `/prompts/`
- `admin-tokens.html` — per-field explanation boxes on Mint and Reserve forms to prevent unit confusion

### Changed
- `agent-brief.html` — 5→6 tokens (AIC added), 164→225+ endpoints, 68→79 pages
- `ops-dashboard.html` — 43→79 page KPI, added 6-token card, rewrote task list with today's deliverables
- `project-map.html` — 49→79 page count
- `sitemap.xml` — 4 → 50 URLs
- `blog/index.html` — 3 → 15 posts listed
- `nfty-bot/main.py` — approved listings now auto-broadcast to @slhniffty channel via `broadcast_new_listing()`
- `g4mebot/bot.py` — `/start <tg_id>` referral tracking, `/share` command, `/site` command, bi-directional web↔bot URL bridge
- 70/79 pages carry `<meta name="slh-version" content="v1.0-flip">` (87% upgrade coverage)

### Security
- `GAME_BOT_TOKEN` rotated (1 of 31 — the one for @G4meb0t_bot_bot)
- `ADMIN_API_KEYS` dual-key configured on Railway (old + new for 24h grace)
- `SILENT_MODE=1` enabled on Railway
- `slh-game` Docker container stopped (running old revoked token causing `Unauthorized` loops)

### Verified in production
- `/api/health` → `{"status":"ok","db":"connected","version":"1.0.0"}`
- `/api/treasury/summary` → returns JSON with empty revenue + policy visible
- `/api/payment/receipts/224223270` → 1 receipt: `SLH-20260417-000001` · 0.0005 BNB · 2026-04-17 19:45 UTC
- Receipt delivered to Osif via Telegram by @MY_SUPER_ADMIN_bot

### Blocked on Osif
- Deploy `@G4meb0t_bot_bot` to Railway as separate service (3-min setup in `g4mebot/README.md`)
- `N8N_PASSWORD` in Railway variables
- CYD screen `colorTest` verification → ESP firmware E.2+
- First AIC mint via `admin-tokens.html` (supply currently 1)
- 30 remaining bot tokens still need `@BotFather /revoke` rotation
- Facebook account warning (link shared `facebook.com/help/messenger-app/1093117295527969`) — pending screenshot for triage

### Metrics snapshot at release
- API version: 1.0.0
- Endpoints: 225+ production
- HTML pages: 79 (+ 15 blog posts)
- Bots: 25 (24 live, @G4meb0t local only)
- Tokens: 6 (SLH, MNH, ZVK, REP, ZUZ, AIC)
- First BSC receipt: #SLH-20260417-000001
- Users: ~18 (live count via `/api/stats`)
- Genesis raised: 0.082 BNB

---

## [Pre-alpha] — Through 2026-04-16

All work before this release was unlabeled. See `slh-genesis/LOGS/timeline.md` for day-by-day reconstruction.
