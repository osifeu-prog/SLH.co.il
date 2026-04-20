# TON Secondary Receiving Address — Added 2026-04-20

## The address
```
UQCd7XHWGj06cBLlWW_DZUN3TWMGr_oWoVy0G0LkC14gQklj
```

- **Format:** TON mainnet non-bounceable (UQ prefix)
- **State:** uninitialized (fresh wallet, never sent outgoing TX)
- **Balance:** 0 nano TON
- **Purpose:** Backup receiving address alongside the primary `TON_PAY_ADDRESS` — for redundancy ("לייצר ביטחון")
- **Source:** Osif's secondary TON account (confirmed via `toncenter.com/api/v2/getAddressInformation`, ok=true)

## Current primary TON address (active)
```
UQCr743gEr_nqV_0SBkSp3CtYS_15R3LDLBvLmKeEv7XdGvp
```
Returned by `GET /api/payment/config` → `ton_address`. Set in Railway env as `TON_PAY_ADDRESS`.

## What "adding it" requires (Phase 2)

### Option A — Replace primary (simplest, but not redundant)
Osif updates Railway env: `TON_PAY_ADDRESS=UQCd7XHWGj...`

### Option B — Multi-address support (true redundancy)
Needs code changes in 3 places:

1. **Railway env** (Osif action):
   ```
   TON_PAY_ADDRESS_2=UQCd7XHWGj...
   ```

2. **Railway backend** (`api/routes/payments_auto.py:497` — `payment_config()`):
   ```python
   "ton_addresses": [TON_PAY_ADDRESS, os.getenv("TON_PAY_ADDRESS_2")],
   ```
   (keep `ton_address` for backward compat)

3. **Railway monitor** (`api/routes/payments_monitor.py`):
   Currently only polls BSC. When TON poller is added (see tonight's handoff), it must watch both addresses.

4. **academia-bot** (`bot.py:_create_payment` method=="ton"):
   Either: rotate between addresses deterministically (e.g., by user_id % len(addresses)) or offer a choice in the payment menu.

## Why not tonight
- bot.py is in an uncommitted state by another agent. Touching it risks clobber.
- `/api/payment/status/{user_id}` is still broken (HTTP 500). Fix that first — it blocks ALL blockchain payments from auto-granting licenses, making multi-address work cosmetic until resolved.
- Stars test path doesn't use TON addresses at all.

## Recommendation for next session
After the Stars E2E passes + status endpoint is fixed, do Option B in this order:
1. Add `TON_PAY_ADDRESS_2` env
2. Update `payment_config` to return both
3. Build TON poller that watches both
4. Update bot.py to show both (or rotate)

Estimated effort: 60-90 min (mostly TON poller — mirror `_bsc_latest_incoming` using toncenter.com/api/v2/getTransactions).
