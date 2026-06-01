# Academia Bot Payment Overhaul — 2026-04-20

**Status:** Phase 1 deployed. Phases 2 & 3 documented for next sessions.

## Phase 1 — DELIVERED ✅

### What changed in @WEWORK_teamviwer_bot

**Removed:**
- ❌ "₪ Bit (ידני)" button — Osif doesn't have Bit/PayBox, so buyers can't pay him that way

**Added (6 new payment methods):**
| Method | Callback | Verification |
|--------|----------|--------------|
| 💎 TON | `pay:N:ton` | Auto (Tonkeeper, 30s) |
| 🟡 BNB / BSC | `pay:N:bsc` | Auto (BscScan) |
| 🦊 MetaMask (BSC) | `pay:N:metamask` | Auto (BSC genesis address) |
| 🥞 PancakeSwap → SLH | `pay:N:pancakeswap` | Manual (link out + verify) |
| 🏦 העברה בנקאית | `pay:N:bank` | Manual (admin approval, to Tzvika) |
| ⭐ Telegram Stars | `pay:N:stars` | Phase 2 (XTR invoice) |
| 📱 Bit/PayBox למדריך | `pay:N:phone` | Conditional — only if instructor has phone |
| 💼 חלופה (זהב/זמן) | `pay:N:alt` | Manual via @osifeu_prog |

### Course detail screen now shows
- 📚 "מה כלול בקורס" — bullet list of inclusions
- 👨‍🏫 Instructor name (when assigned)
- Materials availability
- Lifetime license note

### DB schema additions
- `academy_instructors.payout_phone` (TEXT) — used to enable Bit/PayBox routing

### Wizard flow (`/become_instructor`)
- 4 steps now (was 3): name → bio → wallet → **phone** (new, optional)
- Phone validation: digits + `+ - ( )` allowed, 50 char max

### Files touched
- `academia-bot/bot.py` — payment_methods_kb, _create_payment, cb_course, wizard
- `api/routes/academia_ugc.py` — InstructorRegisterIn model + INSERT + ALTER TABLE
- `docker-compose.yml` — SUPPORT_HANDLE=@osifeu_prog (was @SLHSupport which doesn't exist)

### Bug fix included
- `cmd_buy` & `cmd_my_licenses` now wrap with try/except + log + Hebrew fallback message
- Root cause of "/buy returns empty" pattern: silent exception in `_show_courses` had no user-facing fallback

---

## Phase 1.5 — ALSO SHIPPED (same session, after initial Phase 1)

### UX latency fix
- `cb_pay` now calls `cq.answer("טוען…")` **immediately** on entry — prevents the "ghost /start" effect where delayed callback responses appeared to be triggered by later commands (observed in user chat logs 15:28–15:40).

### QR codes for crypto payments
- TON / BSC / MetaMask / PancakeSwap now send a follow-up photo with a QR encoding the wallet deep-link URI (`ton://transfer/...`, `ethereum:...@56`).
- Uses `api.qrserver.com` public endpoint — zero new deps.
- Helpers: `_qr_image_url(data)`, `_wallet_uri(method, addr, amount)`, `_send_payment_qr(chat_id, caption, uri)`.

### Telegram Mini App button
- Bank transfer payment now includes a `web_app=WebAppInfo(url="...buy.html#bank")` button — opens the bank form **inside Telegram** without leaving the chat.
- PancakeSwap gets a regular `url=` button for simplicity.

### Telegram Stars (XTR) — REAL native invoice
- `_send_stars_invoice(chat_id, course)` builds a `LabeledPrice(currency="XTR")` invoice with no provider token (free for bots).
- `@dp.pre_checkout_query()` auto-approves (ledger entry on success, not on intent).
- `@dp.message(F.successful_payment)` validates payload prefix `academy_stars:` and grants the license inline — full flow stays inside Telegram.
- Conversion: `ILS_PER_STAR = 0.05` (1 XTR ≈ $0.013 ≈ ₪0.05).

## Phase 2 — Next session (~2 hours)

### Telegram Stars (XTR) native invoice — ✅ DONE in Phase 1.5
See Phase 1.5 above. Functional.

### Course content uploads
Currently `materials_url` is a single text field. Need:
- Multi-file upload (Telegram-hosted: send video/document to bot, store file_id)
- Per-section structure (intro / module 1 / module 2 / etc)
- Locked-until-purchase preview (first section free, rest gated)
- New tables: `academy_course_sections`, `academy_course_files`

### Instructor payout for Bit/PayBox
- When buyer pays via Bit (`pay:N:phone`), show the instructor's phone with payment instructions
- Buyer marks "שילמתי" → notification to instructor → instructor confirms → license granted
- New status: `awaiting_instructor_confirm` on `academy_licenses`

### Web ↔ Bot profile linking
- Add `telegram_user_id` column to `users` table on website
- Bot exposes `/link_website` command → generates one-time code
- User pastes code in admin.html → links accounts
- Bot earnings/courses appear in user's website dashboard

---

## Phase 2.5 — User asks from 2026-04-20 session (chat feedback)

These surfaced while testing Phase 1/1.5. Documented but NOT implemented:

### Admin chat catalog (in-bot CRM)
- When buyer picks "💼 חלופה" (time/gold/alt) → bot sends Osif a notification message with: course, amount, buyer username/id, offered value, delivery timeline, recommendation
- Osif replies through `@osifeu_prog` DM → bot relays to buyer
- Admin panel web view: all conversations catalogued, status (open/agreed/rejected), follow-up reminders
- Tables: `academy_negotiations` (id, buyer_user_id, course_id, offer_json, status, admin_notes, created_at)

### Guardian integration
- When license granted → auto-add user to Guardian whitelist for premium group
- When user churns/refunds → remove from Guardian allowlist
- Shared `trusted_users` table between bots

### UGC marketplace — users sell their courses
Already started with `/become_instructor` + `/upload_course` flow in current bot.
What's missing:
- Payment routing to instructor wallet (currently all payments go to Osif/Genesis)
- 70/30 split auto-trigger on `successful_payment` (hook exists at `/api/academia/earnings/trigger-split`, not yet wired to on_successful_payment)
- Instructor dashboard on website (stats, payouts, course edit)
- "Publish to marketplace" toggle on each course

### Claude via Telegram — direct work channel
`@SLH_Claude_bot` exists (D:\SLH_ECOSYSTEM\slh-claude-bot\). Needs:
- `ANTHROPIC_API_KEY` in .env (pending — noted in memory)
- Restart docker-compose service
- Test round-trip: Osif sends task via TG → bot dispatches to Claude SDK → response back in TG

---

## Phase 3 — Cross-bot economy (multi-week)

### NFT integration
- Course completion → mint completion NFT (existing nft-shop bot)
- NFTs grant access to gated content/groups
- Trade NFTs on existing marketplace

### Token economy
- Earn ZVK for course completion (4.4 ILS each)
- Spend ZVK for premium content (alternative to ILS payment)
- REP boost from completion (reputation tier)
- SLH staking → discount on courses (already-staked SLH gets 20% off)

### Cross-bot referrals
- Existing `@SLH_AIR_bot` referral (`?start=ref_X`) → mirror to academia
- Instructor referral codes → 10% commission on referred sales
- Cross-promotion: airdrop bot suggests academia courses, academia suggests airdrop

### Bot-to-bot bridges
| From bot | Suggests | When |
|----------|----------|------|
| @SLH_AIR_bot | @WEWORK_teamviwer_bot | After investment > X amount |
| @WEWORK_teamviwer_bot | @G4meb0t_bot | After course completion |
| @SLH_Wallet_bot | @WEWORK_teamviwer_bot | When balance > course price |
| @Grdian_bot | @WEWORK_teamviwer_bot | For new community members |

### Trading integration
- Live SLH price in course detail screen
- "Pay with my SLH balance" option (queries wallet bot)
- Auto-discount when SLH price > 444₪ target

---

## Verification checklist for Phase 1

- [ ] Send `/start` → menu appears
- [ ] Click `רכוש רישיון` → course list shows intro-slh
- [ ] Click course → detail screen shows "מה כלול בקורס" + new payment grid
- [ ] Click each payment method → instructions appear (no errors)
- [ ] Bit/PayBox button **NOT** visible (no instructor phone configured)
- [ ] Click `🎓 הצטרף כמדריך` → wizard reaches step 4/4 asking for phone
- [ ] Enter phone → registration succeeds, message mentions Bit/PayBox enabled
