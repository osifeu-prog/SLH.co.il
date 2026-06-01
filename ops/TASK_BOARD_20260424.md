# SLH Spark · Task Board · 2026-04-24 (live)
**Priority filter:** "Does this remove an obstacle between 0 → 1 paying customer?"

---

## 🔴 BLOCKED on Osif (user-only, can't be automated)

| # | Task | ETA | Blocks |
|---|------|-----|--------|
| B1 | Railway dashboard → Deployments → Redeploy latest | 30s | 9 commits including CRM + Tzvika fix |
| B2 | Personal Telegram DMs to 4 users (Zvika / Eliezer / Rami / Zohar) — source: `ops/OUTREACH_BATCH_20260424.md` | 7 min | Response funnel for those 4 segments |
| B3 | `git config --global user.name "Osif Kaufman Ungar"` + email | 10s | Correct author on future commits |
| B4 | Eliezer's 130-investor CSV (external request pending) | — | CRM Phase 0 activation |
| B5 | Yaara reply to WhatsApp sent 2026-04-24 | — | First creator conversion test |
| B6 | Yahav to `/start @SLH_AIR_bot` (needs external prompt) | — | Re-deliverable DM channel |
| B7 | ESP32 firmware v3 flash (USB) | 5 min | Device pairing end-to-end |

---

## 🟡 IN PROGRESS

| # | Task | Owner | Status |
|---|------|-------|--------|
| P1 | Control Layer docs (SYSTEM_ARCH, INCIDENTS, API_REF, RUNBOOK) | Agent | ✅ Shipped (commits e12cbe6, e49a57b, 6892556) |
| P2 | 3 funnel landing pages (creator, investor, community) + intake form | Agent | ✅ Live on slh-nft.com |
| P3 | Outreach batch generator + 8-user markdown | Agent | ✅ `ops/OUTREACH_BATCH_20260424.md` ready |
| P4 | Executor Agent Prompt + PowerShell quick commands | Agent | ✅ This turn |
| P5 | Conversion dashboard stub | Agent | 🚧 Next (stub form) |

---

## 🟢 PRE-CUSTOMER-1 TODO (automated — safe to do anytime)

| # | Task | Effort | Why |
|---|------|--------|-----|
| T1 | First-touch bot DMs to 4 never-contacted users (Idan/Halit/יהונתן/Shachar) pointing to `/community-beta.html` | 5 min | Baseline funnel data |
| T2 | Build `/admin/funnel-dashboard.html` — reads `visitor_events` | 45 min | See clicks in real time |
| T3 | Daily digest script — DMs Osif a summary of events + new registrations | 30 min | Passive info flow |
| T4 | `scripts/railway_watchdog.py` — pings `/api/health`, alerts on version mismatch | 20 min | Catch stuck deploys early |
| T5 | Re-run audit after Railway deploys, close remaining HIGH | 10 min | Data integrity |
| T6 | Email/WhatsApp templates for follow-ups (24h / 3-day / 1-week silent user) | 30 min | Re-engagement sequences |

---

## 🔵 POST-CUSTOMER-5 TODO (do NOT start now — log here to remember)

- Multi-currency (USDT/TON/BNB extensions beyond the current 5+AIC)
- Full UX Design System / State Graph / Neural Map (premature optimization)
- PWA / App Store / Play Store packaging
- BSC on-chain holder cross-ref dapp (token-gate by SLH balance)
- Automated A/B testing framework
- SaaS module for accountant firm (tax refund pipeline — flagged by Osif for future)
- Multi-tenant bot factory ("bot-per-ambassador" spec in `project_ambassador_saas.md`)
- Full regulatory expansion (move from עוסק פטור → חברה בע"מ + ISA exemption or license)

---

## 📝 NOTES

- **Today is Yom Hazikaron → Yom Ha'atzmaut transition.** Low-key day. Sales pushes appropriate from 2026-04-23 evening onward. Parallel session already sent Independence Day broadcast to 19 users.
- **Yesterday's lesson:** 6 bot DMs → 0 engagement. 1 personal WhatsApp (Yaara) → awaiting reply. Bot channel is confirmed dead for outreach.
- **This session's lesson:** Don't over-build docs/frameworks. Ship one funnel end-to-end. Measure. Iterate.

---

## 🔜 NEXT SESSION'S FIRST ACTION

Open `ops/SESSION_FULL_CLOSURE_20260422.md` + THIS file. Run `slh-start.ps1 -StatusOnly`. Check `B1` blocker status via `/api/health` version. If still blocked → gently flag to Osif + pick from `T1-T6` to stay productive.
