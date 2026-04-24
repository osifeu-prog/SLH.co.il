# SLH Ecosystem — Comprehensive Audit Report
**Date:** 2026-04-21 (Night Session)
**Scope:** ops/ docs + API code + website + live production + bot ecosystem + firmware
**Method:** 5 parallel specialized agents + live HTTP probes + code grep + doc cross-reference
**Output:** Every open item that stands between current state and "next-stage-ready"

---

## 0. Executive Summary (TL;DR)

The SLH Spark ecosystem is **much less operational than the handoff docs claim**. Behind a clean website facade and a healthy `/api/health` response, five categories of gaps block the next milestone:

1. **Website is visually broken** — `initShared()` (the function that injects nav, footer, i18n, FAB, PWA) is defined in `js/shared.js:1091` but **never called by any of the 121 HTML pages**. Recent "fixes" (commits c25e1fc, f5c7367) added DOM roots and FAB logic but did not wire the entry call. Users see blank nav.
2. **2 pages return 404 despite docs claiming LIVE** — `/marketplace.html` and `/team.html` (documented as shipped in Night 18.4 + 20.4) are missing from GitHub Pages deploy.
3. **Admin security is inconsistent** — 3 admin endpoints bypass `_require_admin()` (use forgeable `admin_id` in request body or hardcoded secret comparison). `JWT_SECRET` and `ADMIN_API_KEYS` both default to empty in code.
4. **Data feeds are dead** — `/api/events/public` returns `event_log_unavailable`, `/api/performance` returns `available:false` (no CSV on Railway), `network.html` + `blockchain.html` show all zeros (missing `BSCSCAN_API_KEY` env var).
5. **SECRETS EXPOSED IN CHAT TONIGHT** — 10+ production API keys pasted into this conversation: OPENAI, GEMINI, GROQ, BSCSCAN, two Telegram bot tokens, JWT_SECRET, ENCRYPTION_KEY, ADMIN_API_KEYS. Must rotate before any further deploy.

**Paid users to date:** Zero real external customers. User 8789977826 (the "₪196 × 4 payments" user) confirmed to be Osif himself. Only PancakeSwap liquidity is real economic activity.

**Recommended next-stage gate:** System truth + security hardening BEFORE any UI polish or new features.

---

## 1. TOP 10 SHIP-BLOCKERS (P0, do this week)

| # | Blocker | Action | Owner | ETA |
|---|---|---|---|---|
| 1 | **10 secrets leaked in chat** | Rotate: OpenAI, Gemini, Groq, BSCScan, EXPERTNET+SLH_AIR bot tokens, GUARDIAN bot token, JWT_SECRET, ADMIN_API_KEYS. Update Railway. Restart services. | Osif | 30 min |
| 2 | **`initShared()` never called on 121 pages** | Add before `</body>` in every page: `<script>if(typeof initShared==='function')initShared({activePage:'…'});</script>` | Code agent | 1 h (scripted) |
| 3 | **`marketplace.html` + `team.html` 404** | Find in `D:\SLH_ECOSYSTEM\website\` — restore or regenerate. Verify GitHub Pages deploy. | Code agent | 20 min |
| 4 | **Railway env var batch** | Set `BSCSCAN_API_KEY`, `ANTHROPIC_API_KEY` (for Claude bot), verify `JWT_SECRET`, `ADMIN_API_KEYS` not empty. | Osif | 5 min |
| 5 | **3 admin endpoints lack `_require_admin()`** | `main.py:957` (registration/approve), `main.py:2344` (beta/create-coupon), `main.py:4782` (marketplace/admin/approve) — swap to header-based auth. | Code agent | 45 min |
| 6 | **`_dev_code` SMS leak in prod** | `main.py:10498-10499` — remove `_dev_code` field from `/api/device/verify` response. | Code agent | 5 min |
| 7 | **`event_log_unavailable`** | `/api/events/public` returns error; chain-status.html shows empty. Check `event_log` table exists + migrations ran. | Code agent | 30 min |
| 8 | **Phase 0B docker rebuild** | `cd D:\SLH_ECOSYSTEM && docker compose up -d --build` — 9 bots have new pool code but old containers running. | Osif | 10 min |
| 9 | **ledger-bot restart loop** | Fix env name mismatch: `docker-compose.yml` maps `TOKEN=${BOT_TOKEN}` but service expects `BOT_TOKEN`. | Code agent | 5 min |
| 10 | **Academia VIP price mismatch** | `/academia.html` shows ₪99, `/api/academia/courses` returns ₪549. Pick one + reconcile. | Osif decision | 10 min |

---

## 2. P0 — Critical (Production Wrong or Unsafe)

### 2.1 Security

| Issue | Location | Fix |
|---|---|---|
| Hardcoded `ADMIN_API_KEY=slh_admin_2026` default | `main.py:961, 1070, 2347` | Remove defaults, fail-fast if unset at startup |
| Hardcoded `ADMIN_BROADCAST_KEY=slh-broadcast-2026-change-me` default | `main.py:250, 254` | Same — env-only, no fallback |
| `JWT_SECRET = os.getenv("JWT_SECRET", "")` | `main.py:58, 256` | `raise RuntimeError` if empty |
| `ADMIN_API_KEYS` can be empty set silently | `main.py:138-142` | Same fail-fast pattern |
| Registration approve uses `admin_secret` body field, not header | `main.py:957-963` | Use `_require_admin(authorization, x_admin_key)` |
| Beta coupon creation unprotected | `main.py:2344-2355` | Same |
| Marketplace admin approve uses `req.admin_id != ADMIN_USER_ID` (forgeable) | `main.py:4782-4801` | Same |
| `_dev_code` leaks SMS code in prod response | `main.py:10498-10499` | Delete field from response |
| CORS allows all methods (`GET, POST, PUT, DELETE, OPTIONS`) | `main.py:84-91` | Method-specific CORS per route |
| Rate limit is per-IP only, no per-user | `main.py:100-112` | Add user-scoped rate limiting |
| 31 bot tokens appeared in chat logs historically | root `.env` | Rotate all via @BotFather `/revoke` |

### 2.2 Website (Public-Facing Wrongness)

| Issue | Location | Fix |
|---|---|---|
| **`initShared()` never called** | 0 of 121 HTML pages invoke it | Inject `<script>initShared({...})</script>` before `</body>` on every page |
| `/marketplace.html` → 404 | GitHub Pages | Restore file, redeploy |
| `/team.html` → 404 | GitHub Pages | Restore file, redeploy |
| Academia module links point to `.html` files that are actually `.md` | `academia.html:230`, `course-1-dynamic-yield.html`, `risk.html` | Either create `.html` wrappers for `.md` content, or convert links to `.md` |
| Dead `/marketplace` link in academia | `academia.html:230` "🛒 שוק" button | Remove or redirect once marketplace.html is back |
| Phantom "Thousands of users" claim | `index.html` `data-i18n="landing_cta_sub"` + `translations.js` | Change copy to "community of early contributors" or similar — only 9 registered users actually |
| 21 HTML files still say "65%" / "APY" | `whitepaper.html`, `staking.html`, `roadmap.html`, `risk.html`, `academy/course-1-dynamic-yield/calculator.html` and others | Replace with `data-i18n="yield_dynamic"` + add "Dynamic Yield (4-12%)" entries |
| `rotate.html` + `test-bots.html` + `ops-report-20260411.html` deployed publicly | Website root | Move to `/admin/internal/` or delete |

### 2.3 API (Broken/Wrong Data)

| Issue | Location | Fix |
|---|---|---|
| `/api/events/public` → `{"error":"event_log_unavailable"}` | route handler | Verify event_log table, connection, insert path |
| `/api/performance` → `{"available":false}` | `main.py:performance` | Run `daily_backtest.py` on Railway (scheduled or deploy-hook) to produce CSV |
| `/api/performance/digest` → same cause | same | Same |
| Deposits schema drift: `token` vs `currency`, `confirmed_at` vs `created_at` | `routes/payments_auto.py:494-502` uses column aliases to mask | Migration: rename columns, drop aliases |
| Recursive referral count hardcoded to direct count | `main.py:4382` "total_network": direct | Walk referrals tree (recursive CTE in SQL) |
| SLH price hardcoded `SLH_PRICE_USD = 121.6` | `routes/creator_economy.py:46` | Wire to oracle or CoinGecko with 5 min cache |
| BSC wallet balance stubbed | `main.py:1494` TODO | Implement via `BSCSCAN_API_KEY` |

---

## 3. P1 — High (Half-Shipped Features)

| Issue | Location | Fix |
|---|---|---|
| Referral 2-tier pivot in code, **no tests, no trace logs, no E2E verification** | `main.py:3029-3070` | Add integration test + log every commission dispatch |
| Marketplace `/api/marketplace/buy` tangles token transfer + fiat + royalty in one endpoint | `main.py:4821-4960` | Split into async idempotent steps with event_log entries |
| Payment endpoint returns raw HTTP errors without i18n Hebrew messages | `routes/payments_auto.py:200-400` | Wrap with error codes + Hebrew strings |
| No event log entries for payment lifecycle | `routes/payments_auto.py:*` | Insert `event_log` rows at each state change (created/verified/rejected/appealed) |
| Legacy XOR encryption backward-compat still live | `main.py:1809, 1826, 1843` | Migrate all secrets to AES-GCM, drop XOR path |
| Stale cache returned silently on DB error with no `cache_age` marker | `main.py:2934` | Add `X-Cache-Age` header, log hits |
| No tests directory at all (0 tests, 113 endpoints) | `api/tests/` missing | Start with pytest + asyncpg fixtures; aim 70% on payment + admin paths |
| `/api/admin/link-phone-tg` had tuple-unpack bug (fixed commit e1b560b per docs, but not re-verified live) | `main.py:~10770` | Re-run the curl per OPEN_TASKS B6 to confirm |
| Guardian bot local code not found | `D:\SLH_ECOSYSTEM\guardian\LOCATION.txt` points to `D:\telegram-guardian-DOCKER-COMPOSE-ENTERPRISE` | Verify path exists OR fix remote repo (memory: `github.com/osifeu-prog/slh-guardian` → 404) |
| `@SLH_Claude_bot` waiting for `ANTHROPIC_API_KEY` | `D:\SLH_ECOSYSTEM\slh-claude-bot\.env` | Generate + paste, then `docker compose up -d slh-claude-bot` |
| ExpertNet bot imports `slh_payments.ledger` + `blockchain` but modules not in repo | `expertnet-bot/main.py` | Either commit shared libs OR document dependency path + adjust imports |
| G4mebot not in `docker-compose.yml` | — | Add service block if dating feature is priority |
| Airdrop bot has 8 variant `bot.py` files | `D:\SLH_ECOSYSTEM\airdrop\bot\*` | Pick canonical, delete rest, document |
| Academia payment method iCount/ZVK listed in docs but not wired | `slh-academia-bot/bot.py` | Implement OR remove from listed options |

---

## 4. P2 — Cleanup (Tech Debt)

| Issue | Location | Fix |
|---|---|---|
| 94 stray `console.log/warn/error` calls in HTML files | `admin.html`, `control-center.html`, `dashboard.html`, bots pages | Wrap with `if(localStorage.slh_dev==='1')` or remove |
| Unused `NAV_ITEMS` array (33 entries) | `shared.js:28-63` | Dead code until `initShared()` is wired |
| Two deposit schemas co-exist (tx_hash legacy + financial) | `main.py:10096` | Consolidate one, migrate |
| Device-registry module purged with no user-migration script | noted in `SESSION_HANDOFF_20260421_LATE.md:25` | Script export of existing device rows into `event_log` |
| `event_log` (Phase 0) has no retention policy — grows unbounded | Phase 0 core | Add 30-day TTL cleanup job |
| Missing NOT NULL on `token_balances.balance` | DB | Add constraint + default 0 |
| `payment_receipts.pdf_url` always NULL (column unused) | DB | Drop column or implement PDF issuance |
| No FK from `external_payments` to `web_users` | DB | Add constraint |
| No composite index on `premium_users(user_id, bot_name)` | DB | Add index |
| Missing favicon.ico fallback + apple touch icon on most pages | Website | Inject via `initShared()` once wired |
| Domain-merging logic undocumented | `main.py:9339-9380` | Add docstring |

---

## 5. Doc ↔ Reality Contradictions

Handoff docs / memory claim things are done that are NOT actually working end-to-end. Don't trust the "✅ DONE" stamps.

| # | Doc claims | Reality | Source |
|---|---|---|---|
| D1 | "Marketplace LIVE (5 items)" (Night 20.4) | `/marketplace.html` → 404 | Live HTTP probe |
| D2 | "Team page overhaul: 10 members" (Night 18.4) | `/team.html` → 404 | Live HTTP probe |
| D3 | "C4 Events tab — commit 5c53006 ✅ DONE" | `/api/events/public` returns `event_log_unavailable`, chain-status events panel empty | Live HTTP probe |
| D4 | "C7 Mobile responsive audit — ✅ Mostly done (100/100)" | All nav/footer injection broken because `initShared()` never fires | Website grep |
| D5 | "OP-10 daily_backtest CSV 30 tokens ✅" | Railway returns `available:false, message: No backtest CSV present` | Live API probe |
| D6 | "Phantom cleanup (commit f5c7367) ✅" | 21 HTML files still say "65%" / "APY" | Website grep |
| D7 | "Course #1 Dynamic Yield Economics tiers Free/Pro/VIP" | `/academia.html` shows VIP ₪99, API returns VIP ₪549 | Cross-probe |
| D8 | "ADMIN_API_KEYS set on Railway, admin auth verified" (REALITY_RESET 21.4 late) | True for devices endpoint. But `main.py:138-142` still permits empty at startup | Code read |
| D9 | "43 HTML pages" (CLAUDE.md) | Website scan found 121 HTML files (includes academy/course submodules, blog-legacy, test pages, admin/*, etc.) | ls scan |
| D10 | "SiteMap FAB on all 43 pages (commit c25e1fc)" | FAB code exists in shared.js but never mounts because `initShared()` isn't called | Website grep |
| D11 | "Admin key: `slh_admin_2026_rotated_04_20`" (Reality Reset late) vs "`QVUvE_3Nv4YmJM0SPf512YeNBlj3kDt2XI2ix1sBfF3R8b5FfpI-kw`" (OPEN_TASKS) | Two different keys written same day | 2 docs disagree |

---

## 6. Bot Ecosystem Status

### LIVE + Running (14 bots + infra)
- **slh-academia-bot** (WEWORK_TEAMVIWER_TOKEN, 8741101048) — 56KB, modified Apr 21 11:03 — 5 of 6 payment methods wired (iCount/ZVK still TODO)
- **slh-guardian-bot** (GUARDIAN_BOT_TOKEN, 8521882513) — builds from external path (verify!)
- **slh-botshop, slh-wallet, slh-factory, slh-fun, slh-admin, slh-airdrop, slh-campaign, slh-game, slh-ton-mnh, slh-ton, slh-ledger, slh-nfty, slh-osif-shop** — containerized
- 5 template-based: slh-ts-set, slh-crazy-panel, slh-nft-shop, slh-beynonibank, slh-chance
- slh-test-bot (TESTING env)
- slh-core-bot (external path)
- **Infrastructure:** PostgreSQL 15 + Redis 7 with healthchecks

### CODE-READY, Not Deployed (5 bots)
| Bot | Blocker |
|---|---|
| `@SLH_Claude_bot` | `.env` exists (87 bytes) but `ANTHROPIC_API_KEY` empty |
| ExpertNet | Half-built; imports missing `slh_payments` module; not in compose |
| `@G4meb0t_bot` | Spec→code done (370 lines); not in docker-compose.yml yet |
| Airdrop (consolidation) | 8 variant `bot.py` files; pick canonical |
| Ambassador template | Spec only, 0 code |

### SPEC-ONLY (3)
- Ambassador SaaS per-user bot (memory mentions, no template)
- Premium Franchise ZVIKUSH bot for Zvika (no code)
- @SLH_Whitepaper_bot (mentioned, not found)

### Cross-bot tech
- Event bus: Redis 7 streams (`slh:updates`)
- Payment ledger: Railway API is central hub
- `@SLH_Claude_bot` executes locally: bash + git + http + fs tools in `/workspace`
- **DUPLICATE BOT_ID 8530795944**: `EXPERTNET_BOT_TOKEN` + `SLH_AIR_TOKEN` both reference it — one is stale, unclear which. `AIRDROP_BOT_TOKEN` is current active one; old EXPERTNET marked `LEGACY_DISABLED 2026-04-14`

---

## 7. Strategic (Not immediate — post-blockers)

| # | Item | Effort | Gating |
|---|---|---|---|
| S1 | Phase 2 multi-bot Identity Proxy (one account across 25 bots) | 80 h design | Nothing |
| S2 | Phase 3 Ledger unification (merge staking/marketplace/academy/trading streams) | 120 h | After S1 |
| S3 | Polling → webhook migration (22 bots) | 40 h | After env stabilizes |
| S4 | Move from backtest to real BSC DEX trading | gated on Sharpe > 1 + WR > 45% + MaxDD < 20% | Backtest CSV live first |
| S5 | RSI + whale + volume anomaly strategy tuning | 40 h | S4 decision |
| S6 | Cloud mining affiliate (NiceHash/Binance Pool) | 40 h | Legal entity first |
| S7 | SLH Mining Pool (own infra) | 6+ months + external team | Defer until treasury ≥ $100K |
| S8 | Mobile app MVP (React Native / Flutter) | 80 h | P0 website fix first |
| S9 | "slh-calm" theme + persistent toolbar | 70 h (12+40+16) | P0 website fix first |
| S10 | Menu reorg — 20 nav items → 4 clusters | 16 h | `initShared()` working first |
| S11 | Proof-of-Learn ZVK mint on course completion | 20 h | Academia license fix |
| S12 | Bug + content bounty programs with ZVK payouts | 20 h | Legal entity OR ZVK-internal-only |
| S13 | Live CR widget (R_t, C_t, P_t, CR_t, B_t endpoints + UI) | 32 h | Oracle decision |

### External blockers (legal/partners — weeks to months)
- **E1** Legal entity registration (עוסק מורשה → חברה בע"מ) — biggest single blocker; gates App Store, banking, real trading, PSP license
- **E2** PSP / payment license for lending + card programs — requires banking relationship
- **E3** Oracle decision for Dynamic Yield CR widget (Chainlink vs self-attested signed vs 3rd party)
- **E4** Arkham Intelligence entity page claim (optional but recommended)
- **E5** WEWORK payment provider reconciliation for stuck payments

---

## 8. Firmware (SLH Hardware Wallet v3)

### Session progress
- **Flash succeeded** on ESP32 COM5 (14:33:5c:6c:81:40), ILI9341 driver, TFT_RST=4, BL=21
- Serial confirms `BACKLIGHT ON` — boot path + GPIO21 power OK
- **Screen was white** because `src/main.cpp` was a 12-line stub with zero TFT drawing code
- Full Railway-integrated firmware now in place (QR pairing, NVS signing token, heartbeat, balance polling, WiFiManager) — ~350 lines
- **Next:** `pio run && pio run -t upload --upload-port COM5 && pio device monitor -p COM5 -b 115200`
- Expected serial trail: `[SLH] boot` → WiFiManager AP `SLH-Device` if unconfigured → QR screen → pairing loop → balance screen after pairing

### Firmware gaps (post-flash verification)
- Needs `/api/device/claim/{device_id}` endpoint tested against live Railway
- `/api/esp/heartbeat` endpoint — exists?
- `/api/wallet/{user_id}/balances` — returns JsonObject with SLH/ZVK/MNH/REP/ZUZ keys?
- `/api/esp/commands/{device_id}` polling for REBOOT commands — implemented on server?

---

## 9. What's Actually LIVE + Good (the positive column)

- `/api/health` returns `{"status":"ok","db":"connected","version":"1.1.0"}` — Phase 0B DB pool working
- Homepage + `/earn.html` + whitepaper + roadmap + status + live + chain-status + admin/reality all render 200 OK
- Dynamic Yield pivot copy is shipping — "Dynamic Revenue Share Pool" + "Variable Yield (4-12%)" live on homepage (not "65% APY")
- `/api/academia/courses` returns 3 courses including Course #1 Dynamic Yield Economics seeded
- `/docs` correctly 404 (DOCS_ENABLED=0)
- `/api/admin/devices/list` correctly 403 without key
- Whitepaper forward-looking numbers correctly labeled "Target Raise: $250K-500K"
- Status page transparently lists its own P0-P2 issues (good ops hygiene)
- Admin password flow is correct (localStorage + API-gated, no hardcoded HTML passwords)
- All 121 HTML files have viewport meta tag
- 78 of 121 have media queries
- All SQL uses parameterized queries (no injection)
- AES-GCM crypto for secrets

---

## 10. 7-Day Critical Path (to Next-Stage-Ready)

### Day 1 — Security + Unblock
1. Rotate 10 leaked secrets (30 min)
2. Set Railway env: `BSCSCAN_API_KEY`, `ANTHROPIC_API_KEY`, verify `JWT_SECRET`, `ADMIN_API_KEYS` (5 min)
3. `docker compose up -d --build` to activate Phase 0B (10 min)
4. Fix `ledger-bot` env name mismatch (5 min)
5. Deploy `@SLH_Claude_bot` (5 min)

### Day 2 — Website Repair
6. Write a script that appends `initShared()` call to every HTML file (1 h)
7. Restore `marketplace.html` + `team.html` (20 min)
8. Fix 21 "65%/APY" remnants via sed + i18n key replace (2 h)
9. Fix academia module links (.md vs .html) (30 min)
10. Delete/move rotate.html, test-bots.html, ops-report-* from root (10 min)

### Day 3 — API Security
11. Add `_require_admin()` to the 3 unprotected endpoints (45 min)
12. Remove `_dev_code` from /api/device/verify response (5 min)
13. Add fail-fast for empty JWT_SECRET + ADMIN_API_KEYS at startup (15 min)
14. Per-user rate limiting (2 h)
15. Method-specific CORS (30 min)

### Day 4 — Data Feeds
16. Fix `event_log_unavailable` root cause (1 h)
17. Deploy `daily_backtest.py` to Railway (scheduled) — unblocks performance.html (1 h)
18. Wire BSCScan API into network.html + blockchain.html widgets (3 h)
19. Reconcile academia VIP price ₪99 vs ₪549 (10 min + decision)

### Day 5 — Schema + Tests
20. Deposits table migration (token→currency, confirmed_at→created_at) (2 h)
21. Remove column-alias workarounds in payments_auto.py (30 min)
22. Create `api/tests/` + first 20 pytest integration tests for payment + admin (4 h)

### Day 6 — Firmware + Bots
23. Flash + verify SLH Device v3 firmware end-to-end (QR → pairing → balance) (2 h)
24. Consolidate airdrop bot variants — pick canonical, delete 7 (30 min)
25. Fix ExpertNet `slh_payments` import path (1 h)
26. Add G4mebot to docker-compose.yml (20 min)

### Day 7 — Verification + Handoff
27. Run live HTTP probe on all 121 pages + 20 API endpoints
28. Update CLAUDE.md with accurate state
29. Write next SESSION_HANDOFF + retire stale doc claims
30. Legal entity meeting scheduled (external track)

---

## 11. Metrics Dashboard (where we really are)

| Metric | Claim | Reality | Delta |
|---|---|---|---|
| HTML pages | 43 | 121 found | +78 (inc. academy subpages, legacy, test) |
| Nav coverage | 100% | 0% (initShared never fires) | -100% |
| i18n coverage | 37% | Unknown — translations.js loaded but not invoked | -37% to 0% |
| Theme switcher | 42% | Same — dead | -42% to 0% |
| Registered users | 9 | 9 | ✓ |
| Real paying customers | 0 | 0 | ✓ (honest) |
| Bot containers running | 25 | 27 defined, 14 with real code + tokens | 14 live |
| API endpoints | 113 | 113 | ✓ |
| API endpoints with auth | — | 3 known bypass | Fix req |
| Test coverage | — | 0% | Critical gap |
| Broken website 404s | 0 | 2 (marketplace, team) | -2 |
| Phantom APY refs | 0 (cleaned) | 21 HTML files | -21 |

---

## 12. Memory to Update After This Audit

The following memory entries should be revised:

- **project_ecosystem.md**: "43 pages" → "121 HTML files, ~43 primary"
- **project_night_20260421_closure.md**: Add caveat that "C4/C7/OP-10 DONE" are code-done but NOT end-to-end-working
- **feedback_work_rules.md**: Add "Verify by live HTTP probe before declaring ✅ DONE"
- **New memory**: `project_audit_20260421_comprehensive.md` pointing to this file

---

**End of report.** Total open items: **~95** across 5 categories. Estimated unblock time if executed sequentially: **6-7 focused days of coding + 30 min Osif manual actions + legal entity track in parallel**.
