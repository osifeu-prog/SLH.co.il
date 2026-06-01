# SLH Spark · Master Prompt · 2026-04-25
**Purpose:** A single self-contained prompt to start a NEW conversation with any agent (Claude / GPT / Cursor / Gemini) and give them full context to continue from exactly where we are.

**How to use:**
1. Copy this entire document.
2. Paste at the start of a new agent session.
3. Add at the bottom: "Begin. Introduce yourself per § 6. Then ask me what to do."

**Web-viewable:** https://slh-nft.com/ops-viewer.html?file=MASTER_PROMPT_20260425.md

---

## §1 · WHO YOU ARE TALKING TO

**Operator:** Osif Kaufman Ungar
- Telegram: @osifeu_prog (ID 224223270)
- Email: osif.erez.ungar@gmail.com
- WhatsApp: 972584203384
- Solo Hebrew-speaking dev/founder building SLH Spark — a crypto investment ecosystem in Israel.
- Has been at this for ~1 year. Multiple parallel agents have contributed.
- Communication: Hebrew chat preferred, English code/commits. Direct action over explanation. "כן לכל ההצעות" usually means "go".
- **Currently exhausted.** Needs ORDER and RESULTS, not more proposals.

---

## §2 · CRITICAL READ ORDER (open in order before acting)

```
1. ops/CONTROL.md                       — daily state board. open every morning.
2. ops/SYSTEM_ALIGNMENT_20260424.md     — Active Agents Claims Board. REGISTER YOURSELF before any work.
3. ops/SYSTEM_ARCHITECTURE.md           — system map (what each component is, where it runs)
4. ops/OPS_RUNBOOK.md                   — when X breaks, do Y
5. ops/INCIDENTS.md                     — past failures + lessons
6. ops/PAGE_INVENTORY_20260425.md       — 117 pages classified, operator marks decisions inline
7. ops/CUSTOMER_PROSPECTUS_DEMO.md      — pitch template (with [DEMO] markers)
8. ops/FOLLOWUP_TEMPLATES.md            — outreach follow-up scripts
9. ops/TEST_PAYMENT_GUIDE.md            — micro-payment validation flow
10. CLAUDE.md (repo root)                — project-wide rules
```

All of these are accessible via browser at `https://slh-nft.com/ops-viewer.html?file=<filename>.md`.

---

## §3 · WHAT EXISTS (verified live as of 2026-04-25)

### Live & verified
- **API:** `https://slh-api-production.up.railway.app/api/health` → 200, v1.1.0
- **Website:** 117 HTML pages on GitHub Pages
- **Docker bots:** 25 services in `docker-compose.yml`
- **Postgres + Redis:** Railway-managed, also local dev
- **CRM Phase 0:** `/api/ambassador/contacts` — full CRUD + import working
- **event_log:** 17 entries, ESP32 heartbeats flowing
- **Telegram Gateway:** loaded; `primary_bot_token_set: false` (THE blocker)
- **Pre-commit + commit-msg hooks:** active, drift-aware
- **Audit script:** `scripts/audit_data_integrity.py` finds phantom data
- **6 ESP32 devices** registered, 1 actively heartbeating
- **admin-bot Telegram dashboard:** 8 control commands shipped (commit `6e22bb9`)
- **Customer prospectus DEMO** (with [DEMO] placeholders) ready to fill + send

### What customers can buy today
- **Nothing through SLH directly.** Card payment not wired (Cardcom credentials needed).
- TON/BNB micro-test (`pay-test.html`) works end-to-end on mainnet.
- Manual flow: Bit/PayBox/bank-transfer to Zvika Kaufman's exempt-dealer account, then manually grant Premium in DB.

### What was REMOVED today (cleanup)
- 3 unused funnel pages: `invest-preview`, `community-beta`, `admin/funnel-dashboard` — git rm + commit `dffb7f3`.
- 4 admin leaks from public nav: `/admin.html`, `/analytics.html`, `/admin/reality.html`, `/project-map.html` — commit `a0091e5`.
- 5 pages got `noindex` meta (admin-bugs, reality, chain-status, guardian-diag, upgrade-tracker).
- Reverted noindex on `alpha-progress.html` (it's deliberately public transparency).

---

## §4 · OPEN BLOCKERS (only the operator can resolve)

| # | Blocker | Action | Time |
|---|---------|--------|------|
| 1 | `TELEGRAM_BOT_TOKEN` env var not set on Railway | Railway → Variables tab → add 3 vars | 3 min |
| 2 | `git config --global user.name/email` still default | one PowerShell command | 10 s |
| 3 | Yaara reply to WhatsApp (sent 2026-04-24) | wait or follow-up via `ops/FOLLOWUP_TEMPLATES.md` | — |
| 4 | Eliezer's Excel of 130 investors | external — wait | — |
| 5 | Cardcom API credentials (for card payments) | apply with Zvika's exempt-dealer account | days |
| 6 | ESP32 firmware flash (final pairing) | physical USB connection | 5 min |

---

## §5 · CURRENT GOALS (in priority order)

1. **First real paying customer (₪)** — anyone, any amount. Validates end-to-end.
2. **One unified UI/UX update** — without breaking the system that works
3. **Audience update across channels** — Facebook (6 pages), YouTube (2 channels), Telegram, WhatsApp
4. **Packaging decision** — PWA / native app / Mini App — see §8
5. **Maintain coordination protocol** — every agent registers in SYSTEM_ALIGNMENT and updates it on session close

---

## §6 · AGENT IDENTITY PROTOCOL (mandatory)

**Step 1 — When you start (first turn in your session):**

Introduce yourself in EXACTLY this format:

```
🤖 AGENT INTRODUCTION
─────────────────────
Name: <your model + version, e.g. "Claude Opus 4.7 1M context">
Session: <give your session a short tag, e.g. "ui-ux-cleanup">
Capabilities: <what you have access to: filesystem? git? web? bash?>
Limitations: <what you CANNOT do: e.g. "no Railway dashboard access">
Working window: <est. duration: 1 hour, overnight, etc>
```

**Step 2 — Register in SYSTEM_ALIGNMENT_20260424.md:**

Add a new entry under `## 👥 Active Agents — Claims Board` following the existing template:

```
### Agent: <Name> — <Session tag>
**Reporting window:** <date>
**Current status:** 🟡 in-progress
**What I'm doing this session:** <task scope>
**What I will NOT touch (deliberate):** <out-of-scope items>
**Started:** <timestamp>
```

Commit with message `ops(alignment): register <session-tag> session`.

**Step 3 — Work.**

**Step 4 — When closing your session:**

Update your SYSTEM_ALIGNMENT entry:

```
**Current status:** ✅ closed
**What I did this session:**
1. <bullet>
2. <bullet>
...

**What I did NOT do (deliberate):**
- <bullet>

**Git state at close:**
- <repo>: <commit hash>

**Next session trigger:** <what condition unblocks the next agent>
```

Commit with message `ops(alignment): close <session-tag> session`.

**Then update `ops/CONTROL.md`** with a one-line entry under "LAST 48 HOURS" if your work changed live state.

---

## §7 · WORK RULES (non-negotiable — see CLAUDE.md for full)

1. **Hebrew UI / English code/commits.** Don't mix.
2. **No fake/mock data in production.** Use `--` or `[DEMO]` markers.
3. **Always `git diff --stat` before commit.** If it's not what you expected, halt.
4. **`api/main.py` and root `main.py` must stay in sync.** Railway builds from root.
5. **Never `git push --force` to master.** Period.
6. **Never commit `.env`.** Only `.env.template`.
7. **Pre-commit guard is active.** Don't bypass with `GUARD_CONFIRMED=1` unless intentional + scoped commit prefix.
8. **Don't create new pages — merge into existing.** Operator already has 117 pages. New ones are noise unless explicitly asked.
9. **Don't create parallel ops docs.** Use SYSTEM_ALIGNMENT and CONTROL.md sections.
10. **Don't promise "guaranteed" returns or "fixed APY".** Use "target" / "Dynamic Yield" framing only. See `project_dynamic_yield_pivot.md`.

---

## §8 · STRATEGIC PACKAGING OPTIONS (choose one)

The system is built. Now: how do customers experience it?

### Option A — PWA (Progressive Web App) ⭐ RECOMMENDED FIRST
**What:** Add `manifest.json` + service worker to `slh-nft.com`. Customer visits site → "Add to Home Screen" → app icon, full-screen experience, offline cache.
**Cost:** ~2 hours of work. Free.
**Pros:** Zero app-store hassle. Same code. Works on iOS + Android. Fast iteration.
**Cons:** Some browsers limit PWA features. Less "premium feel" than native.

### Option B — Native App (via Capacitor or React Native wrapper)
**What:** Wrap PWA in native shell. Submit to Apple App Store + Google Play.
**Cost:** 2-3 weeks of focused work. Apple Developer $99/year, Google $25 one-time. Plus ongoing review delays.
**Pros:** App-store presence. Push notifications easier. Premium feel.
**Cons:** Slower iteration. App-store policies may reject crypto features.

### Option C — Telegram Mini App ⭐ ALREADY 80% DONE
**What:** `/miniapp/dashboard.html` + gateway already exist. Set BotFather + `TELEGRAM_BOT_TOKEN` env on Railway → live.
**Cost:** 5 minutes once env is set. Free.
**Pros:** Customer never leaves Telegram (where the community lives). No install. Single click via bot button. Instant.
**Cons:** Telegram-only audience. Limited UI compared to web.

### Option D — Multi-channel (Web + PWA + Telegram Mini App)
**What:** Do A and C together. Customer chooses entry point.
**Cost:** ~3 hours combined.
**Pros:** Maximum reach. No commitment to native app yet.
**Cons:** Two surfaces to maintain.

### Option E — Defer, focus on customer #1
**What:** Don't package. Send WhatsApp link directly to known prospects. Get one to pay. THEN package based on what worked.
**Cost:** 0.
**Pros:** Validates demand before committing to packaging effort.
**Cons:** Slower scaling.

**Operator's call.** Document the choice in `ops/CONTROL.md`. All agents respect it.

---

## §9 · AUDIENCE-UPDATE CHANNELS (when ready to announce)

Per memory `reference_social_links.md`:

| Channel | URL/handle | Audience size | Last update |
|---|---|---|---|
| Telegram main bot | @SLH_AIR_bot | 21 registered users | active |
| Telegram community | t.me/SLHcommunity (or similar) | check `feedback_*.md` | — |
| Facebook page #1 | (find in `reference_social_links.md`) | unknown | unknown |
| Facebook page #2-6 | (5 more pages, same memory file) | unknown | unknown |
| YouTube #1 | (in same memory file) | unknown | unknown |
| YouTube #2 | (in same memory file) | unknown | unknown |
| WhatsApp groups | various | unknown | unknown |
| Twitter/X | (if exists) | unknown | unknown |
| LinkedIn | personal | unknown | unknown |

**When announcing:** keep tone honest. No "guaranteed", no "100x", no "Ponzi-scheme adjacent" language. Use:
- "Alpha community open"
- "Early access for partners"
- "Looking for first paying customers — here's why we're different"

Use the consent of `ops/CUSTOMER_PROSPECTUS_DEMO.md` (after [DEMO] markers replaced).

---

## §10 · WHAT WOULD MAKE THE SYSTEM "READY" (closure checklist)

Operator wants the system ready for operation. Here's the verified-honest checklist:

### Tier 1 — Customer experience (HIGHEST priority)
- [ ] First paying customer through end-to-end flow (any amount)
- [ ] PWA installable from `slh-nft.com`
- [ ] Telegram Mini App live (after `TELEGRAM_BOT_TOKEN` env set)
- [ ] One-click `/start` flow from any landing page → trial / demo / signup
- [ ] All public pages have proper `<meta name="description">` + OG tags
- [ ] No 404s on linked pages (audit redirects)

### Tier 2 — Operational hygiene
- [ ] Page inventory annotated by operator (KEEP / HIDE / DELETE)
- [ ] Cleanup pass executed based on annotations
- [ ] Daily digest (`scripts/daily_digest.py`) scheduled in Windows Task Scheduler
- [ ] Railway watchdog (`scripts/railway_watchdog.py`) scheduled
- [ ] All bot tokens rotated (31 leaked in chat history per memory)
- [ ] CONTROL.md updated daily

### Tier 3 — Growth infrastructure
- [ ] Cardcom (or alternative card processor) wired
- [ ] Card payment + receipt flow tested
- [ ] All Telegram bots on webhooks (not polling) — currently 0/22
- [ ] Daily backtest CSV running on Railway (not just local)
- [ ] Public events feed populated (`/api/events/public` returns 0 today — needs broadcast/payment events)

### Tier 4 — Scale prep (do later)
- [ ] Native app submission
- [ ] Multi-language i18n on remaining 65% of pages
- [ ] Theme switcher on remaining 58% of pages
- [ ] Webhook migration for all bots
- [ ] Staking/Rebasing real on-chain (not internal ledger)

---

## §11 · WHAT TO SEND BACK TO THE OPERATOR (closure report template)

When you finish your session, send this format:

```
🏁 SESSION CLOSURE — <session-tag>
─────────────────────────────────

📊 What I changed:
- <commit hash> <repo> · <one-line summary>
- ...

📈 Verified live:
- <URL or test command> → expected result observed

⚠️ Issues encountered:
- <issue> → <how I handled it> OR <flagged for next session>

📋 What I did NOT touch (and why):
- <out-of-scope item>

🚦 Recommended next move:
- <single concrete action>

🔗 Updated docs:
- ops/CONTROL.md, ops/SYSTEM_ALIGNMENT_20260424.md
```

---

## §12 · CLOSURE REQUEST FROM OPERATOR (2026-04-25)

The operator has asked for a "report from everyone" so he can decide intelligently. Each agent that picks up from this prompt should produce:

1. **Self-introduction** (per §6).
2. **State assessment** — read CONTROL.md + run state-snapshot commands from §7 of SYSTEM_ARCHITECTURE.
3. **Plan** — what you propose to do, with time estimate, BEFORE you do it.
4. **Execution** — only what was approved.
5. **Closure report** (per §11).
6. **One concrete recommendation** for the operator to decide on next.

If you don't have something concrete to offer that moves toward the goals in §5 — say so. Don't fabricate work.

---

## §13 · END OF PROMPT — BEGIN SESSION

You now have full context. Acknowledge by:

1. Introducing yourself per §6.
2. Stating which option from §8 (packaging) you'd recommend, with reasoning.
3. Asking the operator for ONE specific decision (don't list 10 options).

Then wait for the operator's response.

**Never:**
- Skip the introduction.
- Skip registering in SYSTEM_ALIGNMENT.
- Create new ops docs (extend existing).
- Spawn parallel pages (extend existing).
- Promise "guaranteed returns".
- Force-push to master.

**Always:**
- Hebrew with operator (unless he switches).
- Update CONTROL.md when state changes.
- `git diff --stat` before commit.
- Close your session formally with a report.

---

_Last updated: 2026-04-25._
_Next agent: introduce yourself. The operator is waiting._
