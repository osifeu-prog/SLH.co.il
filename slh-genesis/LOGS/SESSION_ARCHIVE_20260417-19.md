# 📦 Session Archive · 2026-04-17 → 2026-04-19

**Target audience:** Next Claude Code agent (or any AI agent) picking up the project.
**Paste as opening message in a new session** to load full context in 90 seconds.

---

## 🎯 Quick orientation

- **Who:** Osif Kaufman Ungar · Telegram `@osifeu_prog` · TG ID `224223270`
- **What:** SLH Spark — Israeli crypto investment ecosystem (6 tokens, 225+ endpoints, 25 bots, 80 pages)
- **Where:** `D:\SLH_ECOSYSTEM\` · Railway (`osifeu-prog/slh-api`) · GitHub Pages (`osifeu-prog/osifeu-prog.github.io`)
- **Phase:** Late Alpha · Beta launch target 2026-05-03
- **Language:** UI in Hebrew · code/commits in English · comments bilingual allowed

---

## 🎬 What happened in this 3-day session

### Day 1 — 2026-04-17 · Morning (55+ commits by Master Executor)
- 6 tracks orchestrated: Payments, Experts, Dating, No-FB, Social, AIC
- AIC = 6th token born today (AI Credits, ~$0.001)
- Payments: TON+BSC auto-verify live, micro-test tier
- Dating: 8 endpoints + `@G4meb0t_bot_bot` skeleton
- Broadcast to 5 networks live

### Day 1 — 2026-04-17 · Evening (Claude Code)
- **`slh-skeleton.js`** merged APIs (show/hide/withSkeleton alongside apply/reveal)
- **`DESIGN_SYSTEM.md`** canonical reference
- **`nfty-bot`** → auto-post to `@slhniffty` on approve
- **`@G4meb0t_bot_bot`** enhanced (referral, `/share`, `/site`, web↔bot bridge), OLD token rotated
- **10 new seed blog posts** + sitemap 4→50 URLs
- **🔴 PAYMENT 500 FIX** · `_ensure_payment_tables()` at `set_pool()` startup
- **First receipt issued** · `SLH-20260417-000001` · 0.0005 BNB · delivered to Osif via `@MY_SUPER_ADMIN_bot`
- `/receipts.html` standalone viewer
- **4 tokenomics decisions:** Railway deploy path for G4meb0t · docker-compose restored · Love tokens stub · Testnet flag

### Day 2 — 2026-04-18 · The big build
- **`routes/treasury.py`** — revenue + buyback + burn tracking (AIC 2% burn policy)
- **`slh-genesis/`** archive folder born (README + central_agent + timeline + 7 ADRs)
- **`slh-flip.js`** flip+scramble animations + `data-*` markers
- **70/80 pages upgraded** (60 via `shared.js` auto-inject + 10 manual)
- **`/live.html`** FB-blocked-→ pivot to Telegram-first landing
- **`/upgrade-tracker.html`** live scanner for 80 pages
- **PWA:** `manifest.json` + `sw.js` (cache-first for assets, network-first for HTML)
- **`/encryption.html`** SEO landing for "עברית מעוותת" long-tail
- **`/alpha-progress.html`** public dashboard with countdown
- **Facebook Live warning** handled — pivoted to Telegram/LinkedIn/X as primary channels

### Day 3 — 2026-04-19 · Creator Economy (Track 7)
- **`routes/creator_economy.py`** — XP=ROI metric + SLH Index + personal shop
- **`/sell.html`** — upload NFT/course with story, price, course-lesson toggle
- **`/gallery.html`** — public gallery with filter/sort/search + modal buy
- **`/shop.html`** — personal creator dashboard with XP hero card
- **SLH Index pill** in `shared.js` — floats on main public pages
- `v0.9.0-alpha` tag cut

---

## 💾 State of Production (verified 2026-04-19)

### API (Railway · `slh-api-production.up.railway.app`)
| Endpoint | Status |
|----------|:------:|
| `/api/health` | ✅ 200 |
| `/api/treasury/summary` | ✅ 200 |
| `/api/love/config` | ✅ 200 (stub, disabled by default) |
| `/api/payment/receipts/224223270` | ✅ 200 (1 receipt) |
| `/api/payment/status/{uid}` | ✅ 200 (after table bootstrap fix) |
| `/api/creator/*` | 🟡 Railway redeploy pending (pushed `72f15f5`) |
| `/api/dating/*` | ✅ 200 |
| `/api/sudoku/*` | ✅ 200 |

### Website (GitHub Pages · `slh-nft.com`)
All 12 new pages return 200:
- `/sell.html` · `/gallery.html` · `/shop.html`
- `/receipts.html` · `/live.html` · `/encryption.html`
- `/alpha-progress.html` · `/upgrade-tracker.html`
- PWA: `/manifest.json` · `/sw.js`
- Library: `/js/slh-flip.js`

### Git tags
- `v0.9.0-alpha` on master (2026-04-19)

### Unpushed staged work (DO NOT touch)
- `5fdff5c chore(api): wire whatsapp router + sync main.py` — committed, waiting behind `72f15f5`
- Staged `api/` reorganization — intentional WIP by another agent

---

## 🔴 Blocked on Osif (no agent can act)

1. **N8N_PASSWORD** in Railway Variables → unblocks Social Automation agent
2. **CYD screen colorTest** confirmation → unblocks ESP firmware E.2+
3. **AIC first mint** via `/admin-tokens.html` (supply currently ~1)
4. **Rotate 30 remaining bot tokens** (1 rotated: GAME_BOT_TOKEN)
5. **Deploy `@G4meb0t_bot_bot`** as separate Railway service (guide: `g4mebot/README.md`)
6. **Facebook account warning** → Osif never shared screenshot; pivoted to other channels
7. **Uncommitted `pay.html` WIP** — QR encoding experiment, left alone per user instruction

---

## 🎨 Design language (cheat-sheet)

```
Font:          Rubik (primary) + JetBrains Mono (code/numbers)
Brand colors:  #00ff41 (green) · #00e5ff (cyan) · #a855f7 (purple) · #ffd700 (gold) · #ec4899 (rose)
BG gradient:   from #05080f (page) → rgba(255,255,255,.03) (surface)
Border radius: 10-16px organic, 50px pills
Animations:    data-flip (3D rotate) · data-scramble (gibberish→text) · respects reduced-motion
Direction:     dir="rtl" lang="he" on all Hebrew-first pages
```

Every new page should start with:
```html
<link rel="stylesheet" href="/css/slh-design-system.css">
<meta name="slh-version" content="v1.0-flip">
<script defer src="/js/slh-flip.js?v=20260417"></script>
```

---

## 🤖 For the next AI agent

### First 90 seconds of a new session
1. `curl https://slh-api-production.up.railway.app/api/health` → confirm API up
2. `curl https://slh-api-production.up.railway.app/api/creator/slh-index` → confirm creator deploy done
3. Read `D:\SLH_ECOSYSTEM\CLAUDE.md` → who, what, rules
4. Read `D:\SLH_ECOSYSTEM\ops\ALPHA_READINESS.md` → timeline to 2026-05-03 launch
5. Read `D:\SLH_ECOSYSTEM\slh-genesis\LOGS\timeline.md` → append-only history
6. `cd D:\SLH_ECOSYSTEM && git status` — check both repos

### Work rules
- Hebrew UI text · English code/commits
- Every `routes/*.py` MUST sync to `api/routes/*.py` (Railway builds from api/ copy)
- Every Railway change takes 60-180s to deploy
- Never commit `.env`
- `bot_template.py` regression is OPEN — don't use it as generic template
- For new pages: include `meta name="slh-version" content="v1.0-flip"` + `slh-flip.js` script

### Common patterns
- **Add new endpoint module:**
  1. Create `routes/<name>.py` with `router = APIRouter(prefix="/api/<name>")` + `_pool` + `set_pool()`
  2. Import + `app.include_router()` + `_set_pool(pool)` in BOTH `main.py` AND `api/main.py`
  3. Commit + push master → Railway redeploys
- **Add new HTML page:**
  1. Use design system tokens from `slh-design-system.css`
  2. Include `slh-flip.js` + meta marker
  3. Add to `sitemap.xml` + `blog/index.html` if relevant
  4. Commit + push main (website repo)

### Critical decisions already made (don't re-litigate)
- @G4meb0t_bot_bot → Railway (ADR-001)
- docker-compose regression → resolved (ADR-002)
- Love tokens → schema shipped, UI deferred (ADR-003)
- Testnet → flag only, off by default (ADR-004)
- Treasury burns → manual for SLH, auto-log for AIC (ADR-005)
- PWA first, app stores later (ADR-006)
- slh-genesis archive separate from ops (ADR-007)

---

## 📋 Open task priorities (next session)

| # | Track | Task | Est | Blocked on |
|:-:|:-----:|------|:---:|:-----------|
| 1 | 7 | Add "buy now" E2E flow in gallery → pay.html → creator_sales | 2h | nothing |
| 2 | 4 | `/blog/` push to 15+ posts + Google Search Console verification | 3h | nothing |
| 3 | 1 | wallet.html live BSC+TON balances (endpoints ready) | 2h | nothing |
| 4 | 5 | i18n on 27 remaining pages | 4h | nothing |
| 5 | 7 | SLH Index widget styling consistency across themes | 1h | nothing |
| 6 | A | Deploy @G4meb0t_bot_bot to Railway | 3min | **Osif** |
| 7 | A | N8N_PASSWORD env var | 2min | **Osif** |
| 8 | A | AIC first mint | 3min | **Osif** |

---

## 🪪 Living artifacts

- **CLAUDE.md** (root) — authoritative work rules
- **PROJECT_GUIDE.md** — complete onboarding
- **TASKS_STATUS_2026-04-18.md** — 73-task consolidated status
- **ops/ALPHA_READINESS.md** — roadmap to Beta
- **ops/AGENT_PROMPTS_READY.md** — copy-paste prompts for external AI
- **ops/DESIGN_SYSTEM.md** — tokens, themes, skeletons
- **slh-genesis/LOGS/timeline.md** — append-only history
- **slh-genesis/LOGS/decisions.md** — 7 ADRs (append-only)
- **slh-genesis/PROMPTS/central_agent.md** — documentation-agent prompt

---

**Archived at:** 2026-04-19 · End of 3-day intensive session
**Next milestone:** 2026-05-03 Public Beta launch
**If anything breaks, start at:** `https://slh-api-production.up.railway.app/api/health`
