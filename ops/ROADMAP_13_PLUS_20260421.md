# SLH Roadmap — Items 13+ (post-Dynamic-Yield pivot)
**Date:** 2026-04-21
**Author:** Osif + Claude (session 2026-04-21)
**Status:** PROPOSED — awaiting prioritization + sign-off
**Previous items:** 1-12 = Dynamic Yield pivot (shipped 2026-04-20/21). See `SESSION_HANDOFF_20260421_DYNAMIC_YIELD.md`.

---

## TL;DR

Osif's 2026-04-21 10:56 message raised 5 new strategic themes that expand the scope beyond the Dynamic Yield pivot. This document breaks them into **discrete work items (13 through 25)** with scope, effort estimate, dependencies, and a suggested sequencing.

Items are grouped:
- **Revenue expansion** (13-15): Mining, new user earning mechanisms, partner integrations
- **User experience** (16-20): UI/UX overhaul, menu consolidation, toolbar system
- **Mobile delivery** (21-22): PWA hardening, native app wrappers (Play Store + App Store)
- **Platform hygiene** (23-25): User support loop, payment flow rebuild, data model consolidation

---

## 13. Crypto Mining Integration

**The ask:** "האם אפשר להכניס כריה של מטבעות (אולי ביטקויין) למערכת?"

**Scope:** Add crypto mining as a user-facing feature. Three realistic implementation tiers:

### 13a. Merge-mining / cloud mining marketplace (FASTEST to ship)
- Partner with an existing cloud mining provider (NiceHash, Binance Pool, SLH-branded white-label)
- SLH becomes an **affiliate distributor**, not an operator
- Revenue: 10-20% referral cut from provider + flat margin
- Effort: **40h** (provider contracts, UI, payout tracking)
- Legal: same 2-tier affiliate structure (no new regulation)

### 13b. SLH Mining Pool (operational, NOT recommended yet)
- Run actual mining pool infra (BTC or ETC or KAS)
- Requires: hardware contracts, electricity PPA, 24/7 ops
- Capex: $50K-$500K. Opex: high.
- Effort: **6+ months**, external team needed
- **Recommendation: defer until post-entity registration + $100K+ Treasury**

### 13c. "Proof-of-Learn" — use Academia to mint ZVK
- No actual crypto mining, but **positions Academia as mining equivalent**
- Users "mine" ZVK by completing courses, quizzes, peer-review
- Already aligned with the existing ZVK reward economy
- Effort: **20h** (quiz grading + ZVK mint logic)
- **Recommendation: ship this alongside Course #1 — low effort, high narrative value**

**Decision: ship 13c in 2 weeks; evaluate 13a vs 13b in Q2 2026.**

---

## 14. Additional User Revenue Mechanisms

**The ask:** "אילו עוד אפשרויות רווח אפשר להציע למשתמשים?"

**Options (from lowest to highest complexity):**

| Idea | Revenue model | Effort | Legal risk |
|---|---|---|---|
| Course creation (instructors earn 70%) | Already live via academia_ugc | ✅ 0h | Low |
| Affiliate program (2 tiers) | Already live, 20% + 5% | ✅ 0h | Low |
| Bug bounty program | Pay in ZVK for verified issues | 8h | Low |
| Content writing bounties | Blog posts, guides → paid ZVK | 12h | Low |
| Translation bounties (EN/AR/RU/FR) | Per-page micro-payments | 16h | Low |
| P2P marketplace fees (2.5%) | Already scaffold-ed in DB | 24h | Medium |
| Liquidity provider rewards | Stake SLH-TON LP → share DEX fees | 60h | Medium |
| Prediction markets (community) | ZVK-based event betting | 120h | **HIGH** — gambling law |
| Lending desk (collateralized) | Micro-loans in MNH | 200h | **CRITICAL** — need license |
| Card program (SLH debit card) | Partner with Kulipa/Solaris | 400h | **CRITICAL** — PSP license |

**Recommended for next 90 days:**
1. Bug bounty program (easy, trust-building, attracts devs)
2. Content bounties (feeds blog.html and Academia)
3. P2P marketplace activation (infra exists, just needs UI polish)
4. Translation bounties (unblocks i18n debt — 63% of pages still untranslated)

**Defer:** Lending, predictions, card — require licenses.

---

## 15. Partner Integration Question — "ארקם"

**The ask:** "אני עדיין לא רואה את הקשר לארקם ולמערכת שלהם"

**⚠️ NEEDS CLARIFICATION FROM OSIF:**

"ארקם" (Arkam) could mean:
- **Arkham Intelligence** (arkham.com) — on-chain intel platform, free signup, API
- **Arkham Exchange** (arkm.com) — L1 trading, separate from Intelligence
- **Arcanum** — a DeFi vault system
- Internal acronym for a specific partner

**If Arkham Intelligence:** Possible integrations:
- Link SLH Treasury wallets to Arkham for public transparency
- Pull our own on-chain data via their API for `/status` dashboard
- Users can "claim" their wallet on Arkham → REP boost

**If something else — Osif, please clarify in next message.** This roadmap item parked until then.

---

## 16. UI/UX Overhaul — Calm Theme + Toolbar System

**The ask:**
- "עיצוב סולידי רגוע שמשקף את SLH במיטבו"
- "להוסיף את העיצוב כאופציה נוספת לכל העיצובים שיש"
- "להוסיף סרגלי כלים בכל האתר"

**Current state:**
- 7 themes exist: dark, terminal, crypto, cyberpunk, ocean, sunset, light
- No persistent toolbar across pages (each page has its own header)
- 43 HTML pages — inconsistent spacing, different widths, color varies

**Proposed work:**

### 16a. New theme: "slh-calm"
- Palette: off-white bg, deep navy accents, gold highlights (no neon)
- Typography: Rubik for body, Frank Ruhl Libre for headers (Hebrew-aware)
- Reduced animations (30% of current), calm motion easing
- Add to `THEMES` array in `shared.js`, entry in `THEME_META`
- Effort: **12h** for theme CSS + previews on all pages

### 16b. Persistent toolbar
- Top bar: logo · nav · search · wallet · notifications · user menu
- Bottom bar (mobile): 5 key nav items
- Context toolbar: page-specific actions (e.g., "Edit", "Share", "Export" per page type)
- Implement once in `shared.js`, injected into `#slh-nav` div on every page
- Effort: **24h** design + **16h** implementation

### 16c. Design system documentation
- Extend `slh-design-system.css` with components (buttons, cards, inputs, modals)
- Figma file (optional but recommended) as source of truth
- Style guide page (`/styleguide.html`) for developers
- Effort: **16h**

**Total: ~70h. Realistic timeline: 3 weeks if dedicated, 6 weeks parallel to other work.**

---

## 17. Menu Organization + Navigation Cleanup

**The ask:** "אני חייב לסדר את כל התפריטים"

**Current state (from shared.js):**
- `NAV_ITEMS` has 20+ items
- Admin sidebar has 19 pages
- No clear hierarchy (trading vs learning vs admin all mixed)

**Proposed:**
- Group into 4 clusters: **Trade · Learn · Community · Account**
- Dropdown menus for sub-items (not 20 tabs)
- Breadcrumbs on every inner page
- Search bar in header (global page search)
- Mobile: hamburger with nested sections

**Effort: 16h. Ship with 16b.**

---

## 18. Blog + Content Strategy

**The ask (implicit from "SLH במיטבו"):** SLH needs a content voice.

- Daily blog already exists (`daily-blog.html`). Turn into weekly digest + monthly deep-dive.
- Newsletter: outbound email (SendGrid / Postmark) to registered users
- YouTube channel linkage (`reference_social_links.md` lists 2 existing)
- Effort: **24h** setup + **6h/week** ongoing

---

## 19. On-Page Analytics

Currently: we add GA / Plausible tags but don't actually read them. Need:
- Dashboard at `/admin/analytics` (exists scaffolded)
- Per-page conversion tracking (signup, purchase, share)
- A/B testing infrastructure (GrowthBook or self-hosted)
- Effort: **32h**

---

## 20. Status Page (`/status.html`) — Live CR Widget

Tied to Dynamic Yield pivot commitments:
- Real-time TVL, R_t, Net, P_t, CR, Buffer ratio, Run threshold
- Live Circuit Breakers state
- Last 12 distribution events
- Public wallet addresses with live balances (Etherscan/BscScan/Tonviewer API)
- Effort: **32h** backend endpoint + **24h** frontend widget

---

## 21. PWA Hardening

**The ask:** "לארוז את האתר גם כאפליקציה"

**Prerequisites (mostly not done):**
- Service worker (caching strategy) — NOT CONFIGURED
- Offline mode (cache key pages) — NOT CONFIGURED
- Install prompt UX — NOT CONFIGURED
- Push notifications (Web Push API) — NOT CONFIGURED
- App icons (192, 384, 512 × 2x) — partial
- Manifest.json — needs audit

**Effort: 40h to reach PWA "install-ready" state.**

---

## 22. Native App Wrappers (Google Play + App Store)

### 22a. Google Play (Android)
- Use Capacitor (Ionic) to wrap the PWA
- OR Bubblewrap (Trusted Web Activity) — Google's official PWA→APK tool
- Create developer account ($25 one-time)
- Assets: screenshots, feature graphic, description
- Privacy policy URL (we have `/privacy.html`)
- Content rating questionnaire
- **Build + submit effort: 40h. Review cycle: 3-14 days.**

### 22b. App Store (iOS)
- Apple developer account ($99/year)
- Xcode on a Mac (required — we're on Windows, need CI or rent Mac)
- Capacitor project
- App review **much stricter** — no crypto-yield language (need carefully worded submission)
- **Build + submit effort: 60h. Review cycle: 3-30 days, may require appeal.**

### 22c. Strategic note
- Apple rejects anything smelling of unlicensed financial services
- Google is more permissive
- **Recommendation: Play Store first (easier win), App Store 3-6 months later after legal entity + lawyer review**

---

## 23. User Support Loop

**The ask:** "יש לי כרגע משתמשים באתר שאני רוצה שהם יוכלו לפנות אליי"

**Current state:**
- Support handle is `@osifeu_prog` (per `reference_support_handles.md`)
- No ticket system. Users DM directly.
- No centralized view of who's asking what.

**Proposed:**

### 23a. Quick fix (2h)
- Add persistent "Support" button in toolbar (16b) linking to `tg://resolve?domain=osifeu_prog`
- Live chat widget on `/status`, `/dashboard`, `/wallet` pages
- Add "contact" CTA to every page footer

### 23b. Proper ticket system (16h)
- Integrate Freshdesk / Crisp / Zendesk (free tier)
- Telegram bot → ticket forwarding (`@SLHSupport_bot` new)
- Ticket list in admin panel
- Priority tagging (VIP users auto-escalate)

### 23c. Community-powered (40h)
- Discourse forum
- Trusted users earn "moderator" REP
- Public Q&A visible to all
- Reduces Osif's 1:1 load

**Recommendation: 23a this week, 23b in 4 weeks, 23c Q3.**

---

## 24. Payment Flow Rebuild (lesson from today's bug)

**Context:** User 8789977826 paid ₪196 (4×₪49) on 2026-04-20. Got 4 "timeout" errors. `/api/payment/status/` endpoint was returning 500 due to column mismatch. Fixed 2026-04-21.

**Work to prevent recurrence:**

- Reconciliation job: nightly cron that finds `external_payments` with status=approved but no matching `academy_license` → grants license automatically + notifies user
- Webhook from WEWORK → API (not poll from academia-bot)
- Idempotency: `payment_id` as unique key in licenses, not multiple DB paths
- End-to-end test: buy a course with ILS 1 test payment daily, alert if fails
- Monitoring dashboard: pending intents > 2 hours old, approved payments > 1h without license

**Effort: 24h reconciliation + 16h webhook + 16h e2e test = 56h.**

---

## 25. Data Model Consolidation

**Ongoing debt:**
- `love_token_transfers` table still active alongside `web_users` (duplicated state)
- `JWT_SECRET` still empty on Railway (blocked since 2026-04-18 per CLAUDE.md)
- `ADMIN_API_KEYS` still at default `slh2026admin`
- 30 bot tokens exposed historically, 1/31 rotated

**Effort: 80h across 4 weeks. Phase 1 DB work → Phase 2 token rotation → Phase 3 consolidation.**

---

## Sequencing Proposal (the honest plan)

### Week 1 (this week, 2026-04-21 to 04-27)
- [ ] **13c** — Proof-of-Learn ZVK mint (low effort, reinforces pivot)
- [ ] **20** — Live CR widget on `/status` (10h minimum first-pass)
- [ ] **23a** — Support button everywhere (2h)
- [ ] **15** — Clarify "ארקם" with Osif, scope the work
- [ ] **24** (start) — Reconciliation job for academy payments (preventive)

### Week 2-3 (2026-04-28 to 05-11)
- [ ] **16a** — slh-calm theme
- [ ] **16b** — Persistent toolbar system
- [ ] **17** — Menu reorganization (ships with 16b)
- [ ] **14** — Bug bounty + Content bounty programs
- [ ] **24** (complete) — Webhook from WEWORK + e2e test

### Week 4-8 (May 2026)
- [ ] **16c** — Design system docs
- [ ] **18** — Blog strategy + newsletter
- [ ] **19** — Analytics dashboard
- [ ] **21** — PWA hardening
- [ ] **13a** (if decided) — Cloud mining affiliate

### Q3 2026 (June-August)
- [ ] **22a** — Google Play Store submission
- [ ] **23b** — Proper ticket system
- [ ] **25** — Data model + token rotation consolidation
- [ ] **14** (advanced) — P2P marketplace activation, LP rewards

### Q4 2026 (September+)
- [ ] **22b** — App Store submission (post-legal entity)
- [ ] **23c** — Community forum
- [ ] **13b** — SLH Mining Pool (only if Treasury ≥ $100K)

---

## Dependencies + blockers

| Item | Blocked by | Blocks |
|---|---|---|
| 22b (App Store) | #5 Legal entity (from previous handoff) | Nothing downstream |
| 14 (Lending, cards) | Legal entity + PSP license | Retail product lines |
| 13b (Mining pool) | Treasury ≥ $100K | — |
| 16b (Toolbar) | 16a (theme) first | 17 (menu) |
| 20 (Status widget) | Dynamic Yield backend telemetry | Trust metrics |

**Biggest single blocker:** Legal entity registration (#5 from previous handoff). Unlocks 22b, advanced 14, and the payment/card roadmap.

---

## How to use this doc

1. **Osif:** mark items A/B/C priority. Comment on any you want to split or kill.
2. **Next Claude session:** pick top-priority item, expand into implementation plan, execute.
3. **Review cadence:** re-check this doc every Monday, update effort estimates based on reality.

*End of 13+ roadmap — 2026-04-21*
