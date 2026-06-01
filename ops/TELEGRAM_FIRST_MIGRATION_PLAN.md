# Telegram-First Migration Plan — 2026-04-21

## Strategic decision

SLH adopts a **Telegram-first, API-centered, Mini-App-enabled** architecture.

- **Telegram** = unified control surface (bots + Mini Apps)
- **Core API** (FastAPI on Railway) = single source of truth for all business state
- **Workers/Redis** = async jobs (broadcasts, reconciliation, backtests)
- **ESP32 devices** = same citizen class as bots — they talk to the Core API, not to bots directly
- **Website** = public marketing / SEO / legal landing surface; no operational state

Slogan: **Multiple bots, one core.**

---

## The three layers

```
    Telegram User / ESP Device
                │
       ┌────────┴────────┐
       │                 │
   Bot handler     Mini App (HTML)
       │                 │
       └────────┬────────┘
                │
        api/telegram_gateway.py
           (auth + audit)
                │
           Core API (FastAPI)
                │
       ┌────────┼────────┐
       │        │        │
   Postgres  Redis   External
    (state) (queue)  (BSC, TG)
```

Every user-facing flow enters through the Gateway (`api/telegram_gateway.py`).
The Gateway:
1. Validates Telegram identity (initData HMAC-SHA256 for Mini Apps, bot-token trust for bot updates).
2. Resolves `telegram_id → slh_user_id` + role.
3. Audits to `event_log`.
4. Hands off to the existing `/api/...` business routes.

Bot handlers stay **thin**. No SQL, no ledger writes, no business rules inside bots.

---

## ESP32 role in the architecture

ESP devices are equal peers to bots and Mini Apps. They consume the same API.

| Direction | Flow |
|-----------|------|
| Osif → ESP | Mini App `/miniapp/device.html` → `POST /api/device/command/{id}` → ESP polls `GET /api/device/command/{id}` at heartbeat → displays/acts |
| ESP → Osif | ESP button / event → `POST /api/events` → worker → push via bot → Telegram message |
| ESP ↔ Ledger | ESP heartbeat → API reads cached balance → returns to device for display |

Nothing new needs to be built in the firmware for this — `fetchBalances()`, `pollClaim()`, `pollCommand()` in `main.cpp` already talk to the right endpoints.

---

## Page-by-page migration decision (100 HTML files)

Legend:
- **KEEP** — public web page, stays on GitHub Pages (SEO, legal, marketing)
- **MINIAPP** — move to `/miniapp/` (user-specific, state-bound)
- **ADMIN-MINIAPP** — move to `/miniapp/admin/` (admin console inside Telegram)
- **DELETE** — stale, duplicate, or obsolete after migration
- **MERGE → X** — fold into page X
- **CHAT** — replace with bot commands; no page needed

### Marketing / public (KEEP as web pages)

| File | Reason |
|------|--------|
| `index.html` | Primary landing, SEO entry |
| `about.html` | Public company/project info |
| `whitepaper.html` | SEO, investor-facing |
| `roadmap.html` | Public milestones |
| `blog.html`, `daily-blog.html`, `blog-legacy-code.html` | Content marketing |
| `terms.html`, `privacy.html` | Legal requirement |
| `ecosystem-guide.html`, `getting-started.html`, `join-guide.html`, `wallet-guide.html`, `guides.html` | Onboarding docs |
| `tour.html`, `learning-path.html` | Product explainers |
| `encryption.html`, `risk.html` | Transparency for investors |
| `healing-vision.html`, `jubilee.html`, `for-therapists.html` | Vision/positioning |
| `dex-launch.html`, `launch-event.html`, `partner-launch-invite.html` | Event landings |
| `join.html`, `invite.html`, `referral-card.html`, `promo-shekel.html`, `member.html` | Conversion / referral landing |
| `buy.html`, `sell.html`, `p2p.html`, `trade.html` | SEO for "buy SLH" intents; actual flow → MINIAPP |

### Move to Mini App (user-specific, state-bound)

| File | Lands at | Priority |
|------|---------|----------|
| `dashboard.html` | `/miniapp/dashboard.html` | **P0 — shipped** |
| `wallet.html` | `/miniapp/wallet.html` | **P0 — shipped** |
| `device-pair.html` | `/miniapp/device.html` | **P0 — shipped** |
| `profile.html` | `/miniapp/profile.html` | P1 |
| `settings.html` | `/miniapp/settings.html` | P1 |
| `shop.html` | `/miniapp/marketplace.html` | P1 |
| `community.html` | `/miniapp/community.html` | P1 |
| `staking.html` | `/miniapp/staking.html` | P1 |
| `earn.html` (personal side only) | `/miniapp/earn.html` | P1 |
| `referral.html` | `/miniapp/referral.html` | P1 |
| `receipts.html`, `expenses.html` | `/miniapp/expenses.html` | P2 |
| `live.html`, `live-stats.html` | `/miniapp/live.html` | P2 |
| `challenge.html`, `sudoku.html` | `/miniapp/games.html` | P2 |
| `card-payment.html`, `pay.html` | `/miniapp/pay.html` | P2 |
| `leads.html`, `support-deal.html` | `/miniapp/deals.html` | P2 |
| `kosher-wallet.html` | `/miniapp/kosher.html` | P2 |
| `dating.html` | `/miniapp/dating.html` (for @G4meb0t_bot) | P2 |
| `investment-tracker.html`, `upgrade-tracker.html`, `agent-tracker.html` | `/miniapp/tracking.html` | P2 |

### Admin Mini App

| File | Lands at | Priority |
|------|---------|----------|
| `admin.html` | `/miniapp/admin/index.html` | **P0** |
| `admin-bugs.html` | `/miniapp/admin/bugs.html` | P1 |
| `admin-experts.html` | `/miniapp/admin/experts.html` | P1 |
| `admin-tokens.html` | `/miniapp/admin/tokens.html` | P1 |
| `ops-dashboard.html` | `/miniapp/admin/ops.html` | **P0** |
| `mission-control.html` | MERGE → `admin/ops.html` | P1 |
| `control-center.html` | MERGE → `admin/ops.html` | P1 |
| `broadcast-composer.html` | `/miniapp/admin/broadcast.html` | **P0** |
| `partner-dashboard.html` | `/miniapp/admin/partners.html` | P1 |
| `broker-dashboard.html` | `/miniapp/admin/brokers.html` | P2 |
| `risk-dashboard.html` | `/miniapp/admin/risk.html` | P1 |
| `treasury-health.html` | `/miniapp/admin/treasury.html` | P1 |
| `system-health.html`, `system-audit.html`, `status.html` | MERGE → `admin/ops.html` | P1 |
| `guardian-diag.html` | `/miniapp/admin/guardian.html` | P2 |
| `chain-status.html` | `/miniapp/admin/chain.html` | P2 |
| `performance.html` | `/miniapp/admin/performance.html` | P2 |
| `analytics.html` | `/miniapp/admin/analytics.html` | P2 |
| `overnight-report.html` | `/miniapp/admin/overnight.html` | P2 |
| `morning-checklist.html`, `morning-handoff.html` | MERGE → `admin/overnight.html` | P2 |
| `network.html`, `blockchain.html` | MERGE → `admin/chain.html` | P2 |
| `alpha-progress.html` | `/miniapp/admin/alpha.html` | P2 |
| `bot-registry.html`, `bots.html` | `/miniapp/admin/bots.html` | P1 |
| `mass-gift.html` | `/miniapp/admin/mass-gift.html` | P2 |
| `ops-report-20260411.html` | DELETE (stale snapshot) | — |

### Replace with bot commands (CHAT)

These become slash commands in the right bot:

| Was | Replacement |
|-----|-------------|
| `bug-report.html` | `/bug <description>` in main bot → opens ticket |
| `liquidity.html` | `/liquidity` in admin-bot |
| `project-map.html`, `project-map-advanced.html` | `/map` in admin-bot |
| `rotate.html` | `/rotate` in admin-bot (admin only) |
| `experts.html` (self-serve apply) | `/expert apply` in academia-bot |
| `onboarding.html` | `/start` flow in main bot |
| `agent-brief.html`, `agent-hub.html` | `/agent help` |

### Delete (stale, duplicate, or test)

| File | Why |
|------|-----|
| `test-bots.html` | Test artifact, should never be in prod |
| `ops-report-20260411.html` | Stale snapshot from 10 days ago |
| `gallery.html` | Unused |
| `rotate.html` | Replaced by `/rotate` bot command |

---

## Authentication model after migration

| Entry point | Identity proof | Gateway output |
|------|-------|----------------|
| Public web page (KEEP) | None (public) | No auth — read-only public endpoints only |
| Mini App (`/miniapp/*.html`) | `tg.initData` → HMAC-SHA256 | `TelegramUser` with `slh_user_id`, `is_admin` |
| Bot update (aiogram handler) | `from_user.id` + bot-token trust | `TelegramUser` with `slh_user_id`, `is_admin` |
| ESP device | `X-Device-Token` (existing) | Device identity — separate from user, linked to `device-registry` |
| Legacy admin login (CLI / curl) | `X-Admin-Key` header | Grandfathered until all admin UIs migrate |

All mutation endpoints require `verify_miniapp_request` or `verify_bot_request` dependency.
Admin-only endpoints additionally call `require_admin(user)`.

---

## Rollout phases

### Phase 1 — Foundation (this session)
- [x] `api/telegram_gateway.py` created
- [x] `/miniapp/dashboard.html`, `wallet.html`, `device.html` scaffolded
- [x] Migration plan published (this file)
- [ ] `slh-claude-bot/bot.py` extended with direct query handlers
- [ ] Gateway wired into `main.py` (next session — avoids merge conflicts with current deploy)

### Phase 2 — Critical admin (week of 2026-04-22)
- [ ] `/miniapp/admin/index.html` + `ops.html` + `broadcast.html`
- [ ] `event_log` table created & `gateway` audit rows flowing
- [ ] `/api/miniapp/*` routes with `Depends(verify_miniapp_request)`
- [ ] BotFather: set Mini App URL for @WEWORK_teamviwer_bot, @SLH_Claude_bot

### Phase 3 — User migration (week of 2026-04-29)
- [ ] Profile, settings, staking, marketplace Mini App pages
- [ ] Replace legacy `admin.html` localStorage flow with Telegram init-data auth
- [ ] Redirect deprecated pages to `/miniapp/*` with HTTP 301

### Phase 4 — Cleanup (May)
- [ ] Delete stale pages (test-bots, ops-report-20260411, gallery, rotate)
- [ ] Merge pages per decisions above
- [ ] Remove web-only fallbacks; everything authenticated goes through Gateway

### Phase 5 — ESP bidirectional (May-June)
- [ ] Mini App → ESP command UI (live now in draft form in `/miniapp/device.html`)
- [ ] ESP → Mini App push (events → webhook → bot notification)
- [ ] Physical button on ESP triggers `/api/events` → notifies Osif in bot DM

---

## Guardrails

These must not be broken during migration:

1. **No business logic in bot handlers.** Every mutation goes through a Core API endpoint. Bot handlers only: parse + render.
2. **No fake or fallback data.** If the API returns nothing, render `--` or an error card — never invent values.
3. **One Gateway entry point.** Every user-facing request validates identity through `api/telegram_gateway.py`, not ad-hoc in each route.
4. **Public vs. private pages are distinct.** Marketing pages (KEEP) never embed admin state. Mini App pages never render without an authenticated Telegram context.
5. **Admin Telegram IDs live in env (`ADMIN_TELEGRAM_IDS`), not hardcoded.** Osif is the default.
6. **Event log is mandatory.** Every gateway hit writes a row once `event_log` is online.

---

## Open questions before Phase 2

- Do we expose Mini Apps from the same GitHub Pages domain (`slh-nft.com/miniapp/`) or a dedicated `app.slh-nft.com` subdomain? Same domain is simpler; subdomain is cleaner CSP.
- BotFather Mini App URL: pick one bot as "home" (recommend `@WEWORK_teamviwer_bot` — already the revenue entry point).
- Gateway imported into `main.py` directly, or as a sub-router `app.include_router(gateway.router)`? Sub-router scales cleaner but adds one file.
- Mini Apps shipped alongside the current website repo (`osifeu-prog.github.io`) or as a separate repo? Same repo keeps one deploy pipeline.

---

## Reference

- Telegram Mini App init-data spec: https://core.telegram.org/bots/webapps#validating-data-received-via-the-mini-app
- Telegram theme params: https://core.telegram.org/bots/webapps#themeparams
- aiogram webhook mode (prod recommendation): https://docs.aiogram.dev/en/latest/dispatcher/webhook.html
- Our firmware peer: `D:\SLH_ECOSYSTEM\device-registry\esp32-cyd-work\firmware\slh-device-v3\src\main.cpp`
- Our Gateway: `D:\SLH_ECOSYSTEM\api\telegram_gateway.py`
- Our first 3 Mini Apps: `D:\SLH_ECOSYSTEM\website\miniapp\{dashboard,wallet,device}.html`
