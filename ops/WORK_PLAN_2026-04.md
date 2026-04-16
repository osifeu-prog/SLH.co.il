# 📋 SLH Work Plan — April 2026

> Created: 2026-04-09
> Owner: Osif
> Purpose: Structured roadmap covering all critical fixes + features requested
> in the post-reboot system review. Updated daily via `/daily-blog.html`.

## Priority legend

- 🔴 **P0** — Blocks users from registering / trading / using the product
- 🟠 **P1** — Degraded experience, clear bug, visible to users
- 🟡 **P2** — Feature expansion, new capability
- 🟢 **P3** — Polish, nice-to-have, internal

## 🎯 North Star

Within 2 weeks, a new user should be able to:
1. Visit slh-nft.com
2. Register with Telegram (auto-sync with bot)
3. Pay entry fee in TON
4. See REAL on-chain balances (BSC + TON + ETH)
5. List tokens for sale at their own price (P2P)
6. Purchase extended access via courses
7. Use the wallet, community, staking, referral pages freely

---

## Sprint 1 — Critical Fixes (2026-04-09 → 2026-04-11)

All completed items move to `DAILY_BLOG.md` automatically.

### 🔴 P0 — Infrastructure

- [x] **Rotate all bot tokens** — SECURITY_TOKEN_ROTATION.md created; user must execute
- [x] **Fix `#undefined` dashboard user ID** — Sanitize session on load, validate saved slh_user
- [x] **Fix guides.html raw i18n keys** — Modified setLang to preserve original text when key missing
- [x] **Fix footer raw i18n keys** — Same fix + added fallback in renderFooter
- [x] **Replace @osifeu broken link** — Replaced with @osifeu_prog and @TON_MNH_bot across 4 pages
- [x] **Fix community date widget styling** — Themed widget with glass blur, gradient, hover
- [ ] **Auto-registration bot ↔ website sync** — Bot should POST to /api/auth/telegram-sync when user starts

### 🟠 P1 — Dashboard & core pages

- [ ] **MetaMask / Trust Wallet Web3 integration**
  - Add ethers.js CDN to dashboard.html
  - "Connect Wallet" button in header
  - Read SLH balance from BSC contract `0xACb0A09414CEA1C879c67bB7A877E4e19480f022`
  - Read TON balance from TON HTTP API
  - Display real + internal balances side-by-side
- [ ] **Remove hard-coded SLH price (444 ILS)** — Let users list at their own price
- [ ] **Roadmap/Guides/Wallet-guide prominent in top nav** — Not just footer
- [ ] **Ensure 7 themes work on guides.html, wallet-guide.html, roadmap.html** — Add `.theme-*` CSS hooks

### 🟡 P2 — New features

- [ ] **Course marketplace** — Upload/buy digital courses (150 ILS one-time)
  - DB: `courses (id, author_id, title, description, price, file_url, thumbnail, status)`
  - API: POST /api/courses/upload, GET /api/courses, POST /api/courses/buy
  - Page: `/courses.html` with grid + detail view
- [ ] **Sample course seed** — "SLH Ecosystem: Complete Guide" as working example
- [ ] **Daily blog page** — `/daily-blog.html` auto-generated from DAILY_BLOG.md
- [ ] **Facebook feed integration** — User's FB pages shown in personal dashboard area
- [ ] **YouTube feed integration** — User's YT channels shown in personal dashboard area
- [ ] **Token batch update mechanism** — Admin panel to edit ALL token definitions in one form

---

## Sprint 2 — Bot Maximization (2026-04-12 → 2026-04-19)

Each bot gets individual attention. Grouped by impact:

### Week 1 bots (high traffic)

- [ ] **@SLH_AIR_bot** (main) — Add P2P trading, expand funnel, connect all sub-bots via deep-link
- [ ] **@NFTY_madness_bot** (tamagotchi) — Fix /shop /report /guess, add OPENAI_API_KEY, IDs in leaderboard
- [ ] **@OsifShop_bot** — Restore inventory management, add course/album categories
- [ ] **@Buy_My_Shop_bot** — Restore NFT marketplace code, Shopify-style product grid
- [ ] **@SLH_Academia_bot** — Full academy flow, translate to 5 languages
- [ ] **@Grdian_bot** — System-wide monitoring, remote support hooks

### Week 2 bots (medium traffic)

- [ ] **@TON_MNH_bot** — Max capabilities, connect to main ledger
- [ ] **@MY_SUPER_ADMIN_bot** — Fix broken bot-links, unified admin panel
- [ ] **@My_crazy_panel_bot** — Max capabilities, dashboard mirror
- [ ] **@SLH_Ledger_bot** — ESP32 integration (user will reconnect hardware)
- [ ] **@SLH_Wallet_bot** — Dedupe, single canonical wallet bot
- [ ] **@NIFTI_Publisher_Bot** (Wellness) — Expand wellness features, daily content
- [ ] **@MY_NFT_SHOP_bot** — Restore to functional marketplace
- [ ] **@G4meb0t_bot_bot** (matchmaking) — Connect to customer profiling

### Week 3 bots (niche)

- [ ] **@Chance_Pais_bot** → **Gambling Recovery Bot**
  - Transform from "chance game" to addiction-recovery tool
  - Features: CBT journaling, craving tracker, relapse analysis, peer support
  - Research-backed (behavioral science, psychology, math of odds)
- [ ] **@Osifs_Factory_bot** — Fix "Admin login requires Redis" error
- [ ] **@SLH_community_bot** — Clarify purpose, consolidate with community.html
- [ ] **@Campaign_SLH_bot** — Expand marketing/campaigns features
- [ ] **@Slh_selha_bot** — Assign purpose (suggestion: official FAQ / customer-support bot)
- [ ] **@SLH_ton_bot** — Add placeholder: "TON integration coming Q2 2026"

---

## Sprint 3 — Polish & i18n (2026-04-20 → 2026-04-26)

- [ ] **Translate all bots** — HE / EN / RU / AR / FR — add `lang/` dir per bot
- [ ] **Audit all page links** — Verify every link on bots.html, index.html, etc.
- [ ] **Add roadmap highlighting** — Prominent banner on homepage
- [ ] **Expand staking page** — Multi-generation referral visual explanation
  - "Every friend brings a friend → you earn % from their deposits across 10 generations"
  - Tree visualization, earnings calculator
- [ ] **Public wallet-guide** — Remove login gate, make discoverable
- [ ] **Bots page accuracy review** — Verify every bot link, description, status
- [ ] **PWA polish** — Install prompt on mobile, improve offline experience

---

## Sprint 4 — Revenue Engine (2026-04-27 → 2026-05-03)

- [ ] **Paid registration system** — Per plan in `C:\Users\Giga Store\.claude\plans\ethereal-frolicking-pie.md`
- [ ] **Course marketplace live** — Real courses, real purchases
- [ ] **Referral commissions flowing** — Verify 10-gen commissions on registration
- [ ] **Ecommerce marketplace in community** — Buy/sell within ecosystem
- [ ] **Real-time chat widget** — Community presence, Redis pub/sub
- [ ] **Telegram push notifications** — Replies, approvals, staking rewards

---

## Metrics to track

| Metric | Current | 2 weeks | 4 weeks |
|--------|---------|---------|---------|
| Registered users | ~30 | 100 | 300 |
| Bots operational | 20/23 | 23/23 | 23/23 |
| P0 bugs | 7 | 0 | 0 |
| Languages supported | 5 (UI) | 5 (all bots) | 5 (all bots) |
| Courses for sale | 0 | 1 | 5 |
| Avg user balance | 0 SLH | 0.1 SLH | 1 SLH |

---

## User-side actions needed

Tasks ONLY Osif can do — Claude cannot perform these:

1. [ ] **Rotate all bot tokens via @BotFather** (see SECURITY_TOKEN_ROTATION.md)
2. [ ] **Create Facebook App** at developers.facebook.com for feed integration
3. [ ] **Run `railway link`** in `D:\SLH_ECOSYSTEM\api\` to bind Railway CLI
4. [ ] **Set up Windows startup shortcut** (Win+R → shell:startup → slh-startup.bat)
5. [ ] **Reconnect ESP32** when scheduled for SLH_Ledger_bot integration
6. [ ] **Approve first test payments** via admin panel to verify registration flow

---

## Questions for Osif (blocking items)

- What should `@Slh_selha_bot` do? (currently unused)
- Should `@Chance_Pais_bot` keep its current flow OR pivot to gambling recovery? (user said: pivot)
- Which course should be the sample? (content ideas welcome)
- Facebook page IDs to display in dashboard?
- YouTube channel IDs to display in dashboard?

---

## Changelog

See `DAILY_BLOG.md` for daily progress.
