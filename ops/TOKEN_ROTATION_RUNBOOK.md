# SLH Token Rotation — Operations Runbook

Canonical reference for rotating bot tokens and system secrets across the SLH ecosystem. Three surfaces (web admin pages, Telegram bot, curl), one backend pipeline, full audit log.

---

## TL;DR — One-time setup (do this once before first rotation)

```powershell
# 1. Generate a Railway API token (read+write)
#    https://railway.com/account/tokens → New Token → name: "slh-rotation-pipeline"

# 2. Set the token on Railway for the slh-api service:
#    https://railway.com/project/slh-api → Variables → New
#    Key:   RAILWAY_API_TOKEN
#    Value: <paste from step 1>

# 3. Resolve project/service/environment IDs into config/railway_services.json
$env:RAILWAY_API_TOKEN = "<your token>"
cd D:\SLH_ECOSYSTEM
python scripts\railway_resolve_ids.py            # dry-run, prints diff
python scripts\railway_resolve_ids.py --write    # persists IDs

# 4. Commit the resolved IDs
git add config/railway_services.json
git commit -m "config(railway): resolve project/service/environment IDs"
git push

# 5. Verify pipeline is wired in production
curl -H "X-Admin-Key: $env:ADMIN_KEY" https://slh-api-production.up.railway.app/api/admin/rotation-pipeline/health
# Expected: {"config_loaded": true, "config_entries": 31, "railway_token_ok": true, ...}
```

---

## Three rotation surfaces

### 1. Web — `/admin/tokens.html`
- Shows all 31 bots with **tier badge** (🚨/⚠️/🔹/⚪) and **last-rotated** indicator.
- Click `🔄 Rotate` on any row → modal with `new_token` + `swap_mode` checkbox → `🚀 בצע סיבוב`.
- Modal streams progress: validate → push → redeploy → healthcheck → setMyCommands → done.
- Critical-tier bots show 60s confirm prompt before execution.

### 2. Web — `/admin/rotate-token.html`
- Two modes selectable at top:
  - ⚡ **Pipeline** (default) — token POSTed to `/api/admin/rotate-bot-token-pipeline`, full automation.
  - 🛡 **Local** — generates PowerShell command for local execution; token never leaves the browser.
- Step 1: select bot + paste token + validate against Telegram.
- Step 2: pipeline mode shows `🚀 בצע סיבוב מלא` button OR local mode shows `📋 העתק לפקודות`.

### 3. Telegram — `@SLH_Claude_bot` `/admin`
- Inline keyboard: 🔐 Tokens · 🚂 Railway · 📊 Pipeline status · 📜 Audit
- Tap `🔐 Tokens` → paginated bot list (sorted by tier → staleness)
- Tap a bot → detail card → `🔄 סובב טוקן` or `🔁 Swap mode`
- Bot prompts for token in next message → message auto-deleted on receive
- Live progress streamed by editing a single status message
- Critical tier shows 60s `✅ אשר וסובב` button

---

## Tier model — security gates

| Tier | Examples | Confirm | Cooldown | Audit | Broadcast |
|------|----------|---------|----------|-------|-----------|
| 🚨 **critical** | `SLH_CLAUDE_BOT_TOKEN`, `ACADEMIA_BOT_TOKEN`, `ADMIN_API_KEYS`, `DATABASE_URL`, `ANTHROPIC_API_KEY` | 60s confirm window | 15 min | full | all admins |
| ⚠️ **high** | `BOTSHOP`, `WALLET`, `SLH_Spark`, `SLH_Admin`, `TELEGRAM_BOT_TOKEN` (macro) | none | 5 min | full | all admins |
| 🔹 **medium** | most operational bots | none | 1 min | full | none |
| ⚪ **low** | `TEST_BOT_TOKEN`, swap-targets | none | none | basic | none |

Tier is stored in `bot_catalog.tier` and `config/railway_services.json` per env_var. Edit via:
- Web: `/admin/tokens.html` → ✏️ → tier dropdown (planned)
- API: `PATCH /api/admin/bots/{id}` with `{"tier": "critical"}`
- SQL: `UPDATE bot_catalog SET tier = 'critical' WHERE handle = '@SLH_xxx_bot';`

---

## Security model

### What never leaves memory
- The new token transits in HTTPS request body → process memory → Railway GraphQL → discarded.
- **NEVER persisted to DB.** **NEVER logged.** **NEVER returned in any response field.**

### What IS recorded (institutional_audit table)
- `actor_user_id` (admin who triggered)
- `resource_id` (env_var name, e.g. `WALLET_BOT_TOKEN`)
- `before_state.last_rotated_at` (the previous timestamp)
- `after_state.last4` (last 4 chars only)
- `after_state.tg_bot_id` (Telegram numeric ID, NOT the token)
- `after_state.deploy_id` (Railway deploy id)
- `metadata.tier` (critical/high/medium/low)
- `metadata.swap` (whether swap_mode was used)
- `entry_hash` (hash chain — every entry chains to previous; tampering visible)

### Defense in depth
1. **TLS only** — Railway-managed cert + HTTPS enforced
2. **Admin auth** — `_require_admin` checks env keys + DB-rotated keys (hashed+salted)
3. **Critical tier confirm** — 60s `confirm_token` round-trip; one-shot, expires fast
4. **Cooldown** — per-env_var rate limit by tier (in-memory, resets on restart)
5. **Pre-validation** — Telegram `getMe` BEFORE pushing to Railway; bad token never travels further
6. **Post-deploy healthcheck** — `getMe` again 8s after redeploy; alerts admins on failure
7. **Output redaction** — `_redact()` scrubs token-shaped substrings from every error
8. **Response headers** — `Cache-Control: no-store` + `X-Robots-Tag: noindex` on every pipeline response
9. **Bot DM** — token messages auto-deleted after receipt (`bot.delete_message`)
10. **Hash-chained audit** — `institutional_audit.entry_hash` makes silent log edits detectable

---

## Failure modes + recovery

### Validation failure (token rejected by Telegram)
- **System state:** unchanged
- **Audit:** `secret.rotate.failed` with `phase: validate`
- **Recovery:** verify token was copied correctly from BotFather; retry

### Handle mismatch (wrong bot token)
- **System state:** unchanged
- **Audit:** `secret.rotate.failed` with `phase: handle_mismatch`
- **Recovery:** if intentional → set `swap_mode: true`; otherwise pick the right bot

### Railway push failed
- **System state:** unchanged (variable NOT updated)
- **Audit:** `secret.rotate.failed` with `phase: railway_push`
- **HTTP:** 502
- **Recovery:**
  - Check `RAILWAY_API_TOKEN` is set and valid (`/api/admin/rotation-pipeline/health`)
  - Verify config IDs are populated for this env_var (`scripts/railway_resolve_ids.py`)
  - Retry

### Railway redeploy failed (variable already pushed)
- **System state:** **Variable updated** but old deployment still serving traffic
- **Audit:** `secret.rotate.failed` with `phase: railway_redeploy`, note "variable WAS pushed"
- **Broadcast:** `⚠️ סיבוב חלקי` to all admins
- **Recovery:**
  ```powershell
  # Manual redeploy via Railway CLI
  railway redeploy --service <service-name> --yes
  # OR via dashboard: Deployments tab → ⋯ → Redeploy
  ```

### Healthcheck failed (variable + deploy succeeded but bot down)
- **System state:** new variable + new deployment running, but bot not responding to `getMe`
- **Audit:** `secret.rotate.healthcheck_failed`
- **Broadcast:** `🚨 ROTATION HEALTHCHECK נכשל` (loud) to all admins
- **HTTP:** 200 with `{ok: false, phase: "healthcheck_failed"}`
- **Recovery:**
  ```powershell
  # 1. Inspect logs
  railway logs --service <service-name> --tail 100
  # 2. If token genuinely bad → rotate again with a fresh token from BotFather
  # 3. If the bot is just slow → wait 30s + check getMe manually:
  curl https://api.telegram.org/bot<NEW_TOKEN>/getMe
  # 4. Worst case → revert via Railway dashboard → Deployments → previous → Redeploy
  ```

### setMyCommands failed (cosmetic only)
- **System state:** rotation succeeded; just the menu didn't sync
- **Audit:** `secret.rotate.pushed` succeeded; warning logged but no failure entry
- **Recovery:** non-blocking; runs again on next rotation. Manual fix:
  ```powershell
  curl -X POST "https://api.telegram.org/bot<TOKEN>/setMyCommands" \
    -H "Content-Type: application/json" \
    -d '{"commands":[{"command":"start","description":"התחל"}]}'
  ```

---

## Rotation order — recommended sweep through the fleet

Run rotations bottom-up (low risk first). Audit log will track everything.

1. **Low tier first** (`TEST_BOT_TOKEN`, swap-targets) — validate the pipeline works in your real environment
2. **Medium tier** (most operational bots) — biggest batch, ~22 rotations
3. **High tier** (Wallet, BotShop, Spark, Admin, macro) — money-touching bots, broadcast to admins
4. **Critical tier last** — `SLH_CLAUDE_BOT_TOKEN`, `ACADEMIA_BOT_TOKEN`. Expect 60s confirm prompt.

For non-bot secrets (`ADMIN_API_KEYS`, `DATABASE_URL`, etc.), pass `skip_healthcheck=true` since `getMe` doesn't apply.

---

## Quick reference — endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/api/admin/rotate-bot-token-pipeline` | Atomic rotation pipeline |
| `GET`  | `/api/admin/rotation-history?limit=50&env_var=…&action=…` | Audit log query |
| `GET`  | `/api/admin/rotation-pipeline/health` | Self-check (config + Railway token) |
| `GET`  | `/api/admin/bots` | Catalog list (with tier) |
| `GET`  | `/api/admin/bots/stats` | Aggregate counts including by-tier |
| `POST` | `/api/admin/bots/{id}/mark-rotated` | Manual mark (legacy) |

All gated by `X-Admin-Key`.

---

## Files involved

| Path | Role |
|------|------|
| [config/railway_services.json](../config/railway_services.json) | env_var → Railway destination + tier mapping |
| [config/bot_commands.json](../config/bot_commands.json) | `setMyCommands` registry (default + per-bot) |
| [routes/railway_client.py](../routes/railway_client.py) | GraphQL client (variableUpsert, deploymentRedeploy) |
| [routes/rotation_pipeline.py](../routes/rotation_pipeline.py) | Pipeline endpoint + history |
| [api/admin_bots_catalog.py](../api/admin_bots_catalog.py) | bot_catalog table + CRUD (with tier column) |
| [website/admin/tokens.html](../website/admin/tokens.html) | Catalog dashboard with inline rotate modal |
| [website/admin/rotate-token.html](../website/admin/rotate-token.html) | Dedicated rotation page (Pipeline / Local modes) |
| [website/admin/rotation-history.html](../website/admin/rotation-history.html) | Audit-log viewer |
| [slh-claude-bot/rotation_panel.py](../slh-claude-bot/rotation_panel.py) | Telegram inline-keyboard panel |
| [scripts/railway_resolve_ids.py](../scripts/railway_resolve_ids.py) | Bootstrap: populate Railway IDs from CLI scope |

---

## Audit chain verification (paranoid mode)

Each `institutional_audit` row carries `entry_hash` linked to the previous row's hash. To verify the chain hasn't been tampered with:

```sql
-- Count entries per action
SELECT action, COUNT(*) FROM institutional_audit
WHERE action LIKE 'secret.rotate.%' GROUP BY action ORDER BY 2 DESC;

-- Pull last 10 rotations
SELECT id, action, resource_id, after_state->>'last4' AS last4, created_at
FROM institutional_audit
WHERE action LIKE 'secret.rotate.%'
ORDER BY id DESC LIMIT 10;
```

For full hash-chain re-verification, run `python scripts/audit_data_integrity.py` (existing tool).
