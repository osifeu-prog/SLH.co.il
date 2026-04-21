# SLH Spark — Level 5 Break-Even Model

**Date:** 2026-04-21
**Author:** Level 5 pass on the Level 4 analysis — grounded in real SLH state, not generic yield-platform assumptions.
**Source of truth:** `/api/treasury/health` endpoint + CLAUDE.md current state.

---

## 1. Fixed Monthly Burn (real, excluding Osif's time)

The minimum R needed just to stop bleeding.

| Item | ILS/mo | Notes |
|---|---|---|
| Railway (FastAPI + PostgreSQL + Redis) | 90–180 | Scales with traffic; currently low |
| Domain (slh-nft.com, annualized) | 5 | $15/year |
| Telegram bot hosting (if separate from Railway) | 0–70 | 25 bots; if same Railway bundle, $0 extra |
| Anthropic API (Claude bot + AI chat endpoint) | 70–220 | Usage-dependent |
| Misc tooling (monitoring, email, etc.) | 20–40 | |
| **Total floor** | **185–515 ILS/mo** | Use **300 ILS/mo** as working baseline |

→ **Daily floor ≈ 10 ILS/day**. That's your "R minimum" before any growth.

---

## 2. Unit Economics Per Channel

What one transaction contributes to house revenue (after your cut).

| Channel | Avg Ticket | House Cut | Per-Unit Net | Volume for 1,000 ILS/mo |
|---|---|---|---|---|
| Academia — Course (one-time) | 199 ILS | 30% | 60 ILS | **17 sales/mo** |
| Academia — VIP (monthly sub) | 99 ILS | 100% | 99 ILS | **11 active subs** |
| Marketplace — sale | 150 ILS | 15% | 22.5 ILS | **45 sales/mo** |
| Ambassador SaaS (monthly sub) | 199 ILS | 100% | 199 ILS | **6 active ambassadors** |
| Premium bot group (monthly sub) | 49 ILS | 100% | 49 ILS | **21 subs** |
| Genesis NFT (one-time) | 0.03 BNB ≈ 165 ILS | 100% | 165 ILS | 6/mo until sold out (49 cap) |

**Observation:** Ambassador SaaS has **8× more revenue per customer than Marketplace**. VIP subscriptions are 4×. Marketplace only pays off at high volume.

---

## 3. Three Break-Even Scenarios

### Scenario A — Survival (1,000 ILS/mo)
Covers fixed burn + small slack. The bar to "not lose money."

**Minimum recipes** (pick any one):
- 11 Academia VIPs, OR
- 6 paying Ambassadors, OR
- 45 Marketplace sales, OR
- **Realistic mix:** 3 Ambassadors + 5 VIPs + 10 Marketplace = **597 + 495 + 225 = 1,317 ILS/mo**

### Scenario B — Sustainable (5,000 ILS/mo)
Infra + marketing budget + dev tools + small reserve. Osif covers side-expenses.

**Realistic mix:**
- 15 Ambassadors (2,985) + 20 VIPs (1,980) + 40 Marketplace (900) + 2 courses/mo (120) = **5,985 ILS/mo**
- This is **also** where the 10% SLH buyback commitment becomes meaningful: 598 ILS/mo → ~1.35 SLH bought back at target price.

### Scenario C — Thriving (20,000 ILS/mo)
Osif can work on SLH part-time as primary income. Ecosystem funds itself.

**Realistic mix:**
- 40 Ambassadors (7,960) + 60 VIPs (5,940) + 150 Marketplace (3,375) + 10 courses (600) + 30 premium groups (1,470) = **19,345 ILS/mo**
- Buyback budget: 2,000 ILS/mo → ~4.5 SLH/mo at target. Starts meaningfully compressing circulating supply.

---

## 4. Sensitivity — What Actually Moves the Needle

If you only have 40 hours of work, sorted by revenue per hour:

| Lever | Revenue delta / customer | Effort to acquire | ROI rank |
|---|---|---|---|
| Ambassador recruitment | 199 ILS/mo recurring | HIGH (personal sales conversation) | 🥇 |
| Academia VIP onboarding | 99 ILS/mo recurring | MEDIUM (content-driven) | 🥈 |
| Course production + sale | 60 ILS one-time | HIGH (content creation upfront) | 🥉 |
| Marketplace listing growth | 22.5 ILS one-time | LOW (mostly automation) | 4th |
| Genesis NFT promotion | 165 ILS one-time | MEDIUM (one-time campaign) | 5th (not recurring) |
| Premium bot group | 49 ILS/mo recurring | LOW–MED (requires content) | 6th |

**Key insight:** Ambassador SaaS has the best $/hour ratio because it's **recurring + high ticket + scales without you**. Each ambassador operates their own bot.

---

## 5. Proposed 30-Day OKR

Concrete, measurable, tracked via `/api/treasury/health`:

| Goal | Target | Revenue | Status tracking |
|---|---|---|---|
| 1. Ambassador onboarding | 3 paying | 597 ILS/mo | `revenue_by_currency.ILS` tagged `source_type='ambassador_sub'` |
| 2. Academia VIP | 10 active subs | 990 ILS/mo | `source_type='academia_vip'` |
| 3. Marketplace volume | 20 transactions | 450 ILS/mo | existing marketplace flow → `source_type='marketplace_sale'` |
| 4. 1 course launched | 5 sales | 300 ILS one-time | `source_type='academia_course'` |
| **Total target** | | **2,337 ILS/mo** | = 2.3× Survival, 47% of Sustainable |

This gets you to **Green (Healthy)** status on the transparency page within a single month of focused selling.

---

## 6. Current Gap vs. Target (what's REALLY missing)

Looking at what CLAUDE.md reports today:

| Metric | Current | Scenario A (Survival) | Gap |
|---|---|---|---|
| Paying Ambassadors | 0 | 6 | -6 |
| Academia VIPs | 0 (Academia pre-launch) | 11 | -11 |
| Marketplace sales (lifetime) | unknown, likely < 20 | 45/mo | needs baseline |
| Genesis raised | 0.08 BNB (~175 ILS) | N/A (one-time) | N/A |
| **R (lifetime, ILS)** | ≈0 | 1,000/mo | ≈1,000 |

**Bottom line:** You're not in a "model failure" — you're in **pre-launch**. The math of Level 4 doesn't apply yet. Level 5 (this doc) tells you **exactly when it starts to apply**: when P (contingent ZVK liability) crosses ~100 ILS and R starts flowing.

Current P ≈ 0 because ZVK issuance so far is tiny and non-redeemable for cash. Current R ≈ 0 because no recurring revenue channel has been turned on yet. **Neither is a crisis — both are a starting line.**

---

## 7. Dangerous Scenarios to Avoid

| Scenario | Risk | Mitigation |
|---|---|---|
| Promise APY on SLH | Becomes "P guaranteed" — triggers Level 4 collapse math | **Never** promise yield on SLH. Market price only. |
| Add ZVK→cash redemption | Turns ZVK from reward into cash liability | Keep ZVK internal (Academia/Marketplace credit only) |
| Aggressive referral payouts | Compounds P before R exists | Cap referral depth at 2 levels; commission ≤ 10% of purchase, not recurring |
| Raise more Genesis before Academia ships | Investor expectation debt without R | **Ship Academia revenue before next raise** |

---

## 8. When Does Level 4 Math Actually Apply?

Only when **all three** conditions hit:
1. TVL (user-held SLH) > 5,000 SLH (~2.2M ILS at target)
2. Promised yield (if any) exists
3. Withdrawal paths enable bank-run behavior

**None of these are true today.** Revisit this model at 1,000 active holders.

---

## 9. Next Actions (in priority order)

1. **Ambassador pricing page** — create a public `/ambassador.html` with clear 199 ILS/mo tier + signup. Channel this through @SLH_Claude_bot or directly to @osifeu_prog.
2. **Academia VIP enrollment** — launch `/academia.html` VIP tier; wire payment → `treasury/revenue/record` so it lands in the dashboard.
3. **Revenue-record instrumentation audit** — verify every existing payment flow (Academia, Marketplace, Genesis) calls `POST /api/treasury/revenue/record`. Any flow that doesn't = invisible revenue.
4. **Breakeven overlay on transparency page** — add `breakeven_targets` field to `/api/treasury/health`, render a "You are at X% of Survival target" progress bar.
5. **Monthly treasury report** — auto-generated PDF from `/api/treasury/health` snapshot at month-end, stored in `ops/`.

---

## 10. The One Number to Watch

**R_ils_30d ≥ 1,000**

When this crosses 1,000 ILS, you've achieved Survival. Everything before that is pre-revenue. Everything after that is scaling.

Today: R_ils_30d ≈ 0. Target: 1,000. Distance: one ambassador + a few VIPs.
