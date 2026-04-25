# Continuation Prompt — SLH Stabilization Session

**כיצד להשתמש במסמך הזה:**
פתח שיחה חדשה (Claude / GPT / Cursor / סוכן אחר), הדבק את כל התוכן של הקובץ הזה כהודעה ראשונה. הסוכן יקבל את כל ההקשר הדרוש ויתחיל לעבוד על המשימות הלא-פתורות. גרסה זו מכוונת לסוכן שעובד על `D:\SLH.co.il\`. לסוכן אחר (SLH_ECOSYSTEM / AISITE / bots) — התאם את חלק הגבולות.

---

# PROMPT START — PASTE EVERYTHING BELOW INTO NEW CONVERSATION

## Context — who I am, what this is

I'm **Osif Kaufman Ungar** (osif.erez.ungar@gmail.com), solo developer running the SLH ecosystem — 25+ Telegram bots, blockchain token (SLH on BSC), ESP32 hardware devices, website `slh-nft.com`, and several sibling projects.

`D:\SLH.co.il\` is one specific project in this ecosystem:
- Telegram bot `@SLH_macro_bot`
- Static site `www.slh.co.il`
- Brand-new Guardian **pre-order** page at `www.slh.co.il/guardian.html` — flagship ESP hardware device, ₪888 × 99 units early bird, then ₪1,299, official launch **2026-11-07**

**Your mission:** continue stabilizing the system. "Stable" means everything works, everything is documented, everything is easy to operate. Zero false positives — verify empirically, report honestly.

## ⛔ READ THIS BEFORE ANY CODE EDIT — `CLAUDE.md` is binding

The repo has `CLAUDE.md` at root + `docs/SIG_STATISTICAL_DEFENSE.md`. These are **hard rules** for any AI agent (Claude / GPT / Cursor / autonomous):

1. **No APY/ROI without the full wrapper** — every yield % must carry: word "Target", `SIG=X · σ=0.0049%` badge, `Forward-looking projection, not guaranteed` disclaimer, link to `/SIG_STATISTICAL_DEFENSE.md`. Plain `"65% APY"` = breaking change, **refuse**.
2. **No token sales to retail** — `"Buy SLH for ₪Y"` / `"token sale"` / `"mint and distribute"` flows are forbidden. Mining-reward / bundled-utility-credits / earned-via-activity are OK. The 2 SLH on Guardian is utility-mining over 90 days, NOT a sale — frame it that way.
3. **No secrets in code** — `.githooks/pre-commit` blocks 8 secret patterns. Don't bypass with `--no-verify`.
4. **Verify prod schema before any SQL** — prod has `first_seen` TEXT (not `registered_at`), `feedback.timestamp` TEXT (not `created_at`), `feedback.user_id` TEXT (not BIGINT). Run `railway run python -c "..."` against `information_schema.columns` before assuming.

If a user asks for something that conflicts with these rules — **stop and ask Osif**. Do not commit a workaround.

Legal context: Israeli Securities Law 1968 + Howey Test (US). Anything that looks like "promise of return for retail" without proper structure is criminal exposure. The SIG methodology + Mining framing reduces this risk; consult `docs/SIG_STATISTICAL_DEFENSE.md` for the canonical methodology.

## Previous session summary

Previous session was Claude Opus 4.7 on 2026-04-24/25, ~10 hours of work, 13 commits. Shipped:
- Guardian landing page + bot `/preorder` flow + `preorders` DB table
- 2 SLH mining reward (utility, not sale) + `device_mining` table + Target 65% APY with full SIG wrapper
- `CLAUDE.md` + `SIG_STATISTICAL_DEFENSE.md` (binding agent rules)
- Fixed SQL schema divergence (prod had `first_seen`/`timestamp` TEXT, code expected `registered_at`/`created_at`)
- Fixed Markdown eating underscores in bot commands (wrapped in backticks)
- Fixed website 502 caused by removing healthcheck (added static fallback in bot.py)
- Purged leaked bot token from `docs/neural/index.html`
- Added `.gitignore`, `.env.example`, `.githooks/pre-commit` (blocks secrets automatically)
- Created ops/ folder with 7 files: `runbook.md`, `verify.ps1`, `rotate-token.md`, `POST_MORTEM_20260424.md`, `daily_digest.py`, `CONTROL_CENTER_DESIGN.md`, `DISPATCH_20260425.md`
- Added `/health` + `/stats` bot commands + SEO/OG tags on Guardian page

Latest commit at handoff: `a9a0fbe` (Control Center design spec).

## Current verified state (as of handoff)

| Surface | Status | Notes |
|---------|--------|-------|
| `www.slh.co.il/` | ✅ UP (HTTP 200) | |
| `www.slh.co.il/guardian.html` | ✅ UP (HTTP 200) | SEO complete, image placeholders |
| `@SLH_macro_bot` (getUpdates polling) | ❌ **DOWN** — 401 Unauthorized | Token was rotated by Osif but Railway env still has old value |
| Postgres DB | ✅ UP | 2 users, 0 preorders, 5 feedback, 3 ROI |
| Railway services (4) | ✅ all clean | Postgres · Redis · monitor.slh · SLH.co.il (slh-bot was deleted to fix 409 conflicts) |
| Github repo | ✅ synced with main | |

## Scope boundaries (respect these strictly)

- **You can:** read + write anywhere in `D:\SLH.co.il\`
- **You can:** read + write in `C:\Users\Giga Store\.claude\projects\D--\memory\` (your own memory)
- **You cannot:** write anywhere in `D:\SLH_ECOSYSTEM\`, `D:\AISITE\`, or other sibling projects unless I explicitly authorize **per task**
- **You cannot:** rotate tokens, delete Railway services, or touch BotFather autonomously — those are my manual actions
- **Read via memory (OK):** general context about sibling projects via `MEMORY.md`

## Pending work — in priority order

### P0 — Get bot back online (blocked on me)
I need to update `TELEGRAM_BOT_TOKEN` in Railway Project Settings → Shared Variables. The current value returns 401. Until I do this, `/preorder`, `/health`, `/stats`, and all bot commands are dead. When I tell you "token updated", run `pwsh ops/verify.ps1` end-to-end and confirm.

### P1 — Enable automated Guardian preorders (blocked on 5 answers from me)
Do not start until I answer:
1. **Stock on hand:** how many physical Guardian units exist right now?
2. **Payment method:** TON via @wallet / bank transfer / PayPal?
3. **Shipping:** I ship from home? courier? customer pays shipping separately?
4. **Value proposition:** 2-sentence description of what the device DOES for the customer (goes in hero copy)
5. **Legal status:** עוסק מורשה or פטור? do I need to issue invoices for each sale?

Once I answer, build the order → payment → fulfillment flow in `bot.py` + add admin endpoints.

### P2 — Guardian product photos (blocked on me)
I need to drop these files in `docs/assets/`:
- `guardian-1.jpg`, `guardian-2.jpg`, `guardian-3.jpg` — physical device photos, 800×600 each
- `guardian-demo.mp4` — short video under 5MB
- `guardian-og.png` — 1200×630 for WhatsApp/Telegram link preview (critical)

Paths already referenced in `guardian.html`; no code change needed once files exist.

### P3 — Control Center MVP Phase 1 (blocked on authorization)
Full spec: `ops/CONTROL_CENTER_DESIGN.md` (~350 lines, 12 sections, 27h total roadmap).
For Phase 1 (CLI, 2-3h) I need to authorize you to read + write in `D:\SLH_ECOSYSTEM\ops\` (and possibly `api/telegram_gateway.py` + `website/js/shared.js`). Start only after I confirm:
- "authorized for SLH_ECOSYSTEM read/write, Option A (CLI) for Phase 1"

### P4 — Things you can do solo (no blockers)
- Add `/cancel_preorder <id>` bot flow for users who change mind
- Add `/preorder_details <id>` admin command
- Add CSV export endpoint for preorders
- Wire OpenAI `feedback_ai` integration (key is already in Railway env)
- Improve landing page SEO further (keywords, alt text on images, internal linking)
- Harden `ops/verify.ps1` (add Postgres row-count sanity, deploy freshness check)

## Tools you have

- **Git** — `git` CLI. Commit attribution pattern: `GIT_AUTHOR_NAME="Osif Kaufman Ungar" GIT_AUTHOR_EMAIL="osif.erez.ungar@gmail.com" GIT_COMMITTER_NAME="Osif Kaufman Ungar" GIT_COMMITTER_EMAIL="osif.erez.ungar@gmail.com" git commit -m "..."` — local config is placeholder, env-var override is how I want commits attributed
- **Railway CLI** — `railway` linked to `diligent-radiance` (project id `97070988-27f9-4e0f-b76c-a75b5a7c9673`). Run scripts with prod env via `railway run python <file>`
- **Pre-commit hook** — `.githooks/pre-commit` activates on `git config core.hooksPath .githooks`. Blocks Telegram tokens, OpenAI keys, postgres URLs with passwords, ETH private keys, GitHub PATs. Already installed this repo.
- **Preview server** (if Claude Code) — launch.json has `slh-co-il` config serving `docs/` on port 8898
- **`ops/verify.ps1`** — run this before and after significant changes. Must be all green at session close.
- **`ops/daily_digest.py`** — `railway run python ops/daily_digest.py` for activity summary

## Traps (from previous session's post-mortem — do not repeat)

1. **`railway.json` is shared by 3 services** (monitor.slh, slh-bot [now deleted], SLH.co.il). Any change affects all of them. Don't remove keys without mapping impact.
2. **Never ask me to paste a token value.** Describe it (prefix, bot_id, last 4 chars) or ask me to set it directly in Railway. I've already leaked 3 tokens this project; don't make it 4.
3. **`parse_mode='Markdown'` eats `_` in commands.** Wrap every `/command_name` in backticks: `` `/add_roi` ``. Code spans preserve underscores, and Telegram still auto-linkifies them.
4. **`feedback.user_id` is TEXT, not BIGINT** in prod DB. Cast when joining.
5. **The pre-commit hook is not bypassable silently.** If you need `--no-verify`, explain why in the commit message.
6. **Don't declare "system ready" without end-to-end UX test.** A SQL query passing isn't the same as a user successfully using the feature.

## Communication style

- I write in Hebrew, direct, terse. Don't pad responses.
- When blocked, say so clearly. Don't invent workarounds that "should work".
- Verify empirically. Show evidence: log line, HTTP code, row count.
- If you hit a false positive, I'll call it out. Default to honesty over tidiness.
- I work at all hours. Don't assume "good morning" or "good night" — just start working.

## Files to read first (in this exact order)

```
CLAUDE.md                         ← BINDING agent rules — read FIRST (~3 min)
docs/SIG_STATISTICAL_DEFENSE.md   ← Required if touching ANY APY/ROI (~5 min)
ops/DISPATCH_20260425.md          ← routing + current state (~1 min)
ops/POST_MORTEM_20260424.md       ← what went wrong, how to avoid (~3 min)
ops/runbook.md                    ← daily commands reference (~2 min)
ops/CONTROL_CENTER_DESIGN.md      ← only if doing P3 (~5 min)
FINAL_STATUS_20260424.md          ← earlier handoff, still has useful URLs/IDs
AGENT_STATUS_20260424.md          ← cross-agent coordination (if other agents involved)
```

Total ~15-20 minutes to be fully up to speed.

## First things to do in this new session

1. `cd D:\SLH.co.il && pwsh ops\verify.ps1` — confirm current state matches this brief
2. Read the 3 essential files above
3. Ask me: "איזה P0-P4 אתה רוצה שאתחיל עליו?" (which P-level first?)
4. Don't write code before I answer.

## How to close this new session cleanly

When I say "סגור" / "close" / "wrap":
1. Run `ops/verify.ps1` one final time
2. Update todos
3. Write status at bottom of `ops/DISPATCH_20260425.md` (or create new-date file)
4. Commit + push
5. Give me 1-paragraph summary of what shipped and what remains

---

# PROMPT END

---

**Notes for Osif (not part of the prompt — read before pasting):**

1. **Remove this whole section** (everything below "PROMPT END") before you paste to a new agent. Or paste everything — the new agent will figure out what's structural.

2. **For cross-agent routing:** if you're pasting this to an agent working on a **different** project (e.g. SLH_ECOSYSTEM agent), edit:
   - The "Context" section to describe their project
   - The "Scope boundaries" to reflect their allowed paths
   - The "Pending work" to reflect tasks relevant to their scope
   - Keep everything else — the traps, communication style, file pointers, etc. are universal

3. **When the new agent asks "which P-level first"** — suggested answer based on what unblocks fastest:
   - **If you've already rotated the token** → say "P0 is done, verify and then go to P4 solo items"
   - **If you haven't rotated yet** → rotate first (60 seconds in BotFather + Railway), then paste this prompt
   - **If you want to accelerate sales** → answer the 5 P1 questions inline in the prompt and say "P1 go"

4. **Cross-paste strategy:** send this prompt to 2-3 agents simultaneously, wait for their initial status reports (should arrive within 2-5 min if they follow instructions), then pick the one with the clearest handshake as your primary. The others can continue on sibling projects.

5. **Paste this prompt as-is without answering the 5 P1 questions** = agent will be blocked at P1 and only work on P4 solo items. That's fine. P1 unblocking comes from you whenever you're ready.

---

**End of document.**
