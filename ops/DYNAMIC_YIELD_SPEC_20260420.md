# SLH Dynamic Yield — Master Economic Specification
**Date:** 2026-04-20
**Author:** Osif (founder) + collaborative audit
**Status:** PROPOSED — pending implementation
**Replaces:** Fixed APY claims (48% / 55% / 60% / 65%) across site + bots

---

## 0. Why this document exists

External audits (Level 3 deep scan, 2026-04-20) identified the root problem of SLH's current economic presentation:

> **Liabilities > Demonstrated Revenue.**
> The system advertises fixed yields (48%–65% APY) and a 10-tier referral tree before any external revenue stream is proven. That is structurally Ponzi-adjacent, regardless of intent.

This document replaces the fixed-APY model with a **Revenue-Backed Dynamic Yield** framework. It is the single source of truth for all future SLH copy, code, smart-contract hooks, and the backing content of Academia Course #1.

---

## 1. Core Principle

**User rewards are derived exclusively from real, verifiable system revenue.**

No yield is promised. No APY is fixed. Every distribution event is computed from cashflow that already arrived on-chain or in the platform ledger.

---

## 2. Variables

| Symbol | Meaning | Unit |
|---|---|---|
| `U_t` | Total Value Locked (sum of staked balances at time t) | USD-equivalent |
| `R_t` | Real revenue for period t (fees, course sales, SaaS, marketplace %) | USD |
| `C_t` | Operational costs for period t (infra, payroll, gas) | USD |
| `Ref_t` | Referral payouts for period t | USD |
| `W_t` | Withdrawals for period t | USD |
| `B_t` | Treasury buffer / insurance fund | USD |
| `k` | Distribution coefficient (fraction of net revenue distributed to stakers) | 0..1 |
| `balance_user` | Individual user's staked balance | USD |
| `CR_t` | Coverage Ratio | ratio |
| `L_t` | Liquid assets (on-chain + fiat reserves) | USD |

---

## 3. Core Formulas

### 3.1 Net revenue available for distribution
```
Net_t = max(0, R_t - C_t - Ref_t)
```
If costs + referrals exceed revenue → `Net_t = 0` → **no distribution that period.**

### 3.2 Pool distribution
```
P_t = k · Net_t
```
Default `k = 0.5` (half of net revenue to stakers, half to buffer + growth).
`k` is adjustable by governance but **cannot exceed 0.7** and **cannot be raised** when `CR_t < 1.5`.

### 3.3 Per-user yield (pro-rata)
```
Yield_user = (balance_user / U_t) · P_t
```

### 3.4 Implied APY (derived, not promised)
```
APY_implied ≈ (P_t · periods_per_year / U_t)
```
Displayed on dashboard as **"Last period's implied APY"** with explicit language: *"Past performance. Not a forecast. Not a guarantee."*

### 3.5 Coverage Ratio (stability test)
```
CR_t = (Net_t + B_t) / (P_t + W_t)
```
**Mandatory invariant: `CR_t ≥ 1`.**
Target operating range: `CR_t ∈ [1.5, 3.0]`.

### 3.6 Run Risk
```
Run_Threshold = L_t / U_t
```
If a withdrawal spike exceeds `L_t` → **circuit breaker fires** (see §5).

---

## 4. Stability Constraint (The Only Promise)

```
For every period t:
    R_t - C_t - Ref_t  ≥  P_t + ΔB_t
```

This is the **only** guarantee SLH makes about its economics. If the constraint is violated, distributions stop that period. Users see:
> "Revenue this period did not exceed obligations. Coverage protection engaged — no distribution. Treasury unaffected."

---

## 5. Protection Mechanisms (Circuit Breakers)

| Trigger | Action | User-visible message |
|---|---|---|
| `CR_t < 1.0` | Halt distribution, reduce `k` by 20% | "Coverage guardrail active — distribution paused this period." |
| `CR_t < 0.5` | Freeze new deposits, keep withdrawals open | "Treasury protection mode — deposits paused." |
| `W_t > 0.15 · U_t` in 24h | Throttle per-user withdrawal to 1% of balance/day | "High-withdrawal regime detected — pro-rata limits in effect." |
| `B_t < 0.10 · U_t` | Divert 100% of `Net_t` to `B_t` until buffer ≥ 15% | "Buffer recovery mode — yields temporarily 0, will resume when B ≥ 15%." |
| On-chain oracle drift > 5% | Freeze new entries until reconciled | "Oracle reconciliation — operations paused." |

All triggers are enforced **before** the UI shows any yield number.

---

## 6. Revenue Sources (`R_t` composition)

| Source | Status | Expected contribution |
|---|---|---|
| Academia course sales | **LIVE (this document enables Course #1)** | 40% target |
| Marketplace transaction fee (5%) | LIVE — 5 items 2026-04-20 | 20% |
| @WEWORK_teamviwer_bot service subscriptions | LIVE — 6 payment methods | 15% |
| Bot-per-ambassador SaaS (Ambassador program) | Spec'd, not live | 10% |
| External ZVK primary sales to approved partners | Partial | 10% |
| DEX fees (when SLH liquidity grows) | Future | 5% |

**No revenue line includes "new deposits from users" or "referral signup bonuses."** Deposits are liabilities, not revenue.

---

## 7. Referral Redesign

| Before | After |
|---|---|
| 10-tier deep payout | **2 tiers maximum** |
| Paid from new-user deposits | **Paid from `Ref_t` budget carved out of `R_t` (not from staker pool)** |
| Percentages growing with network depth | Flat: Tier 1 = 20% of referee's course/service purchase; Tier 2 = 5% |
| Cash payouts | Paid in ZVK (internal), not SLH or TON |

This cuts legal exposure ~90%: 2 levels with revenue-share is common affiliate marketing, 10 levels from deposits is MLM-Ponzi pattern.

---

## 8. Treasury Layer

Public wallet addresses published on `/status`:
- **BSC Treasury:** (to be assigned — NOT the main MetaMask which holds 199K SLH personal)
- **TON Treasury:** (to be assigned)
- **Fiat/PSP Reserve:** aggregate balance published weekly, signed by founder

Minimum treasury policy: `B_t ≥ 0.15 · U_t` before any `k` increase is considered.

---

## 9. Public Dashboard (Transparency Requirement)

`/status` page must render live (≤5min refresh):
- `U_t` — current TVL
- `R_t` — revenue this period (running)
- `C_t`, `Ref_t`
- `P_t` — pool distributed last period
- `CR_t` — coverage ratio (with color: green ≥1.5, yellow 1.0-1.5, red <1.0)
- `B_t` — treasury buffer ($ and % of U_t)
- Implied last-period APY (with disclaimer)
- **Last 12 distribution events** (date, amount, CR at that time)

If any of these cannot be rendered → dashboard shows "System data unavailable — distributions paused until telemetry restored." Never fallback to stale numbers.

---

## 10. Migration Plan for Existing Stakers

Users who already entered the old Fixed-APY pools (48/55/60/65):

**Option A — Grandfather:** Honor the original terms until their lock expires, funded out of a dedicated legacy wallet (separate from new Dynamic Yield pool). No new deposits accepted into legacy terms.

**Option B — Volunteer Conversion:** Offer conversion to Dynamic Yield pool with bonus ZVK (e.g., +10% of principal in ZVK) to incentivize migration. Users who convert get earlier access to Course #1 (free tier).

**Option C — Full Refund Window:** 30-day window to withdraw principal without penalty, regardless of lock period.

Legacy liability is sized once, bounded, and displayed on `/status` as `Legacy_Obligations` (separate line item, not mixed with `P_t`).

---

## 11. Legal Shield Requirements (Parallel Workstream)

Before this model goes live on the site, the following must be published:
1. `/terms.html` — Terms of Service
2. `/privacy.html` — Privacy Policy
3. `/risk.html` — Risk Disclosure (explicit: "not securities, not banking, not insured")
4. `/aml.html` — AML/KYC summary (MiCA-aligned)
5. Footer disclaimer on every page: *"SLH Spark is an early-stage crypto ecosystem. Dynamic Yield is revenue-share, not a financial product. Past distributions do not guarantee future ones. Not investment advice."*

---

## 12. Course #1 Positioning

Course #1 — **"Dynamic Yield Economics — Crypto That Doesn't Collapse"** — is:
1. The **public documentation** of this spec (educational)
2. The **first external revenue line** under Dynamic Yield itself (recursive proof: the course's revenue funds the pool that distributes under the rules the course teaches)
3. The **signal to the market** that SLH has pivoted from yield-promise to transparency-as-product

See `COURSE_1_SPEC_20260420.md` for curriculum, pricing, sale mechanics.

---

## 13. Versioning

This spec is versioned. Changes require:
- Spec revision in `ops/DYNAMIC_YIELD_SPEC_*.md` (new date)
- Changelog entry on `/status`
- Announcement to stakers ≥7 days before any `k` change

---

## 14. Open Questions (to resolve before v1.1)

- [ ] Exact `k` default (current proposal: 0.5) — sensitivity analysis in `treasury_simulation.py`
- [ ] TON-side treasury wallet generation + signing policy
- [ ] Oracle source for on-chain revenue verification (Chainlink? self-attested + signed?)
- [ ] Legacy pool funding method (founder capital contribution? revenue carve-out?)
- [ ] Governance mechanism for future `k` changes (founder decision vs. SLH holder vote)

---

**End of spec v1.0 — 2026-04-20**
