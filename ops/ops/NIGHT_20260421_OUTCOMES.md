# Night 21.4 Outcomes — Level 4 → Level 5 → Ship

## What was delivered

A single-thread night that took a theoretical concern (Level 4 yield-platform math) through analysis (Level 5 break-even model) to shipped code and public pages. 5 items closed, 2 git repos updated, 3 Railway auto-deploys, 1 GitHub Pages deploy.

---

## 1. Archive: stale `api/routes/` → `archive/legacy_api_routes_20260420/`

- 22 modules + README with rollback
- 8 `"slh2026admin"` fallback references removed from grep-noise
- Verified: no imports from `api.routes.*`; `api/main.py` was broken as standalone (missing admin_rotate/bot_registry). See `archive/legacy_api_routes_20260420/README.md`.
- Commit: `99d4ce9`.

## 2. `/api/treasury/health` — Single Truth Test endpoint

- Public transparency endpoint. Aggregates **R / P / W / Buffer / Status** from real DB state.
- Env-configurable conversion rates (ZVK_ILS, SLH_PRICE_ILS, BNB_ILS, TON_ILS, USD_ILS), exposed in the response for honesty.
- Frontend: `website/treasury-health.html` with auto-refresh every 30s.
- Commits: `9774a78` (endpoint), `bc873f1` (page).

## 3. Level 5 break-even model + live bars

- Full doc: `ops/LEVEL_5_SLH_BREAKEVEN_MODEL.md`. Three tiers: Survival (1,000 ₪/mo), Sustainable (5,000), Thriving (20,000).
- Endpoint now returns `breakeven.{progress_pct, next_milestone, gap_to_next_ils}` block.
- Frontend: 3 progress bars rendered live.
- Commits: `b5d82ba` (endpoint+doc), `b04ad52` (page).

## 4. Revenue recording audit + fix

- **Finding:** zero payment flows were writing to `treasury_revenue`. `/api/treasury/health` was guaranteed to show R=0 forever.
- **Fix:** `record_revenue_internal()` helper in `routes/treasury.py`. Wired into:
  - `routes/payments_auto.py::_issue_receipt` → `source_type='payment_receipt'`
  - `routes/creator_economy.py::purchase_complete` → `source_type='marketplace_sale'`
- Env knobs: `MARKETPLACE_HOUSE_CUT=0` (current state), `ACADEMIA_HOUSE_CUT=0.30` (per CLAUDE.md).
- **Product decision left to Osif:** when to flip `MARKETPLACE_HOUSE_CUT` to `0.15` (requires updating seller payout logic in parallel).
- Doc: `ops/REVENUE_RECORDING_AUDIT_20260421.md`.
- Commit: `162a7f4`.

## 5. `/ambassador.html` — Ambassador SaaS public page

- 199 ₪/mo tier, public entry point. CTA: direct Telegram chat with @osifeu_prog (no half-built payment funnel).
- 6 benefits grid, VIP/Free comparison table, 7-item FAQ, final 15-min discovery call CTA.
- Commit: `ae2874b` (website repo).

## 6. Academia VIP tier on `/academia.html`

- 99 ₪/mo pricing card inserted between hero and stats bar.
- 6-benefit list, value-compare ("קורס יחיד = 199₪, 2 קורסים = 398₪, VIP = 99₪").
- CTA → Telegram to @osifeu_prog.
- Merged by Osif in commit `61482aa` (Dynamic Yield pivot) along with his own legal/compliance work.

## 7. `ops/generate_treasury_report.py` — Monthly report generator

- Python script, no deps beyond stdlib. Fetches live `/api/treasury/health`, formats Hebrew markdown report, saves to `ops/treasury-reports/YYYY-MM.md`.
- End-to-end verified against production Railway API.
- First real report generated: `ops/treasury-reports/2026-04.md` (confirms pre_revenue state, gap = 1,000 ₪ to Survival).
- Recommended schedule: cron/Task Scheduler on the 1st of each month.
- Commit: `162a7f4`.

## 8. ESP32 integration status audit

- Doc: `ops/ESP32_INTEGRATION_STATUS_20260421.md`.
- All 9 firmware↔API endpoints verified present. Pairing flow functional. System-audit admin card already shipped (`c83fb37`).
- 3-check checklist for Public Beta 2026-05-03:
  1. Live heartbeat verification on existing CYD board
  2. End-to-end pairing from a fresh board
  3. Admin command push test
- Commit: `162a7f4`.

---

## Git activity summary

**slh-api (master):**
- `99d4ce9` archive api/routes
- `9774a78` /api/treasury/health endpoint
- `b5d82ba` Level 5 breakeven block + doc
- `162a7f4` revenue recording wiring + 3 docs + report generator

**website (main):**
- `bc873f1` treasury-health.html
- `b04ad52` breakeven progress bars
- `61482aa` (Osif's commit — merged the VIP section I added to academia.html)
- `ae2874b` ambassador.html

---

## What changed since CLAUDE.md's "Current State" section

| Metric | CLAUDE.md | Progress Dashboard (live) | Delta |
|---|---|---|---|
| Users registered | 9 | 225+ | **+216** — CLAUDE.md is stale |
| Marketplace items | 5 | (not specified) | — |
| Genesis raised | 0.08 BNB | (not specified) | — |
| Receipts Issued | (not tracked) | **0.00** | audit finding confirmed |
| Creator Economy track | not in CLAUDE.md | **10%** | big gap to fill |

---

## Follow-ups for Osif (after waking)

1. **Flip `MARKETPLACE_HOUSE_CUT` when ready** — requires parallel update to seller payout logic (see REVENUE_RECORDING_AUDIT doc §"Product decision").
2. **Run the 3 ESP32 beta checks** before 2026-05-03.
3. **Schedule the monthly report** — cron on Railway or Windows Task Scheduler.
4. **Update CLAUDE.md "Current State"** — user count, active track percentages.
5. **First Ambassador sale** — the critical single number: turn R from 0 → 199. One conversation away.

---

## The one number to watch

**`R_ils_30d`** on `/api/treasury/health`. Currently `0`. Survival target: `1,000`. Everything in this night's work existed to make this number observable, actionable, and moveable.
