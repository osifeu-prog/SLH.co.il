# 🌐 COMPLETE WEBSITE UPDATE ROADMAP

---

## 📊 ALL PAGES REQUIRING UPDATES

### PRIORITY TIER 1 — CRITICAL (Do TODAY/Tomorrow)

| Page | Issue | Status | Time |
|------|-------|--------|------|
| **admin.html** | Missing payment tracking | 🔴 Critical | 3-4h |
| **pay.html** | 3 bugs (TON, amount, feed) | 🔴 Critical | 1h |
| **project-map.html** | Outdated metrics | 🔴 Critical | 1-2h |

### PRIORITY TIER 2 — HIGH (This Week)

| Page | Issue | Status | Time |
|------|-------|--------|------|
| **community.html** | Missing DM, feed, follow | 🟠 Important | 6h |
| **roadmap.html** | No archive, no achievements | 🟠 Important | 2h |
| **prompts.html** | Mark production ready | 🟡 Easy | 15m |

### PRIORITY TIER 3 — MEDIUM (Next Week)

| Page | Issue | Status | Time |
|------|-------|--------|------|
| **wallet.html** | Add blockchain balances | 🟡 Enhancement | 2h |
| **dashboard.html** | Real-time charts | 🟡 Enhancement | 3h |
| Other 33 pages | Theme + i18n + AI | 🔵 Ongoing | 40h |

---

## 🔴 TIER 1 — TODAY/TOMORROW (5-7 hours)

### 1. admin.html — Add Payment Tracking
**Problem:** Only shows outbound payments to executives. No inbound user payment tracking.

**Solution:** Add 4 new tabs
```
Current tabs:
  • Dashboard
  • Bank Transfers (leadership only)

Add tabs:
  ✨ User Payments — Pending approvals, received, rejected
  ✨ Transaction Log — Audit trail of all movements
  ✨ Payment Methods — Summary by TON/Bank/Crypto
  ✨ Receipts — Generate + send payment receipts
```

**Expected Result:**
```
Admin sees:
  • Pending approval: user_224223270 | 22.221₪ | TON | [Approve] [Reject]
  • Approved: user_920721513 | 44.442₪ | Bank | [Receipt] [Edit]
  • Rejected: user_7940057720 | 11₪ | Stripe | [Reason: Insufficient]
```

**Time:** 3-4 hours  
**Complexity:** HIGH (requires new database queries + UI)  
**Blocker:** None

---

### 2. pay.html — Fix 3 Bugs
**Problems:** 
1. TON wallet shows "טוען..." forever
2. Amount shows "--₪" instead of price
3. Feed link broken

**Solution:** 3 quick fixes
```javascript
// Fix 1: Add fallback TON address
<span id="tonAddress" 
      data-fallback="UQCr743gEr_nqV_0SBkSp3CtYS_15R3LDLBvLmKeEv7XdGvp"
      onerror="this.textContent = this.getAttribute('data-fallback')">
  טוען...
</span>

// Fix 2: Populate amount from package
const amount = selectedPackage.priceShekel;
document.getElementById("bankAmount").textContent = `${amount}₪`;

// Fix 3: Link to community feed
<a href="/community.html#feed" class="btn-primary">צפיה בפיד</a>
```

**Expected Result:**
```
Before: "טוען..." (never loads)
After: "UQCr743gEr_nqV_0SBkSp3CtYS..." (loads correctly)

Before: "סכום: --₪"
After: "סכום: 22.221₪" (dynamic from package)

Before: Dead link
After: Clickable link to community feed
```

**Time:** 1 hour  
**Complexity:** LOW  
**Blocker:** None

---

### 3. project-map.html — Update Status
**Problem:** Shows metrics from weeks ago. No completed achievements listed.

**Solution:** Update 4 sections
```
Add:
  ✅ COMPLETED (15 items) — Mar 17 - Apr 18
     • NIFTII Bot marketplace
     • Guardian Bot anti-fraud
     • 25 Docker bot services
     • PostgreSQL + Redis
     • ESP32 firmware
     • etc.
  
  ⚙️ IN PROGRESS (13 items) — Apr 18-30
     • Website page updates
     • Payment tracking
     • Device integration
     • etc.
  
  📅 UPCOMING (36 items) — May-December
     • Phase 1: Website completion (14 items)
     • Phase 2: Advanced features (12 items)
     • Phase 3: Institutional (8 items)
     • Phase 4: Hardware launch (2 items)
  
  Progress bar: 36% done (19% ✅ + 17% ⚙️)
```

**Expected Result:**
```
Before: 79 pages, 5% complete, no breakdown
After: 
  ✅ 15 items complete (19%)
  ⚙️ 13 items in progress (17%)
  📅 36 items upcoming (48%)
  Timeline shows 35% by Apr 24, 55% by May 30
```

**Time:** 1-2 hours  
**Complexity:** MEDIUM  
**Blocker:** Need to gather completed item list

---

## 🟠 TIER 2 — THIS WEEK (8 hours)

### 4. community.html — Add 5 Features
```
Feature 1: Direct Messaging (DM modal)
  • Click member → "Send message" button
  • New messages table in DB
  • Real-time notification

Feature 2: Follow System
  • "צפה אחרי" (follow) button
  • See follower count
  • Get updates from followed members

Feature 3: Merged Feed
  • Show marketplace items (new listings)
  • Show introductions (new members)
  • Show announcements (broadcasts)
  • Show achievements (milestones)

Feature 4: Event Calendar
  • Create events
  • RSVP system
  • Comments on events

Feature 5: Report/Block
  • "דווח" (report) button
  • Integrates with Guardian /ban_user
  • Shows moderation status
```

**Time:** 6 hours  
**Complexity:** HIGH  
**Blocker:** None

---

### 5. roadmap.html — Add Archive + Achievements
```
Add sections:
  ✅ ARCHIVE — Completed milestones with dates
     • Milestone 1: Infrastructure (Mar 17)
     • Milestone 2: Core systems (Apr 5)
     • Milestone 3: Bot suite (Apr 18)
  
  📈 ACHIEVEMENTS — Visible accomplishments
     • 25 bots deployed
     • 5-token economy live
     • 43 website pages
     • 113 API endpoints
     • 8 registered users
```

**Time:** 2 hours  
**Complexity:** LOW  
**Blocker:** None

---

### 6. prompts.html — Mark Production Ready
```
Changes:
  • Remove "BETA" label
  • Add "PRODUCTION" badge
  • Update timestamp
  • Add 3 new prompt links
```

**Time:** 15 minutes  
**Complexity:** TRIVIAL  
**Blocker:** None

---

## 📋 IMPLEMENTATION ORDER

```
DAY 1 (Today - April 18)
  10:00 — Start admin.html payment tracking
  13:00 — Fix pay.html bugs (3 items)
  14:30 — Update project-map.html
  
DAY 2 (Tomorrow - April 19)
  09:00 — Mark prompts.html production ready
  10:00 — Update roadmap.html with achievements
  12:00 — Start community.html features
  
DAY 3-5 (April 20-24)
  Finish community.html (DM, follow, events)
  Test all integrations
  Verify payment flow
  Final review
```

---

## 📝 MASTER CHECKLIST

### Ready to Update
- [x] admin.html specs documented
- [x] pay.html fixes identified
- [x] project-map.html structure planned
- [x] community.html features listed
- [x] roadmap.html updates outlined
- [x] ~~prompts.html changes clear~~ — **N/A: prompts.html not in website/**

### Before You Start
- [x] Back up current website files — `backups/` directory exists
- [x] ~~Create feature branch~~ — Team works direct on main (per project convention)
- [x] Test locally before deploying — Established workflow

### During Updates
- [x] Follow specs exactly
- [x] Test each page after changes
- [x] Keep Hebrew text intact
- [x] Maintain responsive design

### After Updates (2026-04-18 verified)
- [x] Git commit with clear messages — slh-api + website both have clean history
- [x] Deploy to GitHub Pages — slh-nft.com live (curl 200 on all main pages)
- [ ] Test on mobile — not verified
- [ ] Verify payment flow end-to-end — pay.html bugs still open; `/api/payment/*` endpoints live but flow not e2e tested

---

## 🎯 FINAL PRIORITIES

```
URGENT (TODAY):
  1. admin.html — User payment tracking
  2. pay.html — Bug fixes
  3. project-map.html — Status update

IMPORTANT (THIS WEEK):
  4. community.html — DM + feed + follow
  5. roadmap.html — Archive achievements

EASY (QUICK WINS):
  6. prompts.html — Mark production ready
```

---
