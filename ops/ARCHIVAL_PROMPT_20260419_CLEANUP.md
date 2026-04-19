# SLH Spark · Archival Prompt · 2026-04-19 · Cleanup Session
**Paste this verbatim into a new Claude Code session to resume with full context.**

---

## WHO I AM

- **Osif Kaufman Ungar** (@osifeu_prog · Telegram ID `224223270`) · GitHub: `osifeu-prog`
- Solo Hebrew-speaking developer building **SLH Spark** — institutional-grade crypto investment ecosystem in Israel
- Windows 10 Pro · working directory `D:\SLH_ECOSYSTEM\`
- 10+ institutional investors interested (1M+ ILS each)

## COMMUNICATION RULES

- Hebrew in UI, English in code/commits. Direct action, no long explanations.
- Never fake/mock data in production — use `[DEMO]` / `test_` prefix.
- "כן לכל ההצעות" = proceed with all suggestions.

## STACK SNAPSHOT

- **Website:** 83 HTML pages on GitHub Pages (`slh-nft.com`) — separate repo `osifeu-prog/osifeu-prog.github.io`
- **API:** FastAPI on Railway (`slh-api-production.up.railway.app`), 230+ endpoints in ~7000-line `api/main.py`. **Railway builds from ROOT `main.py`, not `api/main.py`.**
- **Bots:** 25 Telegram bots via Docker Compose (aiogram 3.x)
- **Chain:** SLH BEP-20 on BSC (`0xACb0A09414CEA1C879c67bB7A877E4e19480f022`), PancakeSwap V2 pool `0xacea26b6e132cd45f2b8a4754170d4d0d3b8bbee`
- **DB:** PostgreSQL 15 + Redis 7, 30+ tables, SHA-256 audit chain

### 5 + 1 Token Economy

| Token | Purpose | Target |
|---|---|---|
| SLH | Premium / governance | 444 ILS |
| MNH | Stablecoin | 1 ILS |
| ZVK | Activity rewards | ~4.4 ILS |
| REP | Reputation score | 0–1000+ |
| ZUZ | Anti-fraud "Mark of Cain" | Auto-ban at 100 |
| AIC | 6th token · AI credits | 1 minted so far, reserve $123,456 |

## REPO STATE AS OF 2026-04-19 EVENING

- Ecosystem repo `master` at commit **`be7a574`** (pushed to origin).
- Website repo `main` — `working tree clean`.
- Recent relevant commits:
  - `be7a574` fix(claude-bot): run /app/bot.py explicitly (was crash-looping)
  - `5fdff5c` chore(api): wire whatsapp router + sync main.py + strip hardcoded DB password
  - `87a84bd` docs(handoff): sprint summary 2026-04-19 — status.html + agent-hub.html shipped
  - `70aa04f` (website) feat: /status.html + /agent-hub.html — live transparency + agent ICQ
  - `d3407b2` (website) feat(auth): Telegram login widget on join.html

## LIVE STATE

- **API health:** `{"status":"ok","db":"connected","version":"1.0.0"}` — will flip to `1.1.0` once Railway picks up commit `5fdff5c`.
- **Docker:** 23/25 bots up. `slh-ledger` (bad token) + `slh-claude-bot` (missing ANTHROPIC_API_KEY) are stopped with `restart=no`.
- **Website:** slh-nft.com live, 83 pages, multi-language (HE/EN/RU/AR/FR), analytics + AI assistant on 100%, theme coverage ~42%, i18n ~37%.
- **Users:** 9 registered, 5 verified contributors (Osif, Tzvika, Zohar, Eli, Yakir). Genesis: 0.08 BNB raised.

## WHAT WAS CLOSED TODAY

1. `pay.html` 3-bug audit → **verified already shipped** (c622208) — `ton-addr` fallback + "בחר מוצר קודם" placeholders + "יוצג לפי המוצר שנבחר" for bank amount.
2. `wallet.html` blockchain balances → **verified already wired** — calls `/api/user/{id}` + `/api/external-wallets/{id}`; returns real 199,788 SLH + TON/BNB.
3. `roadmap.html` sections → **verified already present** — 4 phases, 37 items, progress bar, 4 stat cards, 5 filters.
4. Telegram Login Widget → **verified already on `/join.html` + `/dashboard.html`** (d3407b2).
5. `community.html` DM button → **verified live** (line 2326 `.dm-btn`).
6. `/docs` hide + rate-limit middleware → **code already in `api/main.py`** (commit 50aa6d3 from yesterday). Gate activates only when Railway has `ENV=production`.
7. `routes.whatsapp` wired into FastAPI app (import + include_router + set_pool + init_whatsapp_tables).
8. `broadcast_airdrop.py` — hardcoded Railway DB password removed, now requires `DATABASE_URL` env var.
9. `docker-compose.yml` — `slh-claude-bot` command set to `/app/bot.py` (was failing on `/workspace/bot.py`).
10. `.gitignore` — added `website/`, `device-registry/*/firmware/`, `.claude/local`, `_session_state/`, `System Volume Information/`, `*.corrupted`, `**/.pio/`.
11. Cleanup — moved 21 root `.md`/`.txt` stragglers to `ops/archives_20260419/`.
12. `slh-ledger` container — stopped + `restart=no` to silence 587-iteration crash loop.

## STILL BLOCKED ON OSIF (must be done in dashboards / phone)

1. **Railway Variables** — set `ENV=production`, `DOCS_ENABLED=0`, `JWT_SECRET=<random 32+ chars>`, `ADMIN_API_KEYS=<rotated>`. Without these:
   - `/docs` stays public (200 instead of 404)
   - rate limit still runs but the JWT auth code paths degrade
2. **BotFather token rotation** — 30 of 31 leaked tokens still active. Priority: `SLH_LEDGER_TOKEN` (dead, 401). Ledger bot can't boot until rotated.
3. **`ANTHROPIC_API_KEY`** in `D:\SLH_ECOSYSTEM\slh-claude-bot\.env` — required to launch `@SLH_Claude_bot`.
4. **Guardian repo decision** — `https://github.com/osifeu-prog/gardient2.git` returns 404. Either `gh repo create` a new one or fold the code into `slh-api`.
5. **ESP32 `UPLOAD_FIX.ps1`** — missing from disk, blocking CYD screen flash.
6. **4 contributors website login** (Tzvika, Eli, Yakir, +1) — external action to receive their ZVK.

## CODE-LEVEL WORK STILL OPEN (not urgent, not blocking)

- Webhook migration for 22 polling bots (~12h)
- WebSocket for `community.html` real-time feed (~6h)
- i18n on 27 remaining pages (~63% of site)
- Theme switcher on 25 remaining pages (~58% of site)
- Mobile + e2e testing sweep (3h)
- Log aggregation (loki/fluentd) + pg_dump backup cron (4h)
- Docker Secrets migration (Copilot review P1)
- Central logging (Copilot review P1)
- ESP32 keep-alive heartbeat (Copilot review P2)
- DB locking review under 20 concurrent bots (Copilot review P2)

## REFERENCE FILES TO READ ON NEXT BOOT

```text
D:\SLH_ECOSYSTEM\CLAUDE.md                                       ← onboarding
D:\SLH_ECOSYSTEM\TASKS_STATUS_2026-04-18.md                      ← 73-task audit (2026-04-19 line is this file)
D:\SLH_ECOSYSTEM\ops\SESSION_HANDOFF_20260419_CLEANUP.md         ← this pass
D:\SLH_ECOSYSTEM\ops\SESSION_HANDOFF_20260419_SPRINT.md          ← status.html + agent-hub.html build
D:\SLH_ECOSYSTEM\ops\MASTER_WORKPLAN_20260418.md                 ← full roadmap
D:\SLH_ECOSYSTEM\ops\EXECUTOR_AGENT_PROMPT_20260418.md           ← comprehensive audit agent briefing
```

## SESSION START RITUAL

```bash
cd D:\SLH_ECOSYSTEM
curl -s https://slh-api-production.up.railway.app/api/health    # confirm 1.1.0
curl -so/dev/null -w "%{http_code}\n" https://slh-api-production.up.railway.app/docs
git status && git -C website status
docker ps --format "table {{.Names}}\t{{.Status}}"
```

Then ask Osif: priority now? (options: rotate tokens → onboard contributors → ship webhook migration → i18n sweep → launch/launchpad)
