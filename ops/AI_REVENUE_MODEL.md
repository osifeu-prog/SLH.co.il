# SLH AI Spark — Revenue Model & Operations

**Status:** Phase A live (2026-04-25). Awaiting `ANTHROPIC_API_KEY` for full activation.
**Owner:** Osif Kaufman Ungar (telegram 224223270 / 8789977826).
**Single source of truth for pricing:** `slh-claude-bot/pricing.py`.

---

## 1. The Product

**SLH AI Spark** — paid AI access via the existing `@SLH_Claude_bot` Telegram bot. Users get Claude Sonnet 4.5 + workspace tools (filesystem, git, bash, http) for a monthly subscription paid in Telegram Stars.

**Why Telegram Stars (not Stripe/PayPlus):**
- Zero merchant onboarding (works today)
- Zero PCI/compliance burden
- Native Telegram UX (no out-of-app redirect)
- Pay-out in fiat once SLH passes Telegram's threshold
- Apple/Google IAP fees are absorbed by Telegram, not us

**Why this product first:**
- Already-built bot infrastructure
- Recurring (compounds), not one-time
- Self-funding from Day 1 (customer pays before SLH spends on Anthropic)
- Demonstrates the whole stack to investors as a working revenue product

---

## 2. Tier Structure

| Tier | Price | Stars | Quota | AI Provider | Use case |
|------|-------|-------|-------|-------------|----------|
| **Free** | ₪0 | — | 10 msg/month | Groq/Gemini (free) | Acquisition |
| **Pro** | ₪29 | 500 | 70 msg/month | Claude Sonnet 4.5 + tools | Power users |
| **VIP** | ₪99 | 1500 | 350 fair-use | Claude + tools + priority | Builders, ambassadors |
| **ZVK** | earned | — | 1 msg / 1 ZVK | Claude + tools | Token utility |

All numbers live in `slh-claude-bot/pricing.py:TIERS`. Edit there, never hardcode in HTML/copy.

---

## 3. Unit Economics (per active subscriber per month)

Assumptions:
- Avg conversation = 5K input + 1.5K output tokens ≈ ₪0.135 cost on Anthropic
- Telegram realization rate = 70% (mobile IAP + Telegram fee assumed worst case)
- USD/ILS = 3.60

| Tier | Revenue (gross) | Revenue (net) | AI cost (max) | **Margin** |
|------|-----------------|---------------|---------------|------------|
| Free | ₪0 | ₪0 | ₪1.35 | **−₪1.35** (acquisition) |
| Pro | ₪29 | ₪20.30 | ₪9.45 | **+₪10.85 (53%)** |
| VIP | ₪99 | ₪69.30 | ₪47.25 | **+₪22.05 (32%)** |

**Break-even analysis:**
- 1 Pro pays for 8 Free users
- 1 VIP pays for 16 Free users
- 100 Pro → ₪1,085/month net = ₪13K/year

---

## 4. Architecture

```
slh-claude-bot/
├── pricing.py         # Tier specs, margin math (single source of truth)
├── subscriptions.py   # SQLite layer: subscriptions, ai_usage, payments
├── quota.py           # Pre-flight check + post-flight log middleware
├── payment_flow.py    # /upgrade, /credits, /pricing + Telegram Stars handlers
├── admin_panel.py     # /revenue, /quota_user, /set_tier, /anthropic_spend, /top_users
├── migrations/
│   └── 001_subscriptions.sql
└── bot.py             # Wires it all in on_text + main()
```

**Data flow per message:**
```
User text → on_text → quota.check(user_id) → 
  if !allowed:  send refusal_he ("/upgrade pro" prompt)
  if  allowed:  pick AI client (free vs anthropic) → 
                converse → reply → quota.record(...) → counter++
```

**Data flow per payment:**
```
/upgrade pro → invoice (500 Stars) → user pays → 
  pre_checkout_query (approve) → 
  successful_payment → record_payment(completed) → 
  upgrade(user_id, "pro") → counter reset, period extended 30d
```

**DB tables (SQLite, lives at `/workspace/slh-claude-bot/sessions.db`):**
- `subscriptions`: user_id (PK), tier, current_period_*, messages_used, payment_*
- `ai_usage`: per-message log with tokens + cost (used by /revenue, /top_users)
- `payments`: ledger of every Stars charge (charge_id, status, raw_payload)

---

## 5. Operations

### Bringing the system online

1. **Get Anthropic key:** https://console.anthropic.com/settings/keys
2. **Set env var:**
   ```powershell
   notepad D:\SLH_ECOSYSTEM\slh-claude-bot\.env
   # Add: ANTHROPIC_API_KEY=sk-ant-api03-...
   ```
3. **Recreate container:**
   ```powershell
   cd D:\SLH_ECOSYSTEM
   docker compose up -d --force-recreate claude-bot
   ```
4. **Verify in Telegram:**
   - DM `@SLH_Claude_bot` → `/start`
   - `/credits` → shows "Tier: free · 10/10 messages"
   - `/upgrade pro` → invoice arrives → pay 500 Stars → tier flips to pro
   - Send any text → response should now use Anthropic (verify in `/revenue`)

### Cost monitoring (do these weekly)

```
/anthropic_spend     → ILS spent on Anthropic last 1d/7d/30d
/revenue             → MRR + revenue 30d + net profit
/top_users           → Top 10 by message count (helps spot abuse)
```

**Anthropic dashboard cap:** Set monthly spend cap at https://console.anthropic.com/settings/billing/limits to **$200/month initially**. Raise as MRR grows. This is the hard ceiling that prevents runaway costs from a bug or abuse.

### Tier adjustments

If margins compress (real token usage > model assumption), tighten quotas in `pricing.py`:

```python
# Example: drop Pro from 70 to 50 messages
"pro": TierSpec(..., monthly_quota=50, fair_use_cap=50, ...)
```

Then `docker compose up -d --force-recreate claude-bot`. Existing subscribers keep their period (no auto-downgrade); new period starts at next renewal.

### Refunds

Manual via admin command:
```
/set_tier <user_id> free
```
Then refund Stars manually via Telegram support if needed (rare; Telegram's policy).

---

## 6. Risk & Mitigation

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Anthropic cost spike (real tokens > est.) | Medium | Anthropic spend cap + weekly /anthropic_spend review |
| Abuse (1 Pro user × 70 huge messages) | Low | fair_use_cap enforced; /top_users surfaces outliers |
| Telegram Stars fee higher than 30% | Low | `pricing.expected_margin_ils(realization=0.5)` re-check; raise prices if needed |
| User dispute / chargeback | Very low | Stars are non-refundable by Telegram default; we control refund via /set_tier |
| ANTHROPIC_API_KEY leak | Medium | Never paste in chat; only in .env or Railway env var |
| Compliance — is this a security? | None | SaaS subscription, not a token sale. Israeli VAT applies (17%) at invoicing. |

---

## 7. Documentation Map

- **This doc** — model + ops (canonical)
- **`slh-claude-bot/pricing.py`** — numeric truth
- **`slh-claude-bot/CLAUDE.md`** ← TODO Phase B — agent rules for editing this stack
- **`ops/SESSION_HANDOFF_20260425_AI_SPARK.md`** — handoff for next session
- **`/admin/revenue.html`** ← future — web dashboard mirror of /revenue Telegram command

---

## 8. Future Phases

**Phase B** (next session — ~2 hours):
- `slh-claude-bot/CLAUDE.md` agent rules
- Real token-count threading from `claude_client.converse` → exact cost tracking
- `/admin/revenue.html` web dashboard

**Phase C** (after Phase B — ~3 hours):
- Ambassador SaaS: per-ambassador sub-bot, revenue split
- ZVK credits flow: earn-via-Academia → spend on AI
- Migrate from Telegram Stars to PayPlus when MRR > ₪1,000 (lower fee = +20% margin)

**Phase D** (when MRR > ₪5,000):
- White-label per ambassador (their own bot username)
- API key for power users (BYOK + 30% platform fee)
- Tiered Anthropic models (Haiku for Free@cost, Sonnet for Pro/VIP)
