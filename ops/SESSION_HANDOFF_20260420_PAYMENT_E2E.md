# Session Handoff — 2026-04-20 · Payment E2E Investigation

**Duration:** ~90 min (evening)
**Context:** Osif asked to "close the extended scope" — implement full payment pipeline: real transfer, course delivery, points, stars, broadcast. Multi-agent session with another agent building Stars+QR+Mini App in parallel on the same bot.py file.

---

## TL;DR

1. **Agent 2 built** the user-facing payment UX (Stars + QR + Mini App + 7 payment methods). Container rebuilt, code live at MD5 `251b75db...`, 1430 lines. **Not yet committed.**
2. **Investigation surfaced 2 bugs** in the Railway backend that block auto-grant for blockchain payments — but Stars path bypasses both.
3. **Delivered:** `ops/create_payment_intent.py` wrapper + 3 live intents for Osif's testing + clear E2E protocol.
4. **Blocked:** Osif to tap `/buy` → Stars → pay. I monitor logs. On success → commit all + update handoff.

---

## What I verified tonight

### Architecture

| Component | State |
|---|---|
| `academia-bot` container | Up 30 min, MD5 matches disk, Telegram connected |
| Bot code | 1430 lines (was 1119), 489 lines of uncommitted additions by another agent |
| Stars handler (`on_successful_payment`) | Atomic: parses payload → INSERT INTO academy_licenses → sends materials_url. Idempotent. |
| Railway monitor (`/api/payment/monitor/status`) | Running, 30s poll interval, 0 matches ever |
| Intent endpoint (`POST /api/payment/monitor/intent`) | ✅ Live, verified with 3 successful creates |

### Bugs discovered (not fixed tonight — out of scope / risky)

1. **`/api/payment/status/{user_id}` returns HTTP 500** (any user).
   - Location: `api/routes/payments_auto.py:458`
   - Impact: Bot's `_wait_and_grant` polling fails — even if monitor catches a BSC tx and flips premium, bot never sees `has_premium=True`, never writes license.
   - Workaround: Stars path doesn't use this endpoint. For BSC/TON we'd need to fix this or write license via another mechanism.

2. **Monitor main loop only polls BSC** — no TON auto-poll.
   - Location: `api/routes/payments_monitor.py:187` (`_loop`)
   - Impact: TON payments require manual `POST /api/payment/ton/auto-verify` with tx_hash.
   - The code handles TON branching (line 129, 135, 160) but no `_ton_latest_incoming` exists.

### Bot handlers confirmed present

From direct read of bot.py:
- `_send_stars_invoice` (line 889): `currency="XTR"`, no provider_token (native Telegram Stars)
- `on_pre_checkout` (line 918): unconditional approve
- `on_successful_payment` (line 928): grants license, idempotent, writes to academy_licenses

---

## Intents created tonight (live)

| id | chain | amount | user | status |
|---|---|---|---|---|
| 1 | ton | 0.01 | 224223270 | open (~2h) |
| 2 | bsc | 0.001 | 224223270 | open (~2h) |
| 3 | bsc | 0.000123 | 999999 (test) | open — disposable |

---

## Files changed tonight

**Created:**
- `ops/create_payment_intent.py` — helper to create intents via CLI (78 lines, self-contained, no deps beyond stdlib)
- `ops/SESSION_HANDOFF_20260420_PAYMENT_E2E.md` — this file

**Modified (mine):**
- `academia-bot/requirements.txt` — added `qrcode[pil]==7.4.2` (may be redundant; agent 2 uses URL-based QR)

**Modified (agent 2, not mine):**
- `academia-bot/bot.py` (+489 lines): payment_methods_kb with 7 buttons, Stars invoice flow, QR via api.qrserver.com, Mini App WebApp for bank, payout_phone wizard
- `api/routes/academia_ugc.py`: payout_phone column + validator
- `docker-compose.yml`: SUPPORT_HANDLE "@SLHSupport" → "@osifeu_prog"

**Untracked (agent 2):**
- `ops/ACADEMIA_PAYMENT_OVERHAUL_20260420.md` — Phase 1/1.5/2/2.5/3 roadmap

---

## E2E test protocol (Stars — golden path)

**Why Stars:** bypasses both bugs above. Telegram confirms payment → bot's `on_successful_payment` writes license atomically. No Railway polling, no status endpoint dependency.

1. In `@WEWORK_teamviwer_bot`: send `/buy` → see 7 payment buttons
2. Tap ⭐ Telegram Stars → native Telegram invoice opens
3. Pay with Telegram Stars (Osif has TON in @wallet → can convert TON→Stars)
4. Telegram confirms → `on_successful_payment` fires
5. Bot writes `academy_licenses` row + sends success message with `materials_url`

**Verification:**
```bash
docker logs slh-academia-bot --since 5m --timestamps | grep -E "on_successful_payment|pre_checkout"
docker exec slh-postgres psql -U postgres -d slh_main -c \
  "SELECT * FROM academy_licenses WHERE user_id=224223270;"
```

## E2E test protocol (BSC — blocked on status endpoint bug)

1. Create intent: `python ops/create_payment_intent.py 224223270 bsc 0.001 academy_1 academia`
2. Send exactly 0.001 BNB to `0xd061de73b06d5e91bfa46b35efb7b08b16903da4`
3. Monitor auto-matches within 30-60s → flips premium in Railway DB
4. **BLOCKED**: bot's polling can't detect because `/api/payment/status` returns 500
5. **Workaround**: manually `INSERT INTO academy_licenses` after confirming matched=true in Railway DB

---

## Next session priorities

1. **IF Stars E2E passed tonight:** commit agent 2's work + this handoff + intent script
2. **Fix `/api/payment/status/{user_id}` 500 bug** (1 hr est., probably null-handling or missing table)
3. **Add TON poller to monitor** (~1-2 hr) — mirror `_bsc_latest_incoming` using toncenter.com API
4. **Wire intent creation into `_create_payment`** for TON/BSC in bot.py (single aiohttp.post call, ~5 lines)
5. **Admin /approve command** — Osif-only command that takes payment_id and writes license directly (backup path)

## Blockers on Osif

Inherited from previous handoffs:
- Railway: rotate `ADMIN_API_KEYS` to `QVUvE_...` + add `BOT_SYNC_SECRET` (agent 2 noted these)
- BotFather: rotate leaked tokens
- `ANTHROPIC_API_KEY` for `slh-claude-bot/.env`

New from tonight:
- **The Stars E2E test itself** — needs Osif to initiate `/buy`
- **Commit authorization** — I won't commit agent 2's work until Osif confirms Stars test passed

---

## Session cleanup

- Background log stream (task `bxsty44h2`) running — safe to leave; auto-terminates with shell
- 3 intents expire in ~2 hours — no cleanup needed
- No containers restarted, no services stopped

*Handoff drafted while waiting for user test. Will be finalized with commit hash + test outcome in the next update.*
