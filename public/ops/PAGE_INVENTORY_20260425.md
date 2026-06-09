# SLH Spark · Page Inventory · 2026-04-25

**Purpose:** classify every HTML page into a bucket. Operator marks decisions inline. Agent runs cleanup based on annotations.

**Total:** 109 pages in /root + 4 in /admin + 4 in /miniapp = **117**

**In main nav (shared.js):** 29 pages


---

## How to mark decisions

Add one of these tags AFTER the page name on the line you want to act on:

- `[KEEP]` — leave as is

- `[HIDE]` — add `<meta name="robots" content="noindex,nofollow">` + remove from nav

- `[DELETE]` — `git rm` the file (irreversible — must be on a branch)

- `[MERGE→<target>.html]` — content moves into target, file deleted

- `[RENAME→<new>.html]` — file renamed, redirects added


Default if unmarked: keep current state.


---

## 🌐 HOMEPAGE  (1)

- `/index.html` (43,842 B) — _________________

## 🎯 PUBLIC FUNNEL  (7)

- `/about.html` (45,895 B) — _________________
- `/ecosystem-guide.html` (33,214 B) — _________________
- `/getting-started.html` (24,699 B) — _________________
- `/guides.html` (144,088 B) · 🧭 in-nav — _________________
- `/join-guide.html` (32,333 B) — _________________
- `/join.html` (14,897 B) — _________________
- `/wallet-guide.html` (34,178 B) · 🧭 in-nav — _________________

## 💳 PUBLIC FUNNEL · PAYMENT  (6)

- `/buy.html` (50,460 B) — _________________
- `/card-payment.html` (12,872 B) — _________________
- `/creator-intake.html` (13,559 B) — _________________
- `/pay-creator-package.html` (11,635 B) — _________________
- `/pay-test.html` (12,148 B) — _________________
- `/pay.html` (33,328 B) — _________________

## 🎓 PUBLIC · ACADEMIA  (1)

- `/academia.html` (22,467 B) — _________________

## 💰 PUBLIC · ECONOMICS  (4)

- `/earn.html` (63,214 B) · 🧭 in-nav — _________________
- `/p2p.html` (67,612 B) — _________________
- `/staking.html` (89,785 B) · 🧭 in-nav — _________________
- `/trade.html` (85,290 B) · 🧭 in-nav — _________________

## 🤖 PUBLIC · BOTS LIST  (1)

- `/bots.html` (20,223 B) · 🧭 in-nav — _________________

## 📰 PUBLIC · COMMUNITY/BLOG  (4)

- `/blog-legacy-code.html` (45,046 B) · 🧭 in-nav — _________________
- `/blog.html` (23,337 B) · 🧭 in-nav — _________________
- `/community.html` (133,275 B) · 🧭 in-nav — _________________
- `/daily-blog.html` (44,411 B) — _________________

## 👤 USER ZONE (logged in)  (8)

- `/challenge.html` (50,188 B) — _________________
- `/dashboard.html` (214,191 B) · 🧭 in-nav — _________________
- `/expenses.html` (16,790 B) — _________________
- `/investment-tracker.html` (13,425 B) — _________________
- `/invite.html` (27,542 B) · 🧭 in-nav — _________________
- `/member.html` (39,896 B) — _________________
- `/referral.html` (22,072 B) · 🧭 in-nav — _________________
- `/wallet.html` (85,250 B) · 🧭 in-nav — _________________

## 👤 PARTNER/MEMBER ZONE  (4)

- `/onboarding.html` (48,935 B) — _________________
- `/partner-dashboard.html` (18,989 B) — _________________
- `/partner-launch-invite.html` (17,300 B) — _________________
- `/referral-card.html` (24,384 B) — _________________

## 🌅 PUBLIC · VISION/MARKETING  (6)

- `/encryption.html` (12,675 B) — _________________
- `/healing-vision.html` (26,993 B) — _________________
- `/jubilee.html` (67,825 B) — _________________
- `/kosher-wallet.html` (31,744 B) — _________________
- `/swarm.html` (26,263 B) · 🧭 in-nav — _________________
- `/voice.html` (22,000 B) · 🧭 in-nav — _________________

## 📢 PUBLIC · MARKETING/CAMPAIGN  (7)

- `/ambassador.html` (14,973 B) — _________________
- `/broker-dashboard.html` (11,284 B) — _________________
- `/dex-launch.html` (37,842 B) — _________________
- `/experts.html` (27,689 B) — _________________
- `/for-therapists.html` (16,943 B) — _________________
- `/launch-event.html` (43,017 B) — _________________
- `/promo-shekel.html` (129,626 B) — _________________

## 📜 PUBLIC · LEGAL/REFERENCE  (7)

- `/blockchain.html` (80,312 B) · 🧭 in-nav — _________________
- `/gallery.html` (14,378 B) — _________________
- `/privacy.html` (26,230 B) · 🧭 in-nav — _________________
- `/risk.html` (12,000 B) · 🧭 in-nav — _________________
- `/roadmap.html` (52,985 B) · 🧭 in-nav — _________________
- `/terms.html` (26,981 B) · 🧭 in-nav — _________________
- `/whitepaper.html` (143,924 B) · 🧭 in-nav — _________________

## 🐛 PUBLIC · UTILITY (bug report)  (1)

- `/bug-report.html` (8,544 B) · 🧭 in-nav — _________________

## 🛠 INTERNAL/DEV (hide from customers)  (24)

- `/agent-brief.html` (30,573 B) — _________________
- `/agent-hub.html` (35,061 B) — _________________
- `/agent-tracker.html` (15,730 B) — _________________
- `/alpha-progress.html` (12,845 B) · 🧭 in-nav — _________________
- `/analytics.html` (24,401 B) · 🧭 in-nav — _________________
- `/bot-registry.html` (23,520 B) — _________________
- `/chain-status.html` (10,086 B) — _________________
- `/command-center.html` (34,985 B) — _________________
- `/control-center.html` (46,497 B) — _________________
- `/guardian-diag.html` (30,804 B) — _________________
- `/morning-checklist.html` (33,703 B) — _________________
- `/morning-handoff.html` (21,922 B) — _________________
- `/network.html` (50,770 B) · 🧭 in-nav — _________________
- `/ops-dashboard.html` (32,079 B) — _________________
- `/ops-report-20260411.html` (40,257 B) — _________________
- `/ops-viewer.html` (13,184 B) — _________________
- `/overnight-report.html` (20,860 B) — _________________
- `/performance.html` (9,889 B) · 🧭 in-nav — _________________
- `/project-map-advanced.html` (30,693 B) — _________________
- `/project-map.html` (36,235 B) · 🧭 in-nav — _________________
- `/status.html` (24,805 B) · 🧭 in-nav — _________________
- `/system-audit.html` (18,577 B) — _________________
- `/test-bots.html` (22,459 B) — _________________
- `/upgrade-tracker.html` (10,372 B) — _________________

## 🔒 ADMIN ONLY (hide from customers)  (9)

- `/admin-bugs.html` (15,108 B) — _________________
- `/admin-experts.html` (16,588 B) — _________________
- `/admin-tokens.html` (28,390 B) — _________________
- `/admin.html` (237,609 B) · 🧭 in-nav — _________________
- `/broadcast-composer.html` (20,203 B) — _________________
- `/device-pair.html` (8,385 B) — _________________
- `/leads.html` (14,645 B) — _________________
- `/live.html` (11,943 B) — _________________
- `/rotate.html` (24,748 B) — _________________

## ❓ UNCLASSIFIED — review needed  (19)

- `/dating.html` (25,579 B) — _________________
- `/learning-path.html` (19,862 B) — _________________
- `/liquidity.html` (28,900 B) — _________________
- `/live-stats.html` (23,523 B) — _________________
- `/marketplace.html` (13,001 B) — _________________
- `/mass-gift.html` (12,791 B) — _________________
- `/mission-control.html` (36,789 B) — _________________
- `/my.html` (25,052 B) — _________________
- `/profile.html` (20,358 B) — _________________
- `/receipts.html` (8,084 B) — _________________
- `/risk-dashboard.html` (4,288 B) — _________________
- `/sell.html` (12,480 B) — _________________
- `/settings.html` (16,777 B) — _________________
- `/shop.html` (12,837 B) — _________________
- `/sudoku.html` (21,699 B) — _________________
- `/support-deal.html` (14,324 B) — _________________
- `/system-health.html` (20,052 B) — _________________
- `/tour.html` (19,429 B) — _________________
- `/treasury-health.html` (20,707 B) — _________________

## 🔒 /admin/ (4 — admin-only by URL convention)

- `/admin/control-center.html` (21,221 B) — _________________
- `/admin/mission-control.html` (32,759 B) — _________________
- `/admin/reality.html` (24,363 B) — _________________
- `/admin/tokens.html` (16,635 B) — _________________

## 📱 /miniapp/ (4 — Telegram Mini App, only via Telegram client)

- `/miniapp/dashboard.html` (216,823 B) — _________________
- `/miniapp/device.html` (6,061 B) — _________________
- `/miniapp/swarm.html` (9,386 B) — _________________
- `/miniapp/wallet.html` (5,170 B) — _________________

---

## Quick filters (for review session with operator)


### What customers see in public nav (29 — too many)

- `/admin.html`
- `/alpha-progress.html`
- `/analytics.html`
- `/blockchain.html`
- `/blog-legacy-code.html`
- `/blog.html`
- `/bots.html`
- `/bug-report.html`
- `/community.html`
- `/dashboard.html`
- `/earn.html`
- `/guides.html`
- `/invite.html`
- `/network.html`
- `/performance.html`
- `/privacy.html`
- `/project-map.html`
- `/referral.html`
- `/risk.html`
- `/roadmap.html`
- `/staking.html`
- `/status.html`
- `/swarm.html`
- `/terms.html`
- `/trade.html`
- `/voice.html`
- `/wallet-guide.html`
- `/wallet.html`
- `/whitepaper.html`

### Recommended public nav after cleanup (7-9 items)

- `/` (home)
- `/about.html`
- `/getting-started.html`
- `/bots.html`
- `/earn.html`
- `/buy.html`
- `/dashboard.html` (logged-in)
- `/whitepaper.html`
- `/community.html`

