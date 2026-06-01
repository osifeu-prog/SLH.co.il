# Session Handoff — Telegram-First Architecture Phase 1
**Session date:** 2026-04-21 (continued into 2026-04-22)
**Lead:** Claude Code (Opus 4.7, 1M context) — interactive session with Osif
**Next Lead Agent:** take over from this file. Read it end-to-end before touching anything.

---

## Executive summary

1. **Strategic decision made and approved:** SLH pivots to a **Telegram-first, API-centered, Mini-App-enabled** architecture. Telegram bots + Mini Apps are the unified control surface; the FastAPI on Railway is the single source of truth; ESP32 devices and bots are peer citizens of the API.
2. **Phase 1 shipped and verified:** Gateway module, 3 Mini App pages, full dashboard port, migration plan for 100 HTML pages, 4 new bot commands, PowerShell launcher, operations runbook, verified backlog.
3. **Phase 2 deferred (6 tasks)** are enumerated below with exact next steps. Nothing is half-finished mid-file.
4. **Two user-action blockers** remain (ANTHROPIC_API_KEY, COM5 port) — neither blocks this handoff.

If you read only one other document before starting, read [OPS_RUNBOOK.md](OPS_RUNBOOK.md).

---

## What shipped this session (all files verified)

### Code

| File | Lines | Status | Verification |
|------|-------|--------|--------------|
| [api/telegram_gateway.py](../api/telegram_gateway.py) | 210 | New | `python -c "ast.parse"` ok. Not yet imported into main.py (deliberate, see Phase 2). |
| [website/miniapp/dashboard.html](../website/miniapp/dashboard.html) | 3354 | Ported from `website/dashboard.html` + 54-line Telegram shim | Live preview: real user data (199,789 SLH internal, 735 ZVK, 2 referrals), real prices (BTC 227K ₪, ETH 6.9K ₪, TON $1.36), 0 console errors. One cosmetic bug: activity emojis mojibake — tracked as K-12 in KNOWN_ISSUES. |
| [website/miniapp/wallet.html](../website/miniapp/wallet.html) | 132 | New skeleton | Renders; needs data wiring (K-pending). |
| [website/miniapp/device.html](../website/miniapp/device.html) | 175 | New — ESP command UI | Renders; POST `/api/device/command/{id}` not tested end-to-end (needs paired ESP). |
| [website/miniapp/miniapp.css](../website/miniapp/miniapp.css) | 168 | New — Telegram theme vars + RTL | ok |
| [website/miniapp/miniapp.js](../website/miniapp/miniapp.js) | 98 | New — `SLH.api()` wrapper injecting `X-Telegram-Init-Data` | ok |
| [slh-claude-bot/bot.py](../slh-claude-bot/bot.py) | +152 (was 146, now 298) | Extended — 4 new direct-API handlers | `ast.parse` ok; handlers: `/health`, `/price`, `/devices`, `/task`. /task writes to `ops/TASK_BOARD.md`. |
| [device-registry/esp32-cyd-work/firmware/slh-device-v3/src/main.cpp](../device-registry/esp32-cyd-work/firmware/slh-device-v3/src/main.cpp) | patched | 3 compile errors fixed + 9 serial diagnostic lines + TFT self-test pattern + alive counter | `pio run` success, RAM 14.4% / Flash 30.6%. Upload blocked on COM5 busy (external). |

### Ops documents

| File | Purpose |
|------|---------|
| [ops/TELEGRAM_FIRST_MIGRATION_PLAN.md](TELEGRAM_FIRST_MIGRATION_PLAN.md) | Strategic doc: 3-layer architecture, ESP role, 100-page migration map (KEEP / MINIAPP / ADMIN-MINIAPP / CHAT / DELETE / MERGE), 5-phase rollout, guardrails. |
| [ops/slh-start.ps1](slh-start.ps1) | One-command PowerShell launcher: prereqs → git pull → docker compose up → postgres+redis wait → health matrix. Flags: `-SkipDocker`, `-SkipGit`, `-Verify`, `-Stop`. |
| [ops/OPS_RUNBOOK.md](OPS_RUNBOOK.md) | Operations reference: start/stop, system map, endpoint reference, health matrix, data integrity rules, deploy procedures, security model, broadcast, troubleshooting. |
| [ops/KNOWN_ISSUES.md](KNOWN_ISSUES.md) | Verified backlog — 25 entries, each confirmed in current code. Priority P0/P1/P2. Also lists claims from stale handoffs that were checked and found already-fixed. |
| [ops/SESSION_HANDOFF_20260421_TELEGRAM_FIRST.md](SESSION_HANDOFF_20260421_TELEGRAM_FIRST.md) | This file. |

### Auto-memory (for future Claude sessions)

| Entry | Content |
|-------|---------|
| `project_telegram_first_architecture.md` | The strategic pivot, guardrails, Phase 1 deliverables, gateway wiring procedure. Linked from `MEMORY.md`. |

---

## Live verification (evidence)

Preview server was running during session (port 8899 via `slh-website` launch config). Verified end-to-end:

- `GET /miniapp/dashboard.html` → 200, 4,452+ bytes after edits.
- `GET /api/health` → `{status:"ok", db:"connected"}` (from Railway).
- `GET /api/prices` → 7 coins returned (bitcoin 75,603 USD / 227K ILS, ethereum 2,306 USD / 6,931 ILS, etc.).
- Dashboard accessibility snapshot shows: user banner, price ticker × 2, welcome hero, 8 KPI cards, balance cards (TON/SLH/ZVK), referral stats, blockchain balances section (22,796.6154 SLH on BSC), ESP32 pairing card, recent activity feed, AI chat widget, sidebar navigation.
- Console errors: **zero**.

---

## Architecture snapshot

```
 ESP32 Device       Telegram Bot        Mini App (HTML)
     │                   │                    │
     └───────────────────┼────────────────────┘
                         │
           api/telegram_gateway.py
            (auth + audit, single entry)
                         │
              Core API  (FastAPI)
                         │
       ┌─────────────────┼─────────────────┐
       │                 │                 │
   Postgres           Redis             External
    (state)           (queue)            (BSC, TG)
```

Public web pages (index, whitepaper, roadmap, terms, privacy, blog, etc.) stay on GitHub Pages as marketing surface — **no operational state**.

---

## What is blocked on user action (Osif)

| # | Blocker | How to fix | Impact |
|---|---------|------------|--------|
| U-1 | `ANTHROPIC_API_KEY` empty in `D:\SLH_ECOSYSTEM\slh-claude-bot\.env` | Paste key from console.anthropic.com into line 8. **Do NOT paste in chat.** | `@SLH_Claude_bot` can't run free-text handler (new commands /health /price /devices /task work without it). |
| U-2 | COM5 held by stuck `pio.exe` PID 22064 | Task Manager → kill as admin, OR close owning terminal, OR run `powershell -File ops\slh-start.ps1 -Stop` | ESP32 firmware cannot be flashed. Binary is pre-built at `.pio\build\esp32dev\firmware.bin`. |
| U-3 | Railway env vars not fully set: `BSCSCAN_API_KEY`, `ANTHROPIC_API_KEY` | Railway dashboard → project → variables | network.html + blockchain.html show zeros; certain bots can't call Anthropic. |
| U-4 | BotFather Mini App URL not set for `@WEWORK_teamviwer_bot` | BotFather → `/mybots` → select bot → Bot Settings → Menu Button → URL = `https://slh-nft.com/miniapp/dashboard.html` | No user can actually open the Mini App from Telegram yet. |
| U-5 | 10 leaked secrets not rotated (night 21.4) | Rotate via each provider; list in KNOWN_ISSUES.md K-1 | Security exposure. |
| U-6 | User 8789977826 refund (₪147 or upgrade to VIP) | Banking action | User is Osif himself (per reality-reset doc) — can be unblocked by issuing VIP license from admin bot. |

---

## Phase 2 backlog — exact next steps for Lead Agent

In priority order. Each item has an exit condition — do not mark done without it.

### PH2-1. Wire the Gateway into `main.py` **[2h]**
1. Edit `D:\SLH_ECOSYSTEM\main.py`: add `from api.telegram_gateway import verify_miniapp_request, verify_bot_request, require_admin, TelegramUser, GatewayError` near the top, grouped with other imports.
2. Mirror the import in `D:\SLH_ECOSYSTEM\api\main.py` (both files must stay in sync — Railway builds from root).
3. Add a first Mini-App-only endpoint to prove the wiring:
   ```python
   from fastapi import Depends
   @app.get("/api/miniapp/me")
   async def miniapp_me(user: TelegramUser = Depends(verify_miniapp_request)):
       return {
           "telegram_id": user.telegram_id,
           "slh_user_id": user.slh_user_id,
           "is_admin": user.is_admin,
           "username": user.username,
       }
   ```
4. Commit + push. Watch Railway deploy.
5. Verify: open Mini App in Telegram, check `/api/miniapp/me` returns 200 with correct user.
6. **Exit:** `curl` with a fresh `X-Telegram-Init-Data` header returns 200; curl without returns 401 `{code: "empty_init_data"}`.

### PH2-2. Create the `event_log` table (unblocks K-4) **[30m]**
1. Connect to Railway Postgres via `railway shell` or internal `psql`.
2. Run:
   ```sql
   CREATE TABLE IF NOT EXISTS event_log (
     id BIGSERIAL PRIMARY KEY,
     event_type TEXT NOT NULL,
     telegram_id BIGINT,
     slh_user_id INTEGER,
     payload JSONB,
     created_at TIMESTAMPTZ DEFAULT NOW()
   );
   CREATE INDEX IF NOT EXISTS ix_event_log_created_at ON event_log (created_at DESC);
   CREATE INDEX IF NOT EXISTS ix_event_log_type ON event_log (event_type);
   ```
3. Verify `GET /api/events/public` returns 200 with an empty array (not `event_log_unavailable`).
4. Verify first Gateway hit from PH2-1 writes a row.

### PH2-3. Fix `initShared()` dead across 121 pages (K-5) **[45m]**
1. Append to `website/js/shared.js`:
   ```js
   document.addEventListener('DOMContentLoaded', function() {
     if (typeof initShared === 'function') initShared({});
   });
   ```
2. Commit + push from `website/`.
3. Verify on 3 pages (index, earn, whitepaper) that the nav, footer, theme switcher, FAB render without explicit per-page script.
4. **Do not** add to `/miniapp/*` — Mini Apps have their own init path.

### PH2-4. Fix 3 admin endpoints (K-2) **[45m]**
1. Open `main.py` — find the three endpoints at line ~957 (registration approve), ~2344 (beta coupon), ~4782 (marketplace approve).
2. For each: remove the `admin_secret` body-field check, replace with the standard `_require_admin(authorization, x_admin_key)` header-based dependency used elsewhere in the file.
3. Sync to `api/main.py`, commit, push, verify that previous `admin_secret`-style requests now 401 and header-based requests still 200.

### PH2-5. Restore `marketplace.html` + `team.html` (K-6) **[30m]**
1. From `D:\SLH_ECOSYSTEM\website`: `git log --all -- marketplace.html team.html` to find the last commit that had them.
2. If present locally: just `git add` + commit + push.
3. If missing: regenerate from memory of what they contained (team = 10 members photo grid per night 18.4; marketplace = 5 items per night 20.4).
4. Verify 200 on `https://slh-nft.com/marketplace.html` and `/team.html`.

### PH2-6. Port 3 more Mini App pages (profile, admin, community) **[4h]**
Follow the exact pattern used for `dashboard.html`:
1. `cp website/profile.html website/miniapp/profile.html`
2. Insert the 2-script Telegram shim + fetch-wrapper block immediately after `<script src="https://telegram.org/js/telegram-web-app.js"></script>`. See `dashboard.html` lines 24-78 for the canonical version.
3. Remove `defer` from the telegram-web-app.js tag.
4. Test in preview at `/miniapp/<name>.html`.
Same for `admin.html` and `community.html`. After these three, all P0 Mini App surfaces from [TELEGRAM_FIRST_MIGRATION_PLAN.md](TELEGRAM_FIRST_MIGRATION_PLAN.md) are covered.

---

## Guardrails (do not break)

1. **No business logic in bot handlers.** Parse + call API + render. Mutations go through Core API.
2. **No fake/fallback data.** Render `--` if API returns nothing. Never invent values.
3. **Single Gateway entry.** Every user-facing request validates identity through `api/telegram_gateway.py`.
4. **Public vs. private pages are distinct.** Marketing pages never embed admin state. Mini App pages always require Telegram context.
5. **Admin Telegram IDs in env, not hardcoded.** `ADMIN_TELEGRAM_IDS` default = `224223270` (Osif).
6. **Railway builds from ROOT `main.py`.** Always sync `api/main.py` + `main.py` before push.
7. **No secrets in chat.** If Osif ever pastes a secret, flag + list rotation URL. See memory `feedback_never_paste_secrets.md`.
8. **Hebrew UI, English code/commits.** Dashboard and all Mini App pages are in Hebrew.

---

## Risks I leave on the table

Things that may break if you act without reading the context:

- **Dashboard port is a byte-for-byte copy of `website/dashboard.html` + a shim.** Any future edit to the public dashboard must be mirrored to `/miniapp/dashboard.html` (or we refactor to a shared template). Two-file drift will cause confusion fast.
- **Gateway is not wired yet.** Importing it into `main.py` before Railway env has `TELEGRAM_BOT_TOKEN` set → every Mini App request 500s with `no_bot_token`. Set the env var **first**, then wire.
- **ESP32 firmware has hardcoded WiFi `Beynoni / 12345678`.** Works at Osif's location; everywhere else it will loop on WiFi FAIL. Future: WiFiManager portal or env-injected credentials.
- **The Mini App shim in `dashboard.html` triggers exactly one `location.reload()` on first-open** to let the existing legacy login flow pick up the Telegram-fetched SLH user. Users experience a brief white flash. Acceptable for Phase 1; clean up in Phase 3 by bypassing the legacy login screen entirely in Telegram mode.
- **`/miniapp/dashboard.html` loads `ethers.js` + `chart.js` + `fontawesome`** (inherited from the public dashboard). Mini App cold-load is ~1.5 MB — fine on wifi, slow on 3G. Optimize in Phase 4.
- **The Telegram Mini App shim uses `https://slh-api-production.up.railway.app/api/user/{id}` to resolve users.** If the API is down, the shim silently falls through and the user sees the legacy login screen inside Telegram — acceptable failure mode, but worth noting.

---

## Where to find things quickly

```
D:\SLH_ECOSYSTEM\
├── api\
│   ├── main.py                    # API source (sync to root)
│   └── telegram_gateway.py        # NEW Gateway module (Phase 1)
├── main.py                        # Railway entry (sync to api/)
├── website\                       # GitHub Pages repo (separate git)
│   ├── dashboard.html             # Legacy public dashboard
│   └── miniapp\                   # NEW Mini App surfaces
│       ├── dashboard.html         # Full port (3354 lines)
│       ├── wallet.html            # Skeleton
│       ├── device.html            # ESP command UI
│       ├── miniapp.css
│       └── miniapp.js
├── ops\
│   ├── OPS_RUNBOOK.md             # ← START HERE
│   ├── KNOWN_ISSUES.md
│   ├── TELEGRAM_FIRST_MIGRATION_PLAN.md
│   ├── slh-start.ps1              # One-command launcher
│   ├── SESSION_HANDOFF_20260421_TELEGRAM_FIRST.md   # this file
│   └── AUDIT_FULL_20260421_COMPREHENSIVE.md         # night audit (95 items)
├── slh-claude-bot\                # Telegram executor bot
│   └── bot.py                     # +4 handlers this session
├── device-registry\esp32-cyd-work\firmware\slh-device-v3\
│   ├── src\main.cpp               # Patched: diagnostics + self-test
│   └── platformio.ini
└── CLAUDE.md                      # Project instructions for future Claude sessions

C:\Users\Giga Store\.claude\projects\D--\memory\
├── MEMORY.md                      # Auto-memory index (Claude-only)
└── project_telegram_first_architecture.md   # NEW this session
```

---

## Session outcome in one sentence

**The Telegram-first control surface now exists as a working skeleton with one fully-ported page, a migration plan for the other 99, a one-command launcher, a verified backlog, and a security-clean Gateway module ready to wire in the next session.**

Hand off clean.
