# Team Tasks / משימות צוות

> SLH Ecosystem | SPARK IND
> Created: 2026-04-07
> Last verified: 2026-04-18 (AI-verified against live API/website/docker)
> Full status report: [TASKS_STATUS_2026-04-18.md](TASKS_STATUS_2026-04-18.md)

---

## Priority 1 — Critical (This Week) / קריטי - השבוע

- [x] **Restart slh-factory container** — Up 3h ✓

- [x] **Fix duplicate bot token: AIRDROP = EXPERTNET** — EXPERTNET_BOT_TOKEN marked `LEGACY_DISABLED 2026-04-14`. AIRDROP_BOT_TOKEN now unique (`8530795944:...`)

- [ ] **Test community.html posting from multiple devices** — Endpoints live (`/api/community/*`), manual device test pending
  ```
  ✓ POST /api/community/posts (live)
  ✓ POST /api/community/posts/{id}/like (live)
  ✓ POST /api/community/posts/{id}/comments (live)
  ✓ GET /api/community/posts (live)
  ✓ /api/community/health returns OK
  ```

- [x] **Deploy wallet API endpoints to Railway** — `/api/wallet/{user_id}`, `/api/wallet/deposit`, `/api/wallet/send`, `/api/wallet/price`, `/api/wallet/{user_id}/balances`, `/api/wallet/{user_id}/transactions` all live

- [ ] **Connect wallet.html to real blockchain data** — wallet.html has 0 on-chain calls (grep: `TON|BSC.*balance|getBalance|tonweb|bsc.*rpc` = 0). Endpoints ready; frontend not wired yet

---

## Priority 2 — Important (This Month) / חשוב - החודש

- [x] **Build trading/order-book engine for SLH** — `/api/p2p/*` + `/api/p2p/v2/*` (create-order, fill-order, cancel-order, orders list) live

- [ ] **Add Telegram bot authentication to website login** — `/api/auth/telegram` endpoint exists but widget NOT on website (grep across `website/*.html` = 0 matches for `telegram-widget|TelegramLoginWidget`)

- [ ] **i18n support in all Telegram bots (HE, EN, RU, AR, FR)** — Website has 5-lang hreflang; bots still Hebrew-only

- [ ] **Real-time WebSocket for community page** — community.html has 0 WebSocket refs. Still uses polling

- [x] **Connect analytics.html charts to real daily data** — `/api/analytics/stats` live, analytics.html has 16 chart refs

- [ ] **BLOCKED (Osif):** Fix Guardian GitHub repo (returns 404) — Code was at `D:\telegram-guardian-DOCKER-COMPOSE-ENTERPRISE` (per `guardian/LOCATION.txt`). Decision needed: create new repo OR merge into slh-api

- [x] **Build admin dashboard with real data** — `admin.html` connects to `/api/admin/dashboard` + 27 other `/api/admin/*` endpoints

---

## Priority 3 — Enhancement (Next Month) / שיפורים - החודש הבא

- [x] **Shariah-compliant staking (deterministic yield)** — `website/kosher-wallet.html` has shariah/kosher/halal content; `/api/staking/plans` returns deterministic APY (no variable interest)

- [ ] **Prediction markets (no-loss model)** — not implemented

- [ ] **Launchpad for ethical projects** — `/api/launch/contribute` + `/api/launch/status` exist but screening/voting not built

- [ ] **Ambassador SaaS bot-per-ambassador system** — Spec in memory, not implemented. See [project_ambassador_saas](../../memory/project_ambassador_saas.md)

- [x] **Mobile app (React Native / PWA)** — `D:\SLH_APP` exists (React Native); bot connection not verified

- [x] **Cross-bot economy** — 5-token economy (SLH/MNH/ZVK/REP/ZUZ) live across 24 bots sharing PostgreSQL

---

## For New Developers / למפתחים חדשים

**📘 See [PROJECT_GUIDE.md](PROJECT_GUIDE.md)** — full onboarding for humans + AI agents.

### Quick Start / התחלה מהירה

1. **Read project map first:** `D:\SLH_ECOSYSTEM\PROJECT_MAP.md`
2. **Start Docker services:**
   ```bash
   cd D:\SLH_ECOSYSTEM && docker compose up -d
   ```
3. **Verify:** `docker ps --format "table {{.Names}}\t{{.Status}}"`
4. **Website deploy:** `cd D:\SLH_ECOSYSTEM\website && git push origin main`
5. **API deploy:** `cd D:\SLH_ECOSYSTEM && git push origin master`

### Key URLs
| Service | URL |
|---------|-----|
| Website | https://slh-nft.com |
| API | https://slh-api-production.up.railway.app |
| API Health | https://slh-api-production.up.railway.app/api/health |
| API Docs | https://slh-api-production.up.railway.app/docs |

### Architecture Snapshot (verified 2026-04-18)
- **24 Docker containers** — 22 Telegram bots + PostgreSQL + Redis
- **83 website pages** — GitHub Pages at slh-nft.com
- **230 API endpoints** — FastAPI v1.1.0 on Railway
- **25+ environment variables** — `.env` at project root
- **Blockchain:** TON (primary payments) + BSC (SLH BEP-20 token)

---

*Last updated: 2026-04-18 (verified) | Update this file as tasks are completed.*
