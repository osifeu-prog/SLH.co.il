# SLH Ecosystem — Major Upgrade Plan
## Full Scan Results + Prioritized Action Plan
### Date: 12 April 2026

---

## SCAN SUMMARY

| Scan Area | Files | Findings |
|-----------|-------|----------|
| HTML Pages | 42 | 5 CRITICAL, 8 HIGH, 12 MEDIUM |
| JS/CSS | 7 files | Clean architecture, minor improvements |
| API | 91 endpoints, 4600-line main.py | 4 CRITICAL, 5 HIGH, 6 MEDIUM |
| Infrastructure | 25+ bots, Docker, 2 repos | SLH_PROJECT_V2 conflict, mobile incomplete |

---

## PHASE 0: SECURITY EMERGENCY (Do First — 1-2 Hours)

### SEC-1: Remove Admin Passwords from Public HTML
**Files:** broadcast-composer.html, ecosystem-guide.html
**Passwords exposed:** slh2026admin, slh_admin_2026, slh-spark-admin, slh-institutional
**Action:** Remove all hardcoded passwords, replace with server-side auth check

### SEC-2: Protect Tokenomics Endpoints (API)
**Endpoints with NO AUTH:**
- `POST /api/tokenomics/burn` — anyone can burn tokens
- `POST /api/tokenomics/reserves/add` — anyone can fake reserves
- `POST /api/tokenomics/internal-transfer` — anyone can transfer tokens
**Action:** Add admin_key or JWT auth to all 3 endpoints

### SEC-3: Override Default Secrets on Railway
**Must set:**
- `JWT_SECRET` (currently empty — auth is broken without it)
- `ADMIN_API_KEYS` (override the 4 defaults)
- `ADMIN_BROADCAST_KEY` (override default)
- `BOT_SYNC_SECRET` (override default)
- `BITQUERY_API_KEY` (currently dummy "1123123")

### SEC-4: Fix Wallet Address
**Current:** 0xd061de73B06d5E91bfA46b35EfB7B08b16903da4
**Found in 5 HTML files + API main.py (COMPANY_BSC_WALLET)**
**Action:** User must confirm correct address. Update everywhere simultaneously.

---

## PHASE 1: LAUNCH-EVENT UPGRADE (2-3 Hours)

### 1A: Remove BNB Limits + Change to OPEN
- [x] Remove "maximum 0.05 BNB" from UI (DONE locally)
- [x] Change FILLED → OPEN status (DONE locally)
- [x] Remove max attribute from form input (DONE locally)
- [ ] Update API: remove any server-side max validation
- [ ] Update BNB price from hardcoded $608 to live CoinGecko feed

### 1B: Add PancakeSwap Liquidity Button
Replace the "send BNB to wallet" workflow with direct PancakeSwap integration:
- Add "Add Liquidity" button linking to PancakeSwap V2 Add Liquidity page
- SLH/BNB pair: use router contract
- Keep the manual contribution form as alternative for users without wallets
- Add Swap widget embed (PancakeSwap iframe or direct link)

### 1C: Multi-Token Contribution Support
Add support for contributing with:
- BNB (existing)
- USDT (BEP-20) — PancakeSwap auto-routes through BNB
- BUSD (BEP-20) — same routing
- Add dropdown selector to contribution form
- Show equivalent BNB value using live prices

---

## PHASE 2: REFERRAL FIX + STATS (1 Hour)

### 2A: Fix ref_User → Real Telegram ID
- [x] referral.html: use `user.id` instead of `user.username` (DONE locally)
- [x] Update placeholder to show Telegram ID format (DONE locally)
- [ ] API /api/referral/link/{user_id} already returns correct format
- [ ] Verify deep links actually work in Telegram bots (start=ref_{id})

### 2B: Live Referral Stats
- Connect stats section to `/api/referral/stats/{user_id}`
- Show: direct referrals, network size, total earned
- Add mini referral tree visualization (3 levels)

---

## PHASE 3: NAVIGATION CONSISTENCY (1-2 Hours)

### 3A: Add Missing Nav Elements
- [x] roadmap.html — added topnav-root, bottomnav-root, footer-root (DONE)
- [x] daily-blog.html — added bottomnav-root, footer-root (DONE)
- [x] getting-started.html — added bottomnav-root (DONE)
- [x] onboarding.html — added footer-root, bottomnav-root (DONE)
- [x] invite.html — added footer-root (DONE)
- [ ] partner-launch-invite.html — add topnav-root, bottomnav-root, footer-root + shared.js
- [ ] broadcast-composer.html — add nav (or mark as admin-only with auth gate)

### 3B: Verify initShared() Params
Ensure every page calls initShared() with correct activePage for highlighting.

---

## PHASE 4: BLOCKCHAIN PAGE (2-3 Hours)

### 4A: Real Transaction Data
- Connect to BSCScan API (free tier: 5 calls/sec)
- Fetch SLH token transfers: `?module=account&action=tokentx&contractaddress=0xACb0A09414CEA1C879c67bB7A877E4e19480f022`
- Display: recent transfers, amounts, from/to addresses, timestamps
- Link each TX to BSCScan explorer

### 4B: Charts with Real Data
- Replace empty charts with Chart.js
- Data sources: transfer volume over time, holder count, price history
- Add all 4 tokens: SLH, MNH, ZVK, REP

### 4C: Pool Statistics
- PancakeSwap pool address: 0xacea26b6e132cd45f2b8a4754170d4d0d3b8bbee
- Show: total liquidity, 24h volume, SLH price from pool
- Use PancakeSwap subgraph or direct BSC RPC calls

---

## PHASE 5: COMMUNITY IMAGE UPLOAD (1-2 Hours)

### 5A: Fix Image Persistence
- Frontend: file → canvas resize (max 800px) → base64
- API: POST /api/community/posts with image_data field
- Store base64 in database (small images) or upload to external CDN
- Display in feed with lazy loading

---

## PHASE 6: WALLET CEX CONNECTION (1 Hour)

### 6A: API Key Connection Guide
- wallet.html already has CEX Portfolio section
- Add step-by-step modal: "How to get your Bybit API key"
- Screenshots/instructions for Bybit V5 and Binance V3
- Emphasize: read-only permissions, no withdrawal access
- After key entry: auto-sync portfolio display

---

## PHASE 7: P2P ORDER BOOK (3-4 Hours)

### 7A: Backend Endpoints (Already exist)
- POST /api/p2p/create-order
- GET /api/p2p/orders
- POST /api/p2p/fill-order
- DELETE /api/p2p/cancel-order/{order_id}

### 7B: Frontend Activation
- p2p.html: replace "Coming Soon" with live order book
- Show buy/sell orders with price, amount, user
- Add create order form (token, side, price, amount)
- Add fill/cancel buttons with confirmation

---

## PHASE 8: I18N + THEME EXPANSION (2-3 Hours)

### 8A: Theme Switcher on All Pages
**Missing on:** jubilee, p2p, member, for-therapists, launch-event, partner-*, morning-*
- Pattern: FAB button at bottom:94px, 7 themes from shared.css
- Copy from guides.html implementation

### 8B: i18n on New Pages (5 Languages)
**Hebrew-only pages:** jubilee, healing-vision, for-therapists, p2p, member
- Add data-i18n attributes to all text elements
- Add translation keys to translations.js
- Priority: healing-vision + for-therapists (public-facing)

---

## PHASE 9: EFFECTIVENESS BOOSTERS (3-5 Hours)

### 9A: Embedded Swap Widget
- Add PancakeSwap swap widget to launch-event.html and trade.html
- Direct link: `https://pancakeswap.finance/swap?outputCurrency=0xACb0A09414CEA1C879c67bB7A877E4e19480f022&chain=bsc`
- Consider embedding via iframe for seamless UX

### 9B: Referral Bonus on Liquidity
- New API endpoint: POST /api/referral/lp-bonus
- When user adds liquidity → referrer gets ZVK bonus
- Track via BSC event logs or manual reporting

### 9C: LP Staking Rewards
- New staking plan: "LP Token Staking"
- Users lock PancakeSwap LP tokens → earn ZVK/REP
- Higher APY than regular staking (incentivize liquidity)

### 9D: Fiat On-Ramp
- Integrate MoonPay or Transak widget
- User buys BNB with credit card → swaps to SLH
- Requires KYB/partnership setup (longer term)

---

## PHASE 10: INFRASTRUCTURE (Ongoing)

### 10A: SLH_PROJECT_V2 Consolidation
- Audit which services run from V2 vs ECOSYSTEM
- Resolve NFTY token conflict
- Either merge into single deployment or formally document split

### 10B: Database Migrations
- Create /api/migrations/ folder
- Track all schema changes properly
- Current: inline schema in main.py

### 10C: API Refactoring
- Split main.py (4600 lines!) into route modules:
  - routes/auth.py, routes/wallet.py, routes/referral.py, etc.
- Add proper Pydantic models for all request/response types
- Add Redis for caching (currently in-memory only)

### 10D: Testing
- No test coverage currently
- Add: auth flow tests, wallet transfer tests, referral commission tests
- At minimum: smoke tests for all 91 endpoints

---

## PHASE 11: GROWTH (Week 2+)

| Item | Effort | Priority |
|------|--------|----------|
| LP Lock on Mudra | 2h | P3 |
| Trust Wallet logo PR | 1h | P3 |
| GemPad Presale Round 2 | 4h | P3 |
| Webhook migration (polling → webhooks) | 8h | P3 |
| Strategy Engine live execution | 8h | P3 |
| MEXC/Gate.io listing | 16h+ | P4 |
| Mobile app (React Native) | 40h+ | P4 |
| CertiK audit ($5K-$15K) | External | P4 |

---

## EXECUTION ORDER (Recommended)

```
Session 1 (NOW):
  → Phase 0: Security fixes (passwords, auth, wallet address)
  → Push all P0 changes to GitHub
  → Phase 1A: Launch-event already done, push

Session 2 (Next):
  → Phase 1B-1C: Liquidity button + multi-token
  → Phase 4: Blockchain page real data
  → Phase 5: Community image upload

Session 3:
  → Phase 7: P2P activation
  → Phase 8: i18n + themes
  → Phase 9A-9B: Swap widget + referral LP bonus

Session 4:
  → Phase 9C-9D: LP staking + fiat on-ramp
  → Phase 10: Infrastructure cleanup
  → Phase 11: Growth items
```

---

## KEY METRICS TO TRACK

| Metric | Current | Target |
|--------|---------|--------|
| Pages with nav | 38/42 | 42/42 |
| Pages with i18n | 22/42 | 42/42 |
| Pages with theme | ~25/42 | 42/42 |
| API endpoints with auth | ~10/91 | All sensitive |
| Test coverage | 0% | 50%+ |
| Security issues | 9 CRITICAL+HIGH | 0 |
| Pool liquidity | 0.06 BNB | 1+ BNB |
| Active users | ~4 | 50+ |
