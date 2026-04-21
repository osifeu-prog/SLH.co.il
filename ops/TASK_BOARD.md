# SLH Task Board — Sprint 2026-04
> Single source of truth for all tasks
> Last updated: 2026-04-21 Night Late (chain events closeout)

---

## COMPLETED IN SESSION (21 April 2026 evening)

### Chain Events Closeout
- [x] `GET /api/admin/events` endpoint — ring buffer over event_log with cursor + types filter + 24h breakdown (commit `192e12e`)
- [x] `chain-status.html` — Events panel renders 20 latest events; Ledger day card reads events/24h (commit `251195a`)
- [x] Deleted toy `device-registry/main.py` — Railway endpoints authoritative, README + ESP_QUICKSTART updated
- [x] Wired `chain-status.html` into admin.html sidebar (System section) and ops-dashboard.html header
- [x] API docs updated — `ops/ENDPOINTS_TEST_GUIDE.md` sections 7 (admin events + link-phone-tg) and new 7b (device chain full flow)
- [x] Memory + handoff — `project_night_20260421_late.md` + `SESSION_HANDOFF_20260421_LATE.md`

---

---

## COMPLETED IN SESSION 12 (14 April 2026)

### New Features
- [x] **SLH Control Center** — 8-tab monitoring dashboard (control-center.html)
- [x] **Bank Transfer System** — 8-field form + 4 API endpoints + admin management
- [x] **Admin CRM Upgrade** — 9 columns, search, filters, credit/approve actions
- [x] **Admin Finance Dashboard** — 6 KPIs, contributors table, tokenomics
- [x] **Admin Trust Network** — 4 KPIs, Guardian reports table
- [x] **BOT_REGISTRY.md** — single source of truth for all 23 bots

### Fixes
- [x] NFTY bot Hebrew encoding — 137 lines of braille replaced with proper Hebrew
- [x] Dashboard #undefined — API fetch before showApp() for URL params
- [x] terms.html price — 44.4 → 22.221 ILS
- [x] roadmap.html — added analytics.js
- [x] rotate.html — added shared.css

### Security
- [x] Removed hardcoded admin passwords from admin.html (ADMIN_PASSWORDS array)
- [x] Deleted admin-test.html login bypass page
- [x] Removed password fallbacks from ops-dashboard, control-center
- [x] Tokenomics endpoints verified secure (burn/reserves/transfer all require admin auth)

### Docker/Infrastructure
- [x] Removed dummy bots: selha-bot, userinfo-bot (token collision)
- [x] ExpertNet disabled as LEGACY (token collision with selha)
- [x] Railway secrets generated (waiting for user to set)
- [x] Full system audit: API (137 endpoints), 49 pages, 27 containers

---

## COMPLETED IN PREVIOUS SESSIONS (Sessions 4-11)

- [x] Website V3 (4 languages, 12 bots, live ticker) — Session 6
- [x] Docker 22 containers online — Session 6
- [x] ExpertNet: 12 coins, banking, staking — Session 5
- [x] OsifShop: barcode scanner, inventory — Session 5
- [x] slh-nft.com launched on GitHub Pages — Session 4
- [x] PancakeSwap pool created — Session 8
- [x] Genesis Launch live — Session 8
- [x] Guardian ZUZ system — Session 10
- [x] Multi-staking plans — Session 10
- [x] Risk engine endpoints — Session 10
- [x] P2P marketplace LIVE — Session 11
- [x] Buy SLH page (6 payment methods) — Session 11
- [x] Challenge Day 3 Vipassana — Session 11
- [x] 22 premium OG images — Session 11
- [x] 17 broadcasts (100% delivery) — Session 11

---

## PENDING — P0 Critical

- [ ] **Railway secrets** — JWT_SECRET, ADMIN_API_KEYS, ADMIN_BROADCAST_KEY (USER ACTION: set in Railway UI)
- [ ] **Token rotation** — 31 bot tokens exposed in chat (USER ACTION: @BotFather /revoke)
- [ ] **Wallet address confirmation** — 2 addresses found: 0xd061... vs 0xD061... (USER: confirm which)

## PENDING — P1 High Impact

### Payment & Admin System
- [ ] **Multi-admin system** — admin_users table exists, needs login endpoints + bcrypt (Phase 1B)
- [ ] **User payment profiles** — bank/Bit/PayBox in dashboard (Phase 1C)
- [ ] **Digital invoice system** — receipts for bank transfers (Phase 2)
- [ ] **Broker role for Elazar** — not registered yet
- [ ] **Course upload for Yaara** — not registered yet

### Website
- [ ] **SLH Docs Layout** — MS-Learn/Stripe-Docs style 3-col layout (left tree / content / right TOC) with auto-scroll-spy, breadcrumbs, feedback widget, dynamic manifest. Spec: `ops/SLH_DOCS_LAYOUT_SPEC.md`. Rollout to 10 content pages. Effort: 18h total, 4h foundation. (Requested 2026-04-18)
- [ ] **blockchain.html real data** — BSCScan + TONScan APIs
- [ ] **Mobile responsive audit** — dashboard, wallet, community break on mobile
- [ ] **Web3 on-chain balances** — MetaMask/Trust Wallet show real SLH balance
- [ ] **Launch-event** — remove BNB limits, change FILLED→OPEN, live BNB price
- [ ] **Referral live stats** — connect to API, mini tree visualization
- [ ] **Course marketplace** — 150 ILS upload/buy, sample course

### Bots
- [ ] **Guardian → ZUZ API** — /report and /check commands
- [ ] **Bot /commands** — set commands for 12+ bots via @BotFather
- [ ] **Wallet bot** — fix localhost URLs → slh-nft.com
- [ ] **Factory bot** — fix Redis connection error
- [ ] **Fun bot** — fix InputFile abstract class error
- [ ] **TON_MNH** — fix `tasklist` → `ps aux` for Linux Docker
- [ ] **Auto-sync BSC → DB** — deposit watcher for on-chain transfers
- [ ] **Trust Level gamification** — REP tiers, achievements

## PENDING — P2 Improvements

- [ ] Theme switcher on 26+ pages
- [ ] i18n on 28+ pages
- [ ] Bot translations (HE/EN/RU/AR/FR)
- [ ] LP Lock on Mudra
- [ ] Matrix/bubbles visual effects
- [ ] Sparkline charts in dashboard
- [ ] Facebook landing popup
- [ ] PWA polish (install prompt, offline)
- [ ] Staking referral tree visualization
- [ ] Fear & Greed tooltip
- [ ] Community posting system (text + images)
- [ ] Accessibility audit (WCAG)

## PENDING — P3 Infrastructure

- [ ] Split main.py (7475 lines → route modules)
- [ ] Webhook migration (polling → webhooks, 8h)
- [ ] Redis caching layer
- [ ] Test coverage (0% → 50%+)
- [ ] Database migration system
- [ ] SLH_PROJECT_V2 consolidation

## PENDING — P4 Long-term

- [ ] Fiat on-ramp (MoonPay/Transak)
- [ ] LP Lock on Mudra
- [ ] Trust Wallet logo PR
- [ ] MEXC/Gate.io listing
- [ ] Mobile app (React Native)
- [ ] CertiK audit ($5K-$15K)
- [ ] TonConnect integration
- [ ] Facebook/YouTube feed in dashboard
- [ ] Real-time chat (WebSocket)
- [ ] Token batch update admin panel

## USER ACTIONS REQUIRED

1. Set Railway secrets (JWT_SECRET, ADMIN_API_KEYS, ADMIN_BROADCAST_KEY)
2. Rotate bot tokens via @BotFather
3. Confirm wallet address (0xd061... vs 0xD061...)
4. Create Facebook App at developers.facebook.com
5. Register Elazar + Yaara in system
6. Reconnect ESP32 for Ledger bot
