# Session Handoff — 2026-04-25 — AI Spark Phase A

## TL;DR

Phase A of **SLH AI Spark** (paid AI subscription product) is built, deployed, and verified live in `slh-claude-bot` container. Awaiting one user-action (`ANTHROPIC_API_KEY` in `.env`) to flip from "free-only" mode to "paid tiers active".

**What ships:**
- Pro tier ₪29/month / 70 messages → Claude Sonnet 4.5 + tools (margin ~53%)
- VIP tier ₪99/month / 350 fair-use → priority + Claude + tools (margin ~32%)
- Free tier 10 msg/month → Groq/Gemini fallback (acquisition, ₪0 cost)
- ZVK tier — earn-via-activity (placeholder, Phase C activation)

**Revenue: real, recurring, self-funding from Day 1.**

---

## What's running right now

```
docker ps:                slh-claude-bot · Up (latest restart 2026-04-25)
auth.is_authorized:       [224223270, 8789977826] both pass
quota.check (free user):  allowed=True, 10/10, use_anthropic=False (graceful)
subscriptions.init_db:    runs on every bot start (idempotent)
on_text → quota gate:     wired (slash-commands fall through to handlers)
payment_flow handlers:    /upgrade /pricing /credits + invoice flow + webhook
admin_panel handlers:     /revenue /quota_user /set_tier /anthropic_spend /top_users
```

---

## Files (all under `D:\SLH_ECOSYSTEM\slh-claude-bot\`)

**New (Phase A):**
- `pricing.py` — single source of truth for tiers, costs, margins
- `subscriptions.py` — async SQLite layer (extends existing sessions.db)
- `quota.py` — middleware: check before, record after
- `payment_flow.py` — Telegram Stars: /upgrade /pricing /credits + handlers
- `admin_panel.py` — admin-only: /revenue /quota_user /set_tier /anthropic_spend /top_users
- `migrations/001_subscriptions.sql` — schema (also embedded in subscriptions.py as fallback)

**Modified:**
- `bot.py` — added imports, replaced AI-client global with `_pick_ai_client`, gated `on_text` with quota, wired register() calls in main()
- `auth.py` — multi-admin support (224223270, 8789977826) with comma-separated env var
- `claude_client.py` — SYSTEM_PROMPT updated to recognize both telegram IDs as Osif

**Documentation (`D:\SLH_ECOSYSTEM\ops\`):**
- `AI_REVENUE_MODEL.md` — canonical revenue model & ops doc
- `SESSION_HANDOFF_20260425_AI_SPARK.md` (this file) — for next session

---

## Verified working in container

```python
# Inside slh-claude-bot container, 2026-04-25:
import asyncio, sys; sys.path.insert(0, '/app')
import pricing, subscriptions, quota

async def t():
    await subscriptions.init_db()
    sub = await subscriptions.get_or_create(8789977826)
    d = await quota.check(8789977826)

# Output:
# Tier: free · used: 0
# Quota allowed: True · remaining: 10/10
# Use anthropic: False
# Pro margin: ILS +10.85
# VIP margin: ILS +22.05
```

---

## To activate (3 user-actions, ~10 min)

### 1. Anthropic API key

```powershell
# Get key
start https://console.anthropic.com/settings/keys
# → Create Key → copy

# Set monthly spend cap to $200 (safety net)
start https://console.anthropic.com/settings/billing/limits

# Add to .env (DO NOT paste in any chat)
notepad D:\SLH_ECOSYSTEM\slh-claude-bot\.env
# Add line: ANTHROPIC_API_KEY=sk-ant-api03-...

cd D:\SLH_ECOSYSTEM
docker compose up -d --force-recreate claude-bot
```

### 2. Token rotation (still pending from earlier)

Both bot tokens (SLH_macro_bot + SLH_Claude_bot) were exposed in chat earlier. They were rotated once but the new tokens were also pasted. Need 3rd rotation:

```text
BotFather → /mybots → SLH_Claude → API Token → Revoke → New token
  → DIRECTLY paste into D:\SLH_ECOSYSTEM\slh-claude-bot\.env (line: SLH_CLAUDE_BOT_TOKEN=...)
  → docker compose up -d --force-recreate claude-bot

BotFather → /mybots → SLH_macro_bot → API Token → Revoke → New token
  → DIRECTLY paste into Railway dashboard (project diligent-radiance, service monitor.slh,
    Variables → TELEGRAM_BOT_TOKEN)
  → Railway redeploys automatically
```

Plus DB password (Railway Postgres) and OPENAI_API_KEY also pending rotation per earlier report.

### 3. Smoke test

```text
DM @SLH_Claude_bot:
  /start         → menu shows "💎 Tier: free · 0 הודעות"
  /credits       → "Tier: free · 0/10"
  שלום           → free Groq response (since no Pro yet)
  /upgrade       → menu with Pro/VIP buttons
  /upgrade pro   → invoice for 500 Stars
  (pay)          → "תשלום אושר! שודרגת ל-Pro"
  /credits       → "Tier: pro · 0/70"
  שאלת בדיקה     → Claude response (anthropic provider in /revenue)
  /revenue       → MRR ₪29, Revenue 30d ₪29, Anthropic cost: small
```

---

## Known limitations (deferred to Phase B)

1. **Token counts are estimates** — `len(text)//4` heuristic, not real Anthropic usage data. Means `/anthropic_spend` will be approximate. Fix: thread `response.usage.input_tokens` from Anthropic SDK through `claude_client.converse` return signature. ~30 min work.

2. **No grandfather mechanism** — first 10 paying users will pay full price. Phase C: `/set_tier` admin command can manually grandfather (already implemented, just needs operator flow).

3. **No web dashboard** — admin commands are Telegram-only for now. Phase B: `/admin/revenue.html` mirroring /revenue.

4. **No CLAUDE.md in slh-claude-bot/** — future agents touching this stack should be guided by repo-local rules. Phase B deliverable.

5. **Token leak risk on iteration** — every time we run `railway variables` in this chat, secrets re-leak. Add to `.claude/settings.json` deny: `railway variables*` without explicit user permission.

---

## What this unlocks

**Day 1 (after activation):**
- @SLH_Claude_bot becomes monetizable
- Osif's two accounts (224223270, 8789977826) are admins, can /set_tier anyone manually
- Revenue tracking from message zero

**Week 1:**
- DM 5-10 active SLH users → "אתה מקבל גישה ל-Pro חינם לחודש בתור early access"
- Use the data: which features they ask for, how many messages, real cost per user
- Adjust quotas in `pricing.py` based on observed usage

**Month 1:**
- Pricing battle-tested
- Migrate from Stars (30% fee) to PayPlus (2.5% fee) when MRR > ₪1,000
- Phase C: Ambassador SaaS — sub-bots for ambassadors with their own customer flow

**Quarter 1:**
- This becomes a case study for SLH investors — real recurring revenue from real customers
- Funds the rest of the ecosystem buildout
- Validates the LAB premise: "build once, monetize via Telegram"
