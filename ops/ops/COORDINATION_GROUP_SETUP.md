# SLH Agents Coordination Group — Setup

**Date:** 2026-04-26
**Status:** Phase 1 (claude-bot only)
**Group invite:** `https://t.me/+aww1rlTDUSplODc0` (INTERNAL ONLY — do not commercialize)

## What this is

A single Telegram group where all SLH bots and AI agents can:
- **Post** status events (deploys, errors, alerts, ready-checks).
- **Receive** commands via `@bot_username <cmd>` mentions.

Activated by setting `COORDINATION_GROUP_CHAT_ID` env to the group's numeric chat_id. When unset, all coordination calls are no-ops — bots run normally with zero coordination traffic.

## Why this group ≠ a VIP product

The invite link `+aww1rlTDUSplODc0` was previously listed in `tonmnh-bot/data/products.json` as a paid VIP perk (3 products: VIP Pack, ORG, STRAT). Per Osif's 2026-04-26 decision, this group is **internal coordination only** — no commercial track. The product entries were updated:
- `group_link` blanked for products 1, 2, 3 (commit on this branch).
- `vip_group()` handler in `tonmnh-bot/src/handlers/user_commands.py` already falls back to "No group link found. Contact admin." when blank — safe failure mode.
- A replacement VIP group must be provisioned before re-introducing those products.

## Architecture

```
shared/coordination.py         <- helper module (aiogram + raw-token variants)
scripts/capture_coordination_chat_id.py  <- one-shot to discover chat_id
shared/group_config.json       <- registry entry (no invite_link, internal_only flag)
slh-claude-bot/bot.py          <- Phase 1 wiring (POC)
docker-compose.yml             <- env passthrough for claude-bot
.env.example                   <- COORDINATION_GROUP_CHAT_ID + SLH_CLAUDE_BOT_USERNAME
```

The helper exposes:
- `is_enabled()` / `is_coordination_group(chat_id)` — checks
- `post_event(bot, source, event_type, message)` — outbound (aiogram bot)
- `post_event_via_token(token, ...)` — outbound (raw HTTP, for non-aiogram bots)
- `register_inbound(dp, bot_username, handlers={...})` — inbound (aiogram dispatcher)

Auth boundary: **group membership IS the authorization**. Anyone in the coordination group can call any command. Keep the group locked down to admins.

## Phase 1 scope (now)

Only **@SLH_Claude_bot** is wired. It:
- Posts `[OK] [claude-bot] @SLH_Claude_bot polling · AI=...` on startup.
- Listens for these commands in the group:
  - `@SLH_Claude_bot ping` → `pong`
  - `@SLH_Claude_bot health` → API health line
  - `@SLH_Claude_bot who` → bot identity + AI mode

Other 23 bots remain unchanged. Phase 2 wires them once the chat_id is captured and Phase 1 is verified working.

## Setup procedure (Osif must do these manually)

### Step 1 — Add @SLH_Claude_bot to the group

1. Open `https://t.me/+aww1rlTDUSplODc0` in Telegram.
2. From inside the group: tap title → Manage Group → Administrators → Add Administrator → search for `@SLH_Claude_bot` → grant **send messages** permission (read-all is fine; admin role optional for Phase 1).
3. **Important:** Telegram bots cannot read messages in groups by default unless they are admins OR have privacy mode disabled via BotFather. For the inbound `@SLH_Claude_bot ping` command to work, either:
   - Make the bot a group admin, **or**
   - Open BotFather → `/mybots` → `@SLH_Claude_bot` → Bot Settings → Group Privacy → Disable.

### Step 2 — Capture the chat_id

From the project root on the Windows host:

```powershell
cd D:\SLH_ECOSYSTEM
python scripts\capture_coordination_chat_id.py
```

Then in the group, send any message (e.g. `hi`). The script prints:

```
FOUND group: chat_id=-1001234567890  title='SLH Agents'  type=supergroup

Add to .env (project root) AND to Railway env vars:
    COORDINATION_GROUP_CHAT_ID=-1001234567890
```

Copy the numeric chat_id.

### Step 3 — Set the env vars

**Project root `.env`** (for local docker-compose):
```
COORDINATION_GROUP_CHAT_ID=-1001234567890
SLH_CLAUDE_BOT_USERNAME=SLH_Claude_bot
```

**Railway env vars** (for any future Railway-hosted bots — currently API only, but good hygiene):
- Railway dashboard → slh-api → Variables → add `COORDINATION_GROUP_CHAT_ID=-1001234567890`.

### Step 4 — Restart claude-bot

```powershell
cd D:\SLH_ECOSYSTEM
docker compose restart claude-bot
docker logs slh-claude-bot --tail 20
```

You should see:
```
shared.coordination loaded; enabled=True
register_inbound: SLH_Claude_bot wired with 3 handler(s): health, ping, who
starting @SLH_Claude_bot · AI mode: ...
connected as @SLH_Claude_bot (id=...)
```

And in the coordination group, a posted message:
```
[OK] [claude-bot] @SLH_Claude_bot polling · AI=anthropic-tools+free-fallback
```

### Step 5 — Verify inbound

In the group, send:
```
@SLH_Claude_bot ping
```

Expected reply: `pong`.

Try also `@SLH_Claude_bot health` and `@SLH_Claude_bot who`.

## Phase 2 (next — after Phase 1 verified)

Wire the other 23 bots. Each needs:
1. `from shared.coordination import post_event, register_inbound` (with sys.path adjustment for non-claude-bot containers — varies by Dockerfile).
2. `await post_event(bot, "<bot-name>", "ready", "...")` after `bot.get_me()`.
3. (Optional) `register_inbound(dp, "<BOT_USERNAME>", {"ping": ..., ...})`.
4. Add `COORDINATION_GROUP_CHAT_ID: ${COORDINATION_GROUP_CHAT_ID:-}` to the bot's `environment:` block in `docker-compose.yml`.
5. For python-telegram-bot bots (like campaign-bot, tonmnh-bot): use `post_event_via_token(BOT_TOKEN, ...)` instead.

Bot-by-bot wiring is mechanical once the pattern is confirmed working in Phase 1.

## Rollback

If anything goes wrong:
```powershell
# Kill the env var, restart claude-bot — coordination becomes a silent no-op.
# (Edit .env, blank COORDINATION_GROUP_CHAT_ID=)
docker compose restart claude-bot
```

The bot keeps working in DMs exactly as before. No data loss; coordination is purely additive.

## Failure modes & their behavior

| Scenario | Behavior |
|---|---|
| `COORDINATION_GROUP_CHAT_ID` unset | All coord calls are silent no-ops. Bot operates normally. |
| Bot not yet added to group | `post_event` logs warning `Bad Request: chat not found`, returns False. Inbound never triggers. |
| Bot privacy not disabled | Outbound works. Inbound `@bot ping` doesn't reach handler — handler never sees the message. (Fix: BotFather privacy or admin role.) |
| Network blip during post_event | Logs warning, returns False. Push retried on next event. No exception bubbles to bot logic. |
| Aiogram not installed (raw script) | `register_inbound` logs warning + returns silently. `post_event_via_token` works (uses httpx). |

## Files touched in Phase 1

- `shared/coordination.py` — new helper (177 lines)
- `scripts/capture_coordination_chat_id.py` — new (124 lines)
- `shared/group_config.json` — added `coordination` entry
- `tonmnh-bot/data/products.json` — blanked group_link for products 1-3 + `_note`
- `slh-claude-bot/bot.py` — coord wiring (+~50 lines, additive)
- `docker-compose.yml` — `environment:` block on claude-bot service
- `.env.example` — `COORDINATION_GROUP_CHAT_ID` + `SLH_CLAUDE_BOT_USERNAME`
- `ops/COORDINATION_GROUP_SETUP.md` — this doc
