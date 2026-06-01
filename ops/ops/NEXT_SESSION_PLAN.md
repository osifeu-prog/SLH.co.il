# SLH Ecosystem — Full Session Handoff (2026-04-13)

> Use this document to brief the next Claude Code session.
> It contains EVERYTHING done across sessions + what remains.

---

## 1. PROJECT OVERVIEW

- **Owner:** Osif (Telegram ID 224223270, @osifeu_prog)
- **Stack:** FastAPI on Railway (asyncpg PostgreSQL), GitHub Pages static site (slh-nft.com), 25+ Telegram bots (aiogram 3.26 / python-telegram-bot), Docker Compose (23 containers)
- **Languages:** Hebrew primary UI, i18n for EN/RU/AR/FR
- **Tokens:** SLH on BSC (0xACb0A09414CEA1C879c67bB7A877E4e19480f022), ZVK (internal), MEAH, TON
- **TON wallet:** UQCr743gEr_nqV_0SBkSp3CtYS_15R3LDLBvLmKeEv7XdGvp
- **Key URLs:** https://slh-nft.com, https://slh-api-production.up.railway.app
- **CRITICAL:** Railway builds from ROOT main.py. Always sync: `cp api/main.py main.py`

---

## 2. COMPLETED WORK (all sessions combined)

### Session 1 (2026-04-09): Critical fixes

| # | Task | Files Changed |
|---|------|--------------|
| 1 | Fixed `@osifeu` broken links site-wide | index.html, dashboard.html, privacy.html, terms.html — replaced with `@osifeu_prog` + `@TON_MNH_bot` |
| 2 | Fixed dashboard `#undefined` user ID bug | dashboard.html — added sanitization in `showApp()`, expanded deep-link login params (tgid, first_name, username, photo), localStorage session validation |
| 3 | Fixed i18n raw keys showing on pages | js/shared.js — `t()` now accepts fallback param, `setLang()` preserves original text via `dataset.i18nOrig`, `hasT()` helper added |
| 4 | Styled community date widget | community.html — glass morphism CSS via `renderDateWidget()` in shared.js with injected styles |
| 5 | Added multi-gen referral explainer | staking.html — educational box with tree icon, cascade example (Yossi -> Dana -> Ron), 3 info cards, tip box |
| 6 | Promoted roadmap/guides/blog to main nav | js/shared.js — added `blog`, `guides`, `wallet_guide` to `NAV_ITEMS` array |
| 7 | Restructured bots.html | bots.html — grouped by category (Financial/SaaS/Community/Gaming/Security), status tiers (LIVE/BETA/WIP/SOON), updated COMING_SOON |
| 8 | Created security doc | ops/SECURITY_TOKEN_ROTATION.md — 20-bot rotation checklist |
| 9 | Created 4-sprint work plan | ops/WORK_PLAN_2026-04.md — Sprint 1-4 covering Apr 9 to May 3 |
| 10 | Created daily blog system | ops/DAILY_BLOG.md + website/daily-blog.html — Hebrew blog with date badges, sections |
| 11 | Created Web3 plan doc | ops/WEB3_WALLET_PLAN.md — full implementation plan |
| 12 | Created js/web3.js module | website/js/web3.js — ethers.js v6, MetaMask/Trust Wallet connect, BSC+ETH balance reads, auto-reconnect, account switch listener |

### Session 2 (2026-04-13): Web3 wiring end-to-end

| # | Task | Files Changed |
|---|------|--------------|
| 13 | Wired Web3 panel into dashboard.html | dashboard.html — ethers.js v6 CDN in `<head>`, Web3 panel CSS (`.web3-panel`, `.web3-card`, `.btn-web3-connect`, `.web3-balance-grid`, token-colored borders), HTML panel between referral cards and recent activity section with IDs: `btn-connect-wallet`, `web3-status`, `web3-balances`, `web3-addr-short`, `w3-slh`, `w3-bnb`, `w3-eth`, `w3-usdt`, `btn-disconnect-wallet`. Added `<script src="/js/web3.js?v=20260409a">` before `</body>`. Bumped all version strings to `20260409a`. |
| 14 | Wired Web3 panel into wallet.html | wallet.html — ethers.js CDN, same Web3 CSS block, replaced empty `<div id="wallet-connect-section">` with full panel HTML (uses FontAwesome icons instead of emoji for consistency with wallet page design), added web3.js script tag after shared.js |
| 15 | Added link-wallet API endpoints | api/main.py — 3 new endpoints: `POST /api/user/link-wallet` (validates 0x+40 hex, prevents same wallet on 2 accounts, stores lowercase), `GET /api/user/wallet/{user_id}` (returns address + linked_at), `POST /api/user/unlink-wallet` (nulls the columns). Uses `LinkWalletRequest(BaseModel)` with optional `address`, `signature`, `message` fields. |
| 16 | Added DB migration for wallet columns | api/main.py CREATE TABLE — added `eth_wallet VARCHAR(42)`, `eth_wallet_linked_at TIMESTAMP`, `ton_wallet VARCHAR(68)`, `ton_wallet_linked_at TIMESTAMP`. Auto-migration block with `ALTER TABLE IF NOT EXISTS` + partial indexes (`idx_web_users_eth_wallet`, `idx_web_users_ton_wallet`). Standalone SQL: `ops/migrations/20260409_web3_wallet.sql` |
| 17 | Added Web3 i18n translations | js/translations.js — 7 keys added to all 5 language blocks: `web3_title`, `web3_sub`, `web3_connect`, `web3_disconnect`, `web3_hint`, `web3_connected`, `web3_no_wallet` |
| 18 | Improved web3.js cross-page compat | js/web3.js — added `_getUser()` helper that tries `currentUser` (dashboard global) then `getCurrentUser()` (shared.js function), so link-wallet API call works on both pages. Improved `connectWallet()` with toast feedback (short address). `disconnectWallet()` now calls `/api/user/unlink-wallet` server-side. |
| 19 | Updated daily blog | ops/DAILY_BLOG.md — new "2026-04-09 (evening)" entry. website/daily-blog.html — new article at top with Hebrew details of Web3 wiring. |

### Validation
All files syntax-checked and clean:
- `node -c website/js/web3.js` — OK
- `node -c website/js/translations.js` — OK
- `node -c website/js/shared.js` — OK
- `python ast.parse(api/main.py)` — OK

---

## 3. PENDING ITEMS (priority order)

### P0 — NFTY Tamagotchi bot BROKEN (user escalation)

**Symptom:** As of 09/04/2026 12:30, all Hebrew text from @NFTY_madness_bot is garbled with braille-like unicode (⠢⢢⬡⬝⢢...). Additionally the bot appears to have MERGED with a different bot — it shows "SLH NFT Marketplace | SPARK IND" header and marketplace commands (/activate, /browse, /sell, /buy) instead of pet commands.

**Timeline:**
- 08/04 23:16 — bot working perfectly, Hebrew displays fine
- 09/04 12:30 — completely broken, garbled text + wrong bot identity

**Investigation needed:**
1. Find NFTY bot source code (likely `D:\SLH_ECOSYSTEM\nfty\` or similar)
2. Check if wrong `main.py` was deployed to the NFTY container (marketplace code instead of tamagotchi)
3. Check if bot token was swapped between NFTY and another bot
4. Fix Hebrew encoding (likely file saved as wrong encoding)
5. Test all commands: /start, /feed, /play, /heal, /sleep, /guess, /report, /shop, /teach, /cuteness, /leaderboard, /longevity

**Additional NFTY bugs (from when it WAS working 08/04):**
- Inline buttons trigger "תתחיל קודם ב /start" even when pet exists
- `/teach`, `/cuteness` sometimes return leaderboard output
- `OPENAI_API_KEY` not being read (needs Railway env var, NOT chat input)
- cuteness_battle invitations never resolve
- Pet stuck at "egg" stage forever
- Energy never recovers (always 12/100)

### P1 — Auto-registration bot <-> website sync
- Bot `/start` should auto-create user in `web_users` table
- Remove screenshot requirement for payment
- Auto-detect TON transfers to ecosystem wallet

### P1 — Remove hard-coded SLH price
- `SLH_PRICE_ILS = 444` in shared.js:13
- Should come from dynamic P2P pricing

### P2 — Mobile responsive fix
- User reports layout breaks on mobile
- Needs viewport audit on dashboard, wallet, community, all pages

### P2 — Community posting system
- Users cannot post to community.html
- Need: text posts, image uploads, file attachments
- Foundation for course marketplace + digital goods

### P2 — Accessibility (WCAG)
- Skip-nav links, ARIA labels, contrast ratios, font scaling
- User says this is both regulatory and personal priority

### P2 — Fear & Greed Index
- Shows "14" with no context
- Need tooltip explaining 0-100 scale + what the number means

### P3 — Restore crypto charts
- Mini sparkline charts next to balance cards (existed before, removed)
- Consider cross-coin comparison tools

### P3 — blockchain.html real data
- Currently "Loading blockchain data..."
- Wire BSCScan + TONScan APIs

### P3 — Facebook landing popup
- Quick-join popup for visitors from Facebook ads
- Match promises in the ad (22.221 ILS registration)

### P3 — Course marketplace
- Upload/buy courses (150 ILS), sample course
- Depends on community posting infrastructure

### P3 — Website animations & visual polish
- More animations, images, graphs to make site feel alive

### P3 — 7 themes on remaining pages
- guides.html, wallet-guide.html, roadmap.html need theme CSS

### P4 — Facebook/YouTube feed in dashboard
### P4 — Telegram push notifications
### P4 — Real-time chat (WebSocket) in community
### P4 — Token batch update admin panel
### P4 — TonConnect (Web3 panel is EVM-only today)
### P4 — Wallet ownership proof via signature (for P2P)
### P4 — Webhook migration (polling -> webhooks for all bots)
### P4 — Rotate all 20+ bot tokens via @BotFather

---

## 4. KEY ARCHITECTURE NOTES

### API (api/main.py)
- FastAPI with asyncpg connection pool
- JWT auth with Bearer headers (`create_jwt()`, `get_current_user_id()`)
- `apiPost()` / `apiGet()` in shared.js use `API_BASE = 'https://slh-api-production.up.railway.app'`
- Tables auto-created on startup, migrations via ALTER TABLE IF NOT EXISTS
- 10-generation referral commission system (5%, 3%, 2%, 1.5%, 1%, 0.75%, 0.5%, 0.5%, 0.25%, 0.25%)

### Website (GitHub Pages)
- Vanilla JS, no build step, no framework
- i18n via `data-i18n` attributes + `T[lang][key]` object in translations.js
- 7 theme system via CSS custom properties on `[data-theme]`
- `initShared()` renders nav, footer, ticker, calls `setLang()` twice (before and after DOM inject)
- PWA support (manifest.json + sw.js)
- `getCurrentUser()` reads from localStorage (`slh_user`)
- Dashboard uses global `let currentUser` while other pages use `getCurrentUser()`

### Web3 Module (js/web3.js)
- IIFE wrapping, exposes `window.SLHWeb3` with: connect, disconnect, sign, getBSCBalance, getBSCNative, getETH, getTON
- Constants: `SLH_CONTRACT_BSC`, `USDT_CONTRACT_BSC`
- Auto-init via `DOMContentLoaded` → `initWeb3UI()`
- Requires elements: `btn-connect-wallet`, `btn-disconnect-wallet`, `web3-status`, `web3-balances`, `web3-addr-short`, `w3-slh`, `w3-bnb`, `w3-eth`, `w3-usdt`
- Calls `apiPost('/api/user/link-wallet', ...)` on connect, `apiPost('/api/user/unlink-wallet', ...)` on disconnect

---

## 5. FILE LOCATIONS

```
D:\SLH_ECOSYSTEM\
├── api\main.py                    # FastAPI backend (~800+ lines)
├── main.py                        # ROOT COPY for Railway (must sync!)
├── website\                       # GitHub Pages static site
│   ├── dashboard.html             # ~2850 lines, main user dashboard
│   ├── wallet.html                # ~870 lines, wallet + Web3 panel
│   ├── community.html
│   ├── staking.html               # Has multi-gen referral explainer
│   ├── bots.html                  # Restructured with status tiers
│   ├── daily-blog.html            # Public Hebrew changelog
│   ├── blockchain.html            # Needs real data
│   ├── js\shared.js               # Core module (~930 lines)
│   ├── js\translations.js         # i18n strings (~1800 lines, 5 langs)
│   ├── js\web3.js                 # Web3 wallet module (~240 lines)
│   ├── js\web3-wallet.js          # Older wallet-specific JS (wallet.html)
│   ├── js\analytics.js
│   ├── js\ai-assistant.js
│   └── css\shared.css
├── ops\
│   ├── DAILY_BLOG.md              # Changelog source
│   ├── WORK_PLAN_2026-04.md       # 4-sprint plan
│   ├── WEB3_WALLET_PLAN.md        # Web3 plan
│   ├── SECURITY_TOKEN_ROTATION.md # Token rotation checklist
│   └── migrations\
│       └── 20260409_web3_wallet.sql
├── nfty\                          # NFTY Tamagotchi bot (BROKEN)
├── wallet\
│   └── sql\schema_full.sql, schema_patch.sql
├── docker-compose.yml             # 23 containers
└── .env                           # Bot tokens (DO NOT COMMIT)
```

---

## 6. USER PREFERENCES

- **Hebrew always** in UI text
- **Direct action** — don't explain, just do
- **Don't minimize scope** — user knows system is massive
- **Never fake data** — use real API or label as `[DEMO]`
- **Don't ask unnecessary questions** — "כן לכל ההצעות" means proceed
- User exposed an OpenAI API key in Telegram chat — it needs to be set as a Railway env var for the NFTY bot, NOT typed into chat
- User pasted Anthropic usage policy in confusion — NOT blocked, just confused by a previous session's behavior. Reassure if asked.
