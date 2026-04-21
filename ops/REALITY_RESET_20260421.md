# Reality Reset — 2026-04-21
**Trigger:** Osif's message 2026-04-21 ~11:30 (cleartext, summarized):
> "User 8789977826 is us. I don't have real new users or payers. Some deposited
>  on PancakeSwap, otherwise no real data. The system doesn't allow user
>  management or control. Everything looks like it works but it doesn't."

This document resets our shared understanding of the platform state and
re-orders the roadmap accordingly.

---

## The Honest State (verified 2026-04-21 via /api/ops/reality)

### Users
- **23 total** in `web_users`
- **18 real Telegram IDs** (≥ 1,000,000)
- **3 are Osif himself**: 224223270 (@osifeu_prog), 7757102350 (@Osif83), 8789977826
- **1 is Tzvika** (co-founder, 1185887485)
- **1 is Adam** (nephew tester, 6466974138, memory-documented)
- **~13 community members** — mostly Genesis 49 coupon holders, handful of unregistered browsers
- **5 test/fake IDs** (<1M) still in the DB

### Payments (real + test)
- **4 external_payments rows** — ALL are Osif's self-test (classified, flagged)
- **1 receipt** issued
- **₪0 real customer revenue**
- **0 deposits indexed in API** (the `deposits` table is empty)

### PancakeSwap — THE ONLY REAL ACTIVITY
- Some wallets did deposit on PancakeSwap but the API doesn't index on-chain events
- Liquidity is ~$19.56 per Arkham/ApeSpace snapshot
- 227 holders per same source — but our DB has ZERO of these linked to users

### Courses / Licenses
- 4 courses now in DB (1 demo intro-slh + 3 Course #1 tiers I seeded)
- 2 licenses total — both to Osif himself (self-test + make-good)

### Control surface (before today)
- `/admin.html` exists with 19 sidebar pages
- Most `/api/admin/*` endpoints 403 because `ADMIN_API_KEYS` env is empty on Railway
- `ADMIN_BROADCAST_KEY` works (default: `slh-broadcast-2026-change-me`)

---

## What changed today in response

### Shipped 2026-04-21
1. **`/api/ops/reality`** — new read-only admin snapshot endpoint, auths via
   `ADMIN_BROADCAST_KEY`. Returns users (split founder/community/test),
   payments (real/self-test), licenses, courses, deposits, broadcasts.
   See `api/main.py` line ~10850+.

2. **`/admin/reality.html`** — honest admin dashboard. Single page, no phantom
   data. Every user labeled. Arkham Intelligence + BscScan + TonViewer links
   on every on-chain address. localStorage for broadcast key.

3. **Cleanup in DB** — all 4 payments for user 8789977826 reclassified with
   `self_test: true, classification: "founder_dogfood"`. Original
   `refund_status: pending_review` was wrong (we thought it was a real
   customer) — now voided.

### Reality principle (going forward)

> **Every page must either show TRUE data or display `--`, `N/A`, or be
>  explicitly tagged `[DEMO]` / `[SEED]` per CLAUDE.md conventions.**

Any page showing made-up numbers (TVL, users, staked amount, APY) without
real backing is a bug and must be fixed or marked.

---

## Roadmap re-sequencing

The previous `ROADMAP_13_PLUS_20260421.md` assumed we were running a
production platform with users. That assumption was wrong. The new
sequence acknowledges we are in **pre-traction alpha**:

### Week 1 (RIGHT NOW, 2026-04-21 to 04-27)
Higher priority than anything else:

- [x] **#A1** — `/api/ops/reality` + `/admin/reality.html` ✅ SHIPPED TODAY
- [ ] **#A2** — Phantom data audit of all 43 HTML pages
  - Grep every page for hardcoded numbers (TVL, users, staked, APY)
  - Replace with `--` or fetch from live API
  - Mark [DEMO] / [SEED] where legitimate
- [ ] **#A3** — Arkham Intelligence deep-link pass
  - Every on-chain address in the site links to Arkham
  - Status page shows live BscScan-sourced SLH holder count, LP balance
- [ ] **#A4** — PancakeSwap deposit indexer
  - Backfill the `deposits` table with real BSC pool activity
  - Match by wallet → telegram_id when known; otherwise orphan deposits stay for manual claim
- [ ] **#A5** — Basic admin mutations (replaces dashboard-building)
  - POST `/api/ops/credit` — give a user ZVK/SLH, auth via broadcast key
  - POST `/api/ops/approve-payment` — mark external_payment approved, auto-grant license
  - POST `/api/ops/ban` — flip is_registered, note reason in metadata

### Week 2-3 (was "UI/UX overhaul")
**KEEP, but lower priority than reality work:**

- #16 slh-calm theme + toolbar (was my #16, still valid)
- #17 Menu reorganization
- #18 Blog + newsletter

### May (was "analytics + PWA")
- #19 Analytics (meaningless until A2 is done)
- #20 Live CR widget
- #21 PWA hardening

### Demote (previously Q3, now Q4+)
- #22a Google Play
- #22b App Store
- #13b SLH mining pool (only if Treasury ≥ $100K, currently $0)

### Delete entirely
- #23c Community forum — premature, we have <15 community members

---

## What Osif needs to do THIS WEEK

### Immediate (tonight / tomorrow):
1. **Open `https://slh-nft.com/admin/reality.html`**
   - Paste your `ADMIN_BROADCAST_KEY` (the same one I used for broadcast)
   - See every real user, every real payment, every real anything
   - Click Arkham links to verify on-chain

2. **Verify the reality summary matches your intuition.** If it doesn't,
   the DB is lying somewhere — come back to me.

### This week:
3. **Set `ADMIN_API_KEYS` on Railway** — 10 min job, unblocks half the admin.html pages
4. **Decide:** should I prioritize #A2 phantom-data audit, #A4 PancakeSwap
   indexer, or #A5 admin mutations next?

### Pending from previous handoff (still valid):
- AISITE restart (code ready, Osif-only action)
- Legal entity registration (external)

---

## Arkham Intelligence clarification (was item #15)

**Resolved.** "ארקם" = Arkham Intelligence (https://intel.arkm.com).

Integration levels (from free to paid):
1. **Deep-link pass (done)** — every address in `/admin/reality.html` +
   across public site links to Arkham. Free. No API.
2. **Claim entity page** — register SLH as an entity on Arkham so the public
   SLH-labeled wallets show up as "SLH Spark" instead of unnamed addresses.
   Free, 1h of form-filling. Worth doing.
3. **API integration** (paid, $1K/month+) — pull live holder data, counterparty
   analysis, whale movements. **Skip until we have revenue.**

Recommended: do #2 this week.

---

## Dashboards promised vs. dashboards delivered

| Promised page | Status | Reality |
|---|---|---|
| `/status.html` | Exists | Shows static mock data mostly. Needs A2 audit. |
| `/dashboard.html` | Exists | Shows user-level data. Works if user is logged in. |
| `/admin.html` | Exists, 19 pages | Most call admin endpoints that 403 due to empty ADMIN_API_KEYS |
| `/admin/reality.html` | **NEW today** | Works via broadcast key. Truth source. |
| `/ops-dashboard.html` | Exists per CLAUDE.md | Not audited this session |

---

## Bottom line

You are not running a struggling platform with a broken UI.
You are running a **pre-launch alpha with ~13 friends and family as beta users**, a real smart contract deployed, a legit tokenomics pivot underway, and infrastructure that outpaces the user base.

**That's fine.** Just stop pretending otherwise in the UI.

The reality dashboard is your compass now. Everything we build from here
should show real numbers or clearly-labeled placeholders — nothing else.

---

*End of Reality Reset — 2026-04-21*
