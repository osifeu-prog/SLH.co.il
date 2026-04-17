# Architecture Decision Records · SLH Spark

*Append-only. When a decision changes, write a new entry that supersedes the old. Never edit past entries.*

---

## ADR-001 · 2026-04-17 — @G4meb0t_bot_bot deployment path
**Status:** Accepted
**Context:** Dating bot skeleton (`g4mebot/bot.py`, 200 lines, aiogram 3.x) needed a runtime. Three options considered.
**Decision:** Deploy as a separate Railway service (same project as `slh-api`, different service).
**Alternatives considered:**
- Local Python on Osif's PC — rejected: bot dies on PC reboot.
- Docker Compose alongside existing 24 bots — rejected: working tree of `docker-compose.yml` has had regressions; adding noise to a sensitive file is risky.
- Host on slh-api as a startup task — rejected: mixes concerns (API must stay stateless; polling bot needs persistent event loop).
**Consequences:**
- Short-term: one more Railway service ($0-$5/mo); one more deploy pipeline to monitor.
- Long-term: bot uptime independent of PC + API; clean separation of concerns.
- Enables: @SLH_AIR_bot (announcements) and @MY_SUPER_ADMIN_bot (admin alerts) to follow the same pattern.

---

## ADR-002 · 2026-04-17 — docker-compose.yml regression resolution
**Status:** Accepted (closed)
**Context:** Morning session flagged `docker-compose.yml` as regressed (reduced from 445 lines to 58, stripping 20 bot services). Evening verification found the working tree already back to 454 lines with 24 services.
**Decision:** No action. Use `docker-compose.yml` as-is. Update `ops/REGRESSIONS_FLAG_20260417.md` to mark as resolved.
**Alternatives considered:**
- Back up as `docker-compose.full.yml` — rejected: identical content, redundant.
- Split into `docker-compose.yml` (minimal) + `docker-compose.full.yml` — rejected: no one asked for a minimal version; full version already proven to work.
**Consequences:**
- Short-term: no disruption.
- Long-term: preserves the single-source-of-truth principle for infrastructure-as-code.

---

## ADR-003 · 2026-04-17 — Love tokens (HUG/KISS/HANDSHAKE) as stub
**Status:** Accepted (partial implementation)
**Context:** Osif proposed a virtual affection economy with three token types. Immediate UI wiring risks premature adoption at uncalibrated prices.
**Decision:** Ship schema + endpoints now (`/api/love/balance`, `/received`, `/send`, `/config`), but `/send` returns 503 unless `LOVE_TOKENS_ENABLED=1`. No UI button yet.
**Alternatives considered:**
- Ship UI + endpoint together — rejected: pricing not finalized (placeholder 5/20/2 AIC), daily cap not calibrated.
- Skip until pricing discussions settle — rejected: schema design done now is cheap; later work builds on it.
**Consequences:**
- Short-term: zero user-visible change. Engineering pre-work banked.
- Long-term: flipping to on requires only `LOVE_TOKENS_ENABLED=1` in Railway + a UI button. Pricing changeable via `LOVE_PRICE_HUG` / `LOVE_PRICE_KISS` / `LOVE_PRICE_HANDSHAKE`.
- Prices editable without code change.

---

## ADR-004 · 2026-04-17 — Testnet mode flag
**Status:** Accepted
**Context:** Osif wants to enable testnet payments for QA + tutorials without touching production mainnet.
**Decision:** Add `PAYMENT_MODE` env var (default `mainnet`). When set to `testnet`, BSC Chapel RPCs are selected automatically. Exposed via `/api/payment/config`.
**Alternatives considered:**
- Separate testnet deployment — rejected: doubles infra cost; easy to get out of sync.
- URL query flag (`?mode=testnet`) — rejected: leaks into accidental production calls.
**Consequences:**
- Short-term: zero risk to mainnet (flag defaults off).
- Long-term: one-line switch to run full testnet session for tutorials or audit prep.

---

## ADR-005 · 2026-04-17 — Burn + Buyback via Treasury module
**Status:** Accepted
**Context:** SLH tokenomics lacks deflation. Every SLH minted stays outstanding — can't support mcap growth long-term.
**Decision:** Ship `routes/treasury.py` with 3 tables (`treasury_revenue`, `treasury_buybacks`, `treasury_burns`) and 8 endpoints. Burn rate default 2% of AIC marketplace sales. Buyback rate default 10% of fiat revenue. No wallet-signer integration yet — SLH burns logged manually by Osif after MetaMask TX.
**Alternatives considered:**
- Hot wallet on Railway for automated burns — rejected: security risk, key management complexity.
- Do nothing until post-launch — rejected: transparency is a pre-launch trust signal.
**Consequences:**
- Short-term: public audit trail at `/api/treasury/summary`. Osif burns SLH manually + logs to the API.
- Long-term: when we're ready for automated buyback via CEX integration, the ledger + API surface is already designed.

---

## ADR-006 · 2026-04-17 — PWA instead of Play Store / App Store for alpha
**Status:** Accepted
**Context:** Osif asked whether to publish to Google Play + Apple App Store. Launch target is 16 days away (2026-05-03).
**Decision:** PWA only (manifest.json + service worker + install prompt). Defer native app store submissions to Phase 2 (post-1000-active-users).
**Alternatives considered:**
- Google Play Store now — rejected: $25 fee + 1-3 week review timeline uncertain.
- Apple App Store now — rejected: $99/year + 1-3 week review; Apple PWA support is limited anyway.
- Both stores simultaneously — rejected: review delay would push launch past 2026-05-03.
**Consequences:**
- Short-term: users on Android install via "Add to Home Screen"; PWA gives 80% of native feel at 0% bureaucracy.
- Long-term: PWA + app stores eventually coexist; PWA stays the canonical experience.

---

## ADR-007 · 2026-04-17 — slh-genesis as separate archive
**Status:** Accepted
**Context:** Osif proposed a dedicated archive folder for the system's history, decisions, creative concepts, and agent prompts. Distinct from `ops/` which is the active playbook.
**Decision:** Create `D:\SLH_ECOSYSTEM\slh-genesis\` with structured subfolders (LOGS, ART, TERMINAL_SHOW, PROMPTS, NOTES). Append-only. Master Documentation Agent prompt lives in `PROMPTS/central_agent.md`.
**Alternatives considered:**
- Keep everything in `ops/` — rejected: mixes active playbook with historical record; `ops/` would grow unboundedly.
- Separate git repo — rejected: overhead of repo management without clear benefit.
- Wiki (GitHub wiki / Notion) — rejected: Osif wants files in the repo alongside code.
**Consequences:**
- Short-term: three more files (README, central_agent, timeline) in the working tree.
- Long-term: `slh-genesis` becomes the "book" — any AI joining later reads this first for context.
