# 📰 SLH Daily Blog — What changed today?

> Auto-published to https://slh-nft.com/daily-blog.html
> Oldest entries at the bottom. Newest at the top.

---

## 2026-04-09 (evening) — Web3 wiring complete

**Today's theme:** Customers now see REAL on-chain balances on dashboard and
wallet pages. This is the foundation of P2P trading: if users can't trust the
numbers, they won't trade.

### ✅ Shipped (this session)

- **Web3:** `js/web3.js` ethers.js v6 module — connect MetaMask / Trust Wallet,
  read balances from BSC (SLH, BNB, USDT) and Ethereum (ETH), auto-reconnect,
  react to account switching.
- **Dashboard:** Full Web3 panel between referral cards and recent activity —
  orange connect button, connected address chip, 4-token balance grid, colored
  token borders (SLH gold, BNB yellow, ETH purple, USDT green).
- **Wallet page:** Same Web3 panel right under the header, replacing the old
  empty placeholder.
- **API:** `POST /api/user/link-wallet`, `GET /api/user/wallet/{id}`, and
  `POST /api/user/unlink-wallet` endpoints — validates address format, prevents
  the same wallet being linked to two accounts, stores lowercase.
- **DB:** Auto-migration adds `eth_wallet`, `eth_wallet_linked_at`,
  `ton_wallet`, `ton_wallet_linked_at` columns to `web_users` with partial
  indexes. Also created standalone SQL in
  `ops/migrations/20260409_web3_wallet.sql` for manual runs.
- **i18n:** Web3 panel translations in all 5 languages (HE / EN / RU / AR / FR).
- **web3.js cross-page helper:** `_getUser()` now works on dashboard (global
  `currentUser`) AND wallet (`getCurrentUser()` from shared.js).

### 🚧 Still in progress

- TON wallet connection via TonConnect (Web3 panel only shows EVM chains today).
- Signature-based wallet ownership proof (for P2P listings).
- Auto-registration: bot `/start` syncs user into website DB automatically.
- Course marketplace.

### 📣 Coming up this week

- P2P marketplace UI (list your SLH at your own price, sign offer with wallet).
- Full rotation of the 20 exposed bot tokens via @BotFather.
- Real-time community chat (WebSocket).
- First sample course published for free to test the marketplace.

### 🔐 User action needed

- Rotate all ~20 bot tokens via @BotFather (see SECURITY_TOKEN_ROTATION.md).
- Test the new Web3 panel on dashboard.html → click "Connect Wallet" →
  verify real BSC + ETH balances show.
- Create a Facebook App for feed integration.

---

## 2026-04-09 — Post-reboot critical fixes

**Today's theme:** After a full system reboot and end-to-end test, we fixed the
most visible bugs users reported, started a structured work plan, and prepared
the infrastructure for the next phase.

### ✅ Shipped

- **Security:** Created `SECURITY_TOKEN_ROTATION.md` checklist — bot tokens must
  be rotated via @BotFather this week (exposed in chat).
- **Website:** Fixed `@osifeu` broken link across 4 pages (dashboard, index,
  privacy, terms) — now points to `@osifeu_prog` and `@TON_MNH_bot`.
- **Website:** Fixed the `#undefined` user ID bug on the dashboard. Sanitizes
  invalid sessions, handles deep-link login (`?uid=...`) with more parameters.
- **Website:** Fixed raw i18n keys (`nav_home`, `footer_rights`, etc.) showing
  on the guides page and others. The translation engine now preserves the
  original text when a translation is missing.
- **Website:** Beautified the community date/clock widget with a themed glass
  look (gradient, blur, hover lift) that blends into the page.
- **Website:** Multi-generation referral explainer added to staking page with
  a visual cascade example (Yossi → Dana → Ron).
- **Website:** Restructured `bots.html` — grouped by category, status tiers
  (LIVE / BETA / WIP / SOON), corrected bot descriptions and missing entries.
- **Ops:** Created `WORK_PLAN_2026-04.md` — 4-sprint structured plan covering
  critical fixes, Web3 integration, bot maximization, revenue engine.

### 🚧 In progress

- Web3 wallet connection (MetaMask / Trust Wallet) on the dashboard.
- Course marketplace schema + API endpoints.
- Daily blog page wired into the website.
- Roadmap / guides promoted to the main navigation.

### 📣 Coming up this week

- Auto-registration: bot `/start` will sync the user into the website DB
  automatically, no more separate registration.
- Real on-chain balances (BSC SLH + TON) side-by-side with internal balances.
- P2P marketplace: list your SLH tokens at your own price.
- First sample course published for free to test the marketplace.

### 🔐 User action needed

- Rotate all ~20 bot tokens via @BotFather (see SECURITY_TOKEN_ROTATION.md).
- Create a Facebook App for feed integration.
- Confirm: should @Chance_Pais_bot pivot to a gambling-recovery bot?

---
