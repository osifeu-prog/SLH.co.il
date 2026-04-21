# Revenue Recording Audit — 2026-04-21

## TL;DR

**Before this change:** zero payment flows recorded to `treasury_revenue`. The `/api/treasury/health` dashboard was guaranteed to show `R = 0` forever, no matter how many sales happened. Every sale was **invisible**.

**After this change:** both live payment completion points now write revenue entries with house-cut-applied amounts, plus full audit metadata. The Single Truth Test from the Level 5 model can finally light up in response to real activity.

---

## What was found (grep evidence)

```
grep "/api/treasury/revenue/record" D:\SLH_ECOSYSTEM\ → only docs, 0 callers
grep "INSERT INTO treasury_revenue" D:\SLH_ECOSYSTEM\routes\ → only treasury.py itself
```

Every payment completion point in the live tree was writing to its own table (`payment_receipts`, `creator_sales`, `marketplace_orders`) but **never** publishing a revenue event that the transparency endpoint aggregates.

Impacted flows (all were silent):

| Flow | File | Committed at | Previously recorded revenue? |
|---|---|---|---|
| TON/BSC auto-verify receipt | `routes/payments_auto.py::_issue_receipt` | line 149 INSERT | ❌ No |
| External (Stripe/PayBox/Bit) receipt | same `_issue_receipt` caller | same helper | ❌ No |
| Marketplace purchase completion | `routes/creator_economy.py::purchase_complete` | line 386 INSERT creator_sales | ❌ No |
| Academia VIP / course | (not yet launched — pre-revenue) | N/A | N/A |
| Genesis NFT mint | (no code path exists for minting→revenue) | N/A | N/A |
| Ambassador SaaS subscription | (not yet built) | N/A | N/A |

---

## What changed

### 1. New helper in `routes/treasury.py`

```python
async def record_revenue_internal(conn, source_type, amount_gross, currency,
                                  source_id=None, user_id=None,
                                  house_cut=None, metadata=None) -> None
```

Same DB connection as the caller — no HTTP round-trip, safe inside an open
transaction, **swallows its own exceptions**. Policy: better to have invisible
revenue than to break a live sale because of an audit bug.

### 2. Env-configurable house cuts

| Variable | Default | Notes |
|---|---|---|
| `MARKETPLACE_HOUSE_CUT` | **0** | Preserves current "100% to seller" behavior. Set `0.15` on Railway to monetize. |
| `ACADEMIA_HOUSE_CUT` | `0.30` | Matches CLAUDE.md 70/30 split (lecturer/house) |
| `PAYMENT_HOUSE_CUT` | `1.0` | Direct deposits → 100% treasury |
| `TREASURY_BUYBACK_RATE` | `0.10` | 10% of fiat revenue earmarked for SLH buyback |
| `TREASURY_BURN_RATE_AIC` | `0.02` | 2% of AIC marketplace sales burned |

`source_type` auto-selects the cut if the caller doesn't pass one. `payment_receipt` / `marketplace_sale` / `academia_course` / `academia_vip` / `ambassador_sub` / `premium_group` / `genesis_nft` are all handled.

### 3. Call sites wired

- `payments_auto.py` — `_issue_receipt()` now always records a `payment_receipt` revenue entry after the receipt is persisted. Receipt metadata (origin_source_type, tokens_granted) is embedded in `treasury_revenue.metadata`.
- `creator_economy.py` — `purchase_complete()` records a `marketplace_sale` entry after `INSERT INTO creator_sales`. With `MARKETPLACE_HOUSE_CUT=0`, the amount is 0 — but the audit trail (buyer, seller, item, gross, currency) is captured, so the history will be complete from the day monetization is switched on.

---

## Product decision Osif must make

The default `MARKETPLACE_HOUSE_CUT=0` is a faithful reflection of the current UX: sellers expect 100% of their sale. **If you want Marketplace to contribute to survival R, you must:**

1. Decide the cut — 10% / 15% / 20% are realistic for a digital-goods marketplace.
2. Communicate to existing sellers that starting `<date>` the platform takes `X%`.
3. Set `MARKETPLACE_HOUSE_CUT=0.15` on Railway.
4. The seller payout UX (`marketplace_earnings_usd`) still computes on the FULL amount today — you'll want to subtract the house cut from seller earnings too. **Follow-up TODO:** update `_compute_xp` and seller payout logic to subtract the cut.

Until step 4, turning on the cut creates an accounting mismatch (house gets revenue logged, seller also gets full amount). **Leave `0` until the payout side is synced.**

---

## What this unlocks

- `/api/treasury/health.R_revenue.ils_today` starts moving as payments happen.
- `/treasury-health.html` Survival progress bar animates from 0% toward 100% in real time.
- Level 5 break-even milestones become **observable**, not just aspirational.
- Future audits (security reviews, investor due diligence) have a single trustworthy source for the revenue question.

---

## Rollback

Both edits are additive and wrapped in `try/except`. If something explodes, the safe revert is:

```bash
git revert <commit-sha>
```

No data loss — `treasury_revenue` rows written before rollback remain valid records of what happened.

---

## Next steps (tracked in Level 5 OKRs)

1. ✅ Revenue recording wired (this commit)
2. ⬜ Ship `/ambassador.html` public page
3. ⬜ Add Academia VIP tier + payment flow that feeds revenue
4. ⬜ Monthly treasury report generator (reads `/api/treasury/health` snapshot → `ops/treasury-reports/YYYY-MM.md`)
5. ⬜ Decide `MARKETPLACE_HOUSE_CUT` + update seller payout
