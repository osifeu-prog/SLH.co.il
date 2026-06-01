# Coordination Wiring — Phase 2C Plan

**Status:** Phase 1 + 2A + 2B done. **13 of 24 bots wired** to `shared.coordination`.

**Remaining: 11 bots** that need per-bot analysis (each has a quirk that broke
the simple "drop in `init_coordination_for_bot()` before `start_polling`" pattern
used in Phase 1/2A/2B).

This doc enumerates each remaining bot, the specific quirk, and the exact
change needed. A future session can execute mechanically without re-discovery.

---

## Already wired (13)

| # | Bot | File | Phase | Commit |
|---|---|---|---|---|
| 1 | claude-bot | `slh-claude-bot/bot.py` | Phase 1 | `478f6e6` |
| 2-9 | slh-ton, ledger, chance, ts-set, crazy-panel, nft-shop, beynonibank, test-bot | `shared/bot_template.py` (single edit) | Phase 2A | `e7a9d95` |
| 10 | admin-bot | `admin-bot/main.py:1009` | Phase 2B-1 | `c5aa00c` |
| 11 | game-bot | `match-bot/main.py:632` | Phase 2B-1 | `c5aa00c` |
| 12 | nfty-bot | `nfty-bot/main.py:1428` | Phase 2B-2 | `487a297` |
| 13 | nifti-bot | `wellness-bot/main.py:204` | Phase 2B-2 | `487a297` |

## Standard pattern (re-use for any aiogram3 + async main + shared/ accessible bot)

```python
async def main():
    ...existing setup...

    # Coordination: register inbound + post ready (no-op if env unset)
    try:
        from shared.coordination import init_coordination_for_bot
        me = await bot.get_me()
        await init_coordination_for_bot(
            bot, dp,
            name="<bot-key>",
            username=me.username,
        )
    except Exception as e:
        log.warning("coordination init failed: %s", e)

    await dp.start_polling(bot, ...)
```

---

## Remaining 11 bots — per-bot plan

### Tier A — aiogram3 but quirky build/startup (4)

#### 1. airdrop-bot

- **Entry:** `airdrop/app/bot_server.py:~2356`
- **Quirk:** non-async `main()` called via subprocess; uses `bot_server.py -c "import …"` pattern.
- **Plan:** Find the actual async polling-start point (search for `dp.start_polling` or `application.run_polling`). Insert standard pattern there. If no async main, wrap the existing sync main in an async wrapper and add coord wiring.
- **Risk:** Medium — the subprocess pattern suggests existing wrapper logic that may need careful handling.

#### 2. osif-shop-bot

- **Entry:** `osif-shop/main.py:640`
- **Quirk:** Dockerfile.osifshop CMD runs `webapp_server.py & main.py` — two processes, polling in main.py.
- **Plan:** Apply standard pattern in `osif-shop/main.py:main()` before `start_polling`. The webapp side is unaffected.
- **Risk:** Low — the dual-process is just a launch ordering; coord wiring is in the polling process only.

#### 3. fun-bot

- **Entry:** `fun/app.py:585`
- **Quirk:** uvicorn + aiogram polling hybrid. FastAPI startup event launches polling via `asyncio.create_task()`.
- **Plan:** Find the FastAPI startup-event handler (likely `@app.on_event("startup")`). Add standard pattern inside it, BEFORE the `create_task(dp.start_polling(...))` call.
- **Risk:** Medium — ensure `bot.get_me()` works inside FastAPI's lifespan context.

#### 4. botshop (Tier 3 — uses python-telegram-bot)

- **Entry:** `botshop/app/main.py:27`
- **Quirk:** PTB + uvicorn hybrid. FastAPI startup event triggers `updater.start_polling()`.
- **Library:** `python-telegram-bot` (NOT aiogram).
- **Plan:** Use `post_event_via_token(token, "botshop", "ready", "...")` from `shared.coordination`. For inbound, PTB requires its own handler registration — add a custom `MessageHandler` with a `Filters.chat(coord_chat_id)` filter that parses `@botshop_username <cmd>`. Inbound is more work in PTB; outbound is simple.
- **Risk:** Medium — PTB API differs from aiogram, register_inbound() in shared.coordination is aiogram-only.

---

### Tier B — sub-dir build context, shared/ may not be reachable (3)

#### 5. wallet-bot

- **Entry:** `wallet/app/main.py:36`
- **Quirk 1:** Embedded `wallet/shared/` directory shadows root `shared/` via PYTHONPATH ordering.
- **Quirk 2:** Library is python-telegram-bot.
- **Plan:**
  1. Either delete `wallet/shared/coordination.py` (none exists — but the dir has bot_template.py copy that's stale) or update Dockerfile.wallet to mount root `shared/` after wallet's own.
  2. Use `post_event_via_token` (PTB).
- **Risk:** High — needs Dockerfile change AND careful PYTHONPATH ordering.

#### 6. academia-bot

- **Entry:** `academia-bot/bot.py:1025`
- **Quirk:** Build context is `./academia-bot` only — root `shared/` is not in build context.
- **Plan:** Update `academia-bot/Dockerfile`:
  ```dockerfile
  COPY ../shared /app/shared
  ENV PYTHONPATH=/app:/app/shared
  ```
  Or change docker-compose to use `context: .` and point dockerfile to `academia-bot/Dockerfile`. Then apply standard pattern.
- **Risk:** Low — Dockerfile change is clean; aiogram pattern is straightforward after that.

#### 7. wellness-bot — DONE (counted as nifti-bot in Phase 2B-2)

---

### Tier C — python-telegram-bot, no PYTHONPATH (2)

#### 8. campaign-bot

- **Entry:** `campaign-bot/main.py:243`
- **Library:** python-telegram-bot 21.4
- **Quirk:** No PYTHONPATH set; PTB-specific `app.run_polling()`.
- **Plan:**
  1. Update Dockerfile.campaign to include root `shared/` and set PYTHONPATH.
  2. Use `post_event_via_token(BOT_TOKEN, "campaign-bot", "ready", "...")` from inside an async helper (PTB has `application.bot.send_message` async, but can also fire-and-forget via httpx).
  3. For inbound — register a PTB `MessageHandler(Filters.chat(coord_chat_id), handler)` that parses `@campaign_bot <cmd>`.
- **Risk:** Medium — PTB-specific.

#### 9. tonmnh-bot

- **Entry:** `tonmnh-bot/src/main.py:173`
- **Library:** python-telegram-bot 21.4
- **Quirk:** PYTHONPATH=/app only, no /app/shared.
- **Plan:** Same as campaign-bot — Dockerfile update + `post_event_via_token` + PTB MessageHandler.
- **Risk:** Medium.

---

### Tier D — out-of-tree builds (2)

#### 10. core-bot

- **Build context:** `../SLH_PROJECT_V2`
- **Entry:** `../SLH_PROJECT_V2/bot/worker.py` (per Explore — needs verification on disk)
- **Quirk:** Out-of-tree. Root `shared/` is not in this build context. Even bind-mounting via docker-compose volumes only gets us shared/ at runtime, not build time.
- **Plan:**
  1. Symlink or copy `shared/` into `SLH_PROJECT_V2/` before build, OR
  2. Change Dockerfile.core to use `context: .` (root) and explicit `COPY ../SLH_PROJECT_V2/...` paths, OR
  3. Use a docker-compose volume mount `- ./shared:/app/shared` and add `/app` to PYTHONPATH.
- **Risk:** High — out-of-tree ergonomics, non-standard layout.

#### 11. guardian-bot

- **Build context:** `../telegram-guardian-DOCKER-COMPOSE-ENTERPRISE`
- **Entry:** `../telegram-guardian-DOCKER-COMPOSE-ENTERPRISE/bot/main.py` (needs verification)
- **Plan:** Same options as core-bot — symlink, change context, or mount volume.
- **Risk:** High — same as core-bot.

---

### Skipped intentionally (1)

#### factory-bot

- **Quirk:** `DISABLE_TELEGRAM: "1"` in docker-compose.yml — bot does not connect to Telegram in production.
- **Decision:** Do NOT wire. The bot has no Telegram surface to coordinate from. If it ever re-enables Telegram, revisit.

---

## Execution order recommendation

When activating Phase 2C, sequence by risk:

1. **academia-bot, osif-shop-bot** (Tier A/B, low risk, big leverage — 2 bots)
2. **fun-bot, airdrop-bot** (Tier A, medium risk, async — 2 bots)
3. **campaign-bot, tonmnh-bot** (Tier C, PTB pattern shared — 2 bots, both follow same template once first is done)
4. **botshop, wallet-bot** (Tier A/B, PTB hybrids — 2 bots)
5. **core-bot, guardian-bot** (Tier D, out-of-tree — 2 bots, biggest infra change)

Total: 5 commits across 10 bots = full wiring of all non-disabled bots in the ecosystem.

---

## How to verify any wired bot post-wiring

After setting `COORDINATION_GROUP_CHAT_ID` and restarting the bot:

```powershell
docker compose restart <bot-service>
docker logs slh-<bot> --tail 20 | Select-String "coordination|register_inbound|ready"
```

Expected lines:
```
shared.coordination loaded; enabled=True
register_inbound: <bot_username> wired with N handler(s): ...
```

In the coordination group:
- `[OK] [<bot-name>] @<username> polling started`  (outbound startup post)
- `@<username> ping` → `pong`  (inbound test)
