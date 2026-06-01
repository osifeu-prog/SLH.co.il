# 🌐 Website Updates Required — 2026-04-18

---

## 📋 PAGE 1: prompts.html

### Current State
✅ Lists 9 AI agent prompts + master index
✅ Marked as "established resources"
✅ All have markdown documentation + shareable links

### Updates Needed
- [ ] Mark as **PRODUCTION READY** (not experimental)
- [ ] Add links to:
  - Guardian Bot Admin prompt
  - NIFTII Airdrop prompt
  - ESP32 Device Connector prompt
- [ ] Add "Last Updated: 2026-04-18" timestamp

### Status: 🟢 MOSTLY COMPLETE

---

## 💳 PAGE 2: pay.html

### Current State
🟡 **BETA** — Known issues:

#### Issue #1: TON Wallet Address Missing
```
Problem: Shows "טוען..." (loading) but never loads
Location: Premium package section
Expected: "UQCr743gEr_nqV_0SBkSp3CtYS_15R3LDLBvLmKeEv7XdGvp"
```

#### Issue #2: Dynamic Amount Not Showing
```
Problem: Shows "סכום: -- ₪" instead of actual price
Expected: "סכום: 22.221₪ (~1.5 TON)"
Affected: Bank transfer section
```

#### Issue #3: Feed Reference Orphaned
```
Text mentions: "גישה מלאה לכל הבוטים + פיד"
Problem: No link to actual feed
Solution: Link to community.html + new feed features
```

### Fixes to Apply
- [ ] **Line 1:** Add fallback TON address if API times out
  ```html
  <span id="tonAddress" data-fallback="UQCr743gEr_nqV_0SBkSp3CtYS_15R3LDLBvLmKeEv7XdGvp">
    טוען...
  </span>
  ```

- [ ] **Line 2:** Populate amount dynamically from selected package
  ```javascript
  const amount = selectedPackage.priceShekel;
  document.getElementById("bankAmount").textContent = `${amount}₪`;
  ```

- [ ] **Line 3:** Add button linking to community feed
  ```html
  <a href="/community.html#feed" class="btn-primary">צפיה בפיד</a>
  ```

### Status: 🟡 REQUIRES FIXES (3 items)

---

## 👥 PAGE 3: community.html

### Current State
✅ Has basic features:
- Member profiles
- Posts + activity feeds
- Marketplace (items, courses, NFTs)
- Daily tasks / Sudoku games
- Live member counts

❌ Missing Features (vs Facebook/ICQ):
1. **No Direct Messaging** — Members can't DM each other
2. **No Media Richness** — Limited image/video sharing
3. **No Event Calendar** — Can't create/schedule events
4. **No Friend Connections** — No "Add Friend" mechanic
5. **No Recommendations** — No algorithm for content discovery
6. **No Moderation Tools** — No reporting/blocking

### Proposed Improvements (Priority Order)

#### HIGH PRIORITY
**Feature 1: Direct Messaging**
```
Component: DM modal overlay
Action: Click member name → "Send message" button
Database: Add messages table to PostgreSQL
Example: admin.html has similar pattern (already working)
```

**Feature 2: Connected Feed**
```
What: Merge 3 feeds:
  • Marketplace activity (new items)
  • Member introductions (new joiners)
  • Community announcements
Where: /community.html#feed (top section)
Data source: Combine from NIFTII marketplace + user_profiles + broadcasts
```

**Feature 3: Friend/Follow System**
```
Add: "צפה אחרי" (follow) button on member cards
Count: "X עוקבים" (followers) badge
Use case: Users see updates from people they follow
Database: Add follows table
```

#### MEDIUM PRIORITY
**Feature 4: Event Calendar**
```
Component: Calendar widget (Gregorian + Hebrew dates)
Actions: Create event, RSVP, comment
Examples: Meetups, AMAs, AirDrop announcements
```

**Feature 5: Moderation**
```
Add: "דווח" (report) button on posts
Uses: Guardian bot's /ban_user integration
Status: Block bad actors, show to all moderators
```

### Status: 🟠 REQUIRES ENHANCEMENT (5 features)

---

## 🗺️ PAGE 4: roadmap.html

### Current State
❌ Broken:
- Shows 0 completed items
- Shows 0 in progress
- Shows 0 upcoming
- Only 1 future milestone listed (Dec 2026)
- No archive section
- No completed achievements shown

### What Should Show

#### COMPLETED SECTION (Archive)
```
✅ Q1 2026 — Infrastructure Foundation
   • PostgreSQL + Redis deployment
   • 25 Docker bot services launched
   • Railway API integration (113 endpoints)
   • GitHub Pages website (43 pages)

✅ Q2 2026 April — Core Systems
   • NIFTII Bot marketplace (Hebrew UI, pet simulation)
   • Token economy (5 tokens: SLH, ZVK, MNH, REP, ZUZ)
   • Guardian Bot anti-fraud system
   • Ledger Bot transaction tracking
   • ESP32 device firmware (WiFi selector)
   • Broadcast airdrop automation
```

#### IN PROGRESS SECTION
```
⚙️ April 18-30, 2026 — Website Completeness
   • Direct messaging feature (community.html)
   • Feed integration (pay.html + community.html)
   • Roadmap achievement display (this page)
   • TON testnet transaction completion

⚙️ May 2026 — Scaling
   • Mobile app (React Native)
   • Advanced analytics dashboard
   • Webhook-based bot communication
```

#### UPCOMING SECTION
```
📅 June-August 2026 — Premium Features
   • AI portfolio advisor
   • Event calendar + RSVPs
   • Multi-language support (English, French, Arabic)
   
📅 September 2026 — Institutional
   • Institutional wallet support
   • Advanced KYC flows
   • API for partner integrations

📅 December 2026 — Hardware
   • 🕊️ ESP32 "Kosher Wallet" launch (₪888)
   • Integration with ledger system
```

### Updates to Apply
- [ ] Create 3 sections: COMPLETED | IN PROGRESS | UPCOMING
- [ ] Move 4-5 items to COMPLETED (with dates + descriptions)
- [ ] Add 3-4 items to IN PROGRESS (current April work)
- [ ] Reorganize UPCOMING with realistic dates
- [ ] Add visual badges: ✅ (done) ⚙️ (active) 📅 (planned)
- [ ] Show completion percentage: "15% of 2026 roadmap complete"

### Status: 🔴 REQUIRES COMPLETE REWRITE (structure + content)

---

## 🔗 INTEGRATION MAP — What to Connect

### Feed Connections
```
Community Feed should show:
  1. Marketplace activity (new NIFTII items)
  2. User introductions (new members joining)
  3. Announcements (broadcasts, airdrops)
  4. Achievements (user leveled up, milestones)
  5. Follow suggestions (members you might know)
```

### Marketplace ↔ Community Links
```
When user views item in NIFTII:
  → Show seller's community profile
  → "Contact seller" opens DM (new feature)
  → "See seller's other items" links to marketplace
```

### Introduction/Networking Features
```
New member flow:
  1. Register → prompt for intro post
  2. Intro post appears in community feed
  3. Others can follow/message them
  4. Show mutual connections ("5 משותף")
```

### What Else Could Connect?
```
Suggested additions:
  • Leaderboards by XP (per pet level in NIFTII)
  • Badges system (first purchase, 100 followers, etc.)
  • Referral tracking (show referrer + referees)
  • Live activity stream (who's online now)
  • Trending hashtags (tracked from posts + marketplace)
  • Weekly digest emails (community highlights)
```

---

## 📅 IMPLEMENTATION SCHEDULE

### TODAY (April 18)
- [x] Fix pay.html (3 quick fixes)
- [x] Update prompts.html (mark production ready)
- [ ] Create archive section on roadmap.html
- [ ] Move completed items to archive

### Tomorrow (April 19)
- [ ] Add direct messaging to community.html
- [ ] Implement follow/friend system
- [ ] Test feed integration

### This Week (April 19-24)
- [ ] Event calendar widget
- [ ] Moderation tools (report button)
- [ ] Complete roadmap rewrite
- [ ] Test all connections

---

## 🎯 PRIORITY SUMMARY

| Page | Status | Priority | Est. Time |
|------|--------|----------|-----------|
| prompts.html | ✅ 90% | LOW | 15 min |
| pay.html | 🟡 50% | HIGH | 1 hour |
| community.html | 🟠 30% | HIGH | 6 hours |
| roadmap.html | 🔴 5% | HIGH | 2 hours |

**Total: ~9 hours of work**

---
