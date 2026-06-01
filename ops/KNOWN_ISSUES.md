# Known Issues — Verified Backlog (2026-04-21)

Each entry below was **verified in the current code** during this session.
Claims from older handoff docs that turned out to be already-fixed were removed.

Priority legend:
- **P0** — blocks shipping / is a security or monetary risk
- **P1** — visible bug but a workaround exists
- **P2** — cleanup / tech debt / nice-to-have

---

## P0 — blockers

### K-1. 10 secrets leaked in chat transcript (night 21.4)
- **Evidence:** OpenAI, Gemini, Groq, BSCScan, 2 bot tokens, JWT, ENCRYPTION, ADMIN_API_KEYS, one more appeared in chat per `project_night_20260421_audit.md`.
- **Fix:** rotate all of them; see [OPS_RUNBOOK.md §7](OPS_RUNBOOK.md#7-security-model) for locations. Owner: Osif.
- **Status:** 1 of ~11 rotated (GAME_BOT_TOKEN on 2026-04-17). The rest pending Osif.

### K-2. ~~3 admin endpoints bypass `_require_admin()`~~ **RESOLVED 2026-04-24**
- **Was:** `/api/registration/approve`, `/api/registration/unlock` (method=admin), and `/api/beta/create-coupon` accepted `admin_key` in body/query compared to `ADMIN_API_KEY` env with default `slh_admin_2026`. When env was empty (initial deploys) the default matched → anyone passing `"admin_key": "slh_admin_2026"` was admin.
- **Fix applied (commit `5abade2`):** each endpoint now prefers `_require_admin(authorization, x_admin_key)` header-based auth. Body field still accepted as a deprecated fallback but **rejects the `slh_admin_2026` placeholder explicitly**. Deprecation warning logged to server output.
- **Verified live:**
  - `POST /api/registration/approve` with `{"admin_key":"slh_admin_2026"}` → 403 (was 200/404 before fix)
  - `POST /api/registration/approve` with `X-Admin-Key: <valid rotated key>` → proceeds past auth
- **Follow-up:** remove the body-field fallback in 1 week after monitoring logs for legacy callers.

### K-3. `_dev_code` leaks in `/api/device/verify` response
- **Evidence:** `main.py:10498-10499` returns `dev_code` field so QR-pairing devs can see what to type. In production this exposes the code for attackers.
- **Fix:** gate behind `DEV=true` env var or remove entirely for prod responses.

### K-4. ~~`/api/events/public` returns `event_log_unavailable`~~ **RESOLVED 2026-04-24**
- **Was:** `/api/events/public` returned `{error:"event_log_unavailable"}`.
- **Reality:** The table was created lazily via `shared.events.ensure_event_log_table()` which `/api/events/public` already calls on every hit. Live probe: `curl /api/events/public?limit=3` → `{"events":[],"total_returned":0}` (empty but correct).
- **Fix applied:** Aligned `api/telegram_gateway._audit()` to use the canonical `shared.events.emit()` helper instead of a raw INSERT with wrong columns. Previous audit writes silently failed; now they succeed.
- **Canonical schema** (from `shared/events.py`):
  ```sql
  event_log (id BIGSERIAL, event_type TEXT, payload JSONB, created_at TIMESTAMP, source TEXT)
  -- NOTE: telegram_id and slh_user_id live INSIDE payload JSON, not as top-level columns
  ```

### K-5. `initShared()` never fires on 121 HTML pages
- **Evidence:** `website/js/shared.js:1091` defines `initShared()` but no `<script>initShared({...})</script>` call in any of the 121 HTML pages.
- **Impact:** nav bar, footer, theme switcher, i18n, PWA, FAB — all off on all public pages.
- **Fix (fastest):** add to bottom of `shared.js`:
  ```js
  document.addEventListener('DOMContentLoaded', function(){ initShared({}); });
  ```
- **Note:** the new `/miniapp/dashboard.html` does NOT need this; it uses its own init flow via `telegram-web-app.js` + the shim added 2026-04-21.

### K-6a. ~~`marketplace.html` 404~~ **RESOLVED 2026-04-24**
- **Was:** 404 despite `project_night_20260420.md` memory claiming "Marketplace LIVE (5 items)".
- **Reality:** page was never in git — memory was wrong. API `/api/marketplace/items` did return 5 items though, so the data side was correct.
- **Fix applied:** built `website/marketplace.html` from scratch — fetches `/api/marketplace/items?limit=50`, renders as grid with category filters (digital/physical/service/course), real stats strip, stock badges, "רכוש עכשיו" CTA linking to `/pay.html?product_id=mkt-<id>&amount=...`. Zero fake data. Commit shipped.

### K-6b. `team.html` 404 (still open)
- **Evidence:** `curl -I https://slh-nft.com/team.html` → 404. Not in git, not in local tree.
- **Blocker:** no `/api/team` endpoint exists in `main.py`. Building a static HTML with names+photos would violate the "no fake data" rule.
- **Fix:** (1) build `GET /api/team` returning founders + contributors from the `users` table filtered by role/flag; (2) add `assets/team/` directory for photos; (3) build `website/team.html` consuming the endpoint. Estimated 2 hours end-to-end.

### K-7. Phase 0B docker rebuild required
- **Evidence:** 9 bots have code changes committed but running containers are from a stale image.
- **Fix:** `docker compose up -d --build` (see [OPS_RUNBOOK.md §6](OPS_RUNBOOK.md#6-deployment-procedures)).

### K-8. ledger-bot crash loop (TOKEN vs BOT_TOKEN)
- **Evidence:** `docker-compose.yml` passes `TOKEN=${BOT_TOKEN}` but service reads `LEDGER_BOT_TOKEN`.
- **Fix:** edit compose, restart.

### K-9. ANTHROPIC_API_KEY empty in `slh-claude-bot/.env`
- **Evidence:** verified via `awk` on `.env` — key has 0 chars.
- **Fix:** Osif pastes key from console.anthropic.com into `D:\SLH_ECOSYSTEM\slh-claude-bot\.env` line 8. Do **not** paste in chat.
- **Impact:** @SLH_Claude_bot handlers /health, /price, /devices, /task work (they don't use Claude); free-text handler fails with "ANTHROPIC_API_KEY not set" until fixed.

### K-9b. SMS provider not configured on Railway
- **Evidence:** `/api/device/register` response shows `delivery: "pending"` with `sms_provider: "disabled"` in production. The `api/sms_provider.py` module is wired but no SMS_PROVIDER env var is set.
- **Fix (pick one):**
  - **Twilio:** signup + get `TWILIO_ACCOUNT_SID`/`TWILIO_AUTH_TOKEN`/`TWILIO_FROM` → set on Railway + `SMS_PROVIDER=twilio`
  - **Inforu (Israeli, cheaper):** signup at inforu.co.il → set `INFORU_USERNAME`/`INFORU_API_TOKEN`/`INFORU_SENDER` + `SMS_PROVIDER=inforu`
  - **019 Mobile:** similar flow with `SMS019_USERNAME`/`SMS019_PASSWORD` + `SMS_PROVIDER=sms019`
- **Impact:** new users can't complete device pairing without Telegram-linked phone. Currently ESP OTP shows on-screen via `_dev_code` only in dev. See [OPS_RUNBOOK.md §SMS (OTP) provider](OPS_RUNBOOK.md#sms-otp-provider).

### K-9c. Systemic mojibake in `main.py` string literals (pre-existing)
- **Evidence:** On 2026-04-23, `main.py` contained 861 U+FFFD characters and 78 corrupted em-dash sequences (`�?"`) that broke parsing at multiple lines (251, 257, 1193, …).
- **Root cause:** a previous session opened main.py in latin-1, saved as utf-8, losing Hebrew chars in the process.
- **Fix applied this session:** restored from `main.py.bak_20260422_162309` (clean backup, zero U+FFFD), stripped BOM, re-applied SMS integration. **Zero U+FFFD remain, parses clean.**
- **Action required:** whoever opens main.py in an editor next — confirm their editor is set to UTF-8 (no BOM) before saving. Notepad.exe tends to save as UTF-8-BOM by default; use VS Code with `files.encoding: utf8`.

### K-10. Academia VIP price mismatch (`₪99` vs `₪549`)
- **Evidence:** `/academia.html` shows tier at `₪99`; `/api/academia/courses` returns `₪549` for VIP.
- **Fix:** decide canonical number + align both.

---

## P1 — visible bugs with workaround

### K-11. `buy.html` hardcodes `tokenPrices={SLH:122, ZVK:1.2, MNH:0.27}` + `|| 122` fallback
- **Evidence:** `website/buy.html:333-334`.
- **Risk:** quoted buy amounts for SLH are based on ~122 (old target?) while real SLH target is 444.
- **Fix:** hydrate `tokenPrices` from `/api/prices` on page load; for tokens not in `/api/prices` (SLH, MNH, ZVK), add a new endpoint `/api/wallet/price?tokens=SLH,MNH,ZVK` that returns internal prices; show `--` + disable buy button if price unknown.

### K-12. Activity emoji corruption on dashboard (`ðŸ¤`, `ðŸ'Ž`, `ðŸ"¤`)
- **Evidence:** verified in live preview of `/miniapp/dashboard.html` — activity feed shows mojibake instead of 📤, 💎, 🤝.
- **Root cause:** data is encoded UTF-8 but read as Latin-1 somewhere between DB → API JSON.
- **Fix:** find the emoji insertion path in `main.py` transaction endpoints — likely writing with wrong encoding.

### K-13. Phantom "65% APY" across 14 pages after Dynamic Yield pivot
- **Evidence:** `project_night_20260421_i18n.md` notes 27 occurrences; JS layer fixed (commit `7ff9db1`) but HTML layer still has 14 files × 27 occurrences.
- **Fix:** bulk replace `65%` → `Dynamic` in HTML files listed in the i18n closure doc.

### K-14. `/api/performance` returns `available: false`
- **Evidence:** `daily_backtest.py` has not been scheduled on Railway.
- **Fix:** add to `scheduled-tasks` or call on startup.

### K-15. Deposits schema drift (`token` vs `currency`, `confirmed_at` vs `created_at`)
- **Evidence:** root cause of user 8789977826 paying ₪196 with 0 licenses (documented in `project_ecosystem.md` → ACADEMIA_PAYMENT_OVERHAUL). Patched in commit `b4da6b1` but schema not unified.
- **Fix:** database migration to pick one set of column names everywhere.

### K-16. `admin.html` still uses localStorage for password storage
- **Evidence:** `website/admin.html` reads `localStorage.slh_admin_password`.
- **Risk:** XSS → steal admin key.
- **Fix:** migrate admin.html to Mini App + Gateway auth (Phase 2 per migration plan).

---

## P2 — cleanup / tech debt

### K-17. BSCScan widget zeros out without `BSCSCAN_API_KEY`
- **Evidence:** `/network.html` + `/blockchain.html` show 0 holders + 0 tx. Env var not set on Railway.
- **Fix:** Osif — set `BSCSCAN_API_KEY` on Railway.

### K-18. 94 `console.log` calls in production website JS
- **Evidence:** grep `console.log` in `website/**/*.html` + `website/**/*.js`.
- **Fix:** remove or gate behind a debug flag before prod launch.

### K-19. Stale deploy artifacts still accessible
- **Evidence:** `website/rotate.html`, `website/test-bots.html`, `website/ops-report-20260411.html` shouldn't be public.
- **Fix:** delete per [TELEGRAM_FIRST_MIGRATION_PLAN.md §deletes](TELEGRAM_FIRST_MIGRATION_PLAN.md#delete-stale-duplicate-or-test).

### K-20. 121 HTML pages reported but mapping lists 100
- **Evidence:** `ls website/*.html | wc -l` = 100; migration plan says "100"; earlier audit says "121".
- **Explanation:** 21 pages are in subdirectories (`/miniapp/`, `/admin/`, others). Count by path, not just top-level.

### K-21. Zero automated tests on 114 API endpoints
- **Evidence:** no `tests/` directory in repo root.
- **Fix:** scaffold pytest with 20 tests covering payment + admin critical paths.

### K-22. Recursive referral count fake (direct only counted)
- **Evidence:** `main.py` referral tree endpoint counts Gen 1 only, despite UI claiming Gen 1-10 total.
- **Fix:** recursive CTE query.

### K-23. `SLH_PRICE_USD` hardcoded in `creator_economy.py`
- **Evidence:** `D:\SLH_ECOSYSTEM\creator_economy.py` contains `SLH_PRICE_USD = 121.6` constant.
- **Fix:** read from `/api/prices` or a single source.

### K-24. 8 versions of `airdrop/bot.py` on disk
- **Evidence:** `ls D:\SLH_ECOSYSTEM\airdrop\bot*.py` shows `bot.py`, `bot_v2.py`, `bot_fixed.py`, etc.
- **Fix:** consolidate to one file, delete the rest.

### K-25. Duplicate BOT_ID `8530795944` in `.env`
- **Evidence:** both `EXPERTNET_BOT_TOKEN` and `SLH_AIR_TOKEN` share the same ID — one is stale.
- **Fix:** rotate one of them via BotFather, update `.env`, restart affected service.

---

## Claims from external sources we checked and did NOT find

These were asserted in prior handoffs / pasted chat content but verified absent in the current code. Do not re-add them to the backlog:

| Claim | Claimed location | Real state |
|-------|------------------|------------|
| `\|\| 47` fake fallback | `website/community.html` | Already fixed — current code is `\|\| { total_posts: '—', posts_today: '—', active_today: '—', total_users: '—' }` at line 1728 |
| `<span>47</span>` hardcoded | HTML files | Grep for literal `>47<` across website/ — no matches |
| `active_today \|\| 47` | HTML files | No occurrences in current website/ files |

These claims originated from a grep snapshot dated 2026-04-13 (`ops/FRONTEND_API_CONTRACT_20260413_171657.txt:63`) which is stale.
