# Pre-Broadcast Verification Checklist
**Date:** 2026-04-27
**Goal:** Before sending ANY broadcast that points users at the new pages — verify each URL works.

---

## ⚠️ DO NOT broadcast until ALL ✓ are checked

The new code I built must be deployed first. Until then, the URLs below will return 404 or fail.

---

## Phase 0 — Deploy code (~10 min)

```powershell
cd D:\SLH_ECOSYSTEM

# 1. Verify both main.py files are equivalent
fc D:\SLH_ECOSYSTEM\main.py D:\SLH_ECOSYSTEM\api\main.py | Select-Object -First 10

# 2. Verify the new routers import cleanly (no syntax errors)
python -c "from routes.system_status import router; from routes.investor_engine import router; from routes.courses import router; print('All 3 routers OK')"

# 3. Stage everything new + edited
git add main.py api/main.py
git add routes/system_status.py routes/investor_engine.py routes/courses.py
git add scripts/slh-orchestrator.py scripts/slh-orchestrator.ps1
git add ops/SECURITY_FIX_PLAN_2026-04-27.md
git add ops/SLH_NEURAL_MIGRATION_2026-04-27.md
git add ops/STRATEGIC_ROADMAP_2026-04-27.md
git add ops/CONTROL_LAYER_ARCHITECTURE_2026-04-27.md
git add ops/PRE_BROADCAST_CHECKLIST_2026-04-27.md
git add ops/CLEANUP_PLAN_2026-04-27.md
git add ops/SESSION_HANDOFF_20260427.md ops/SESSION_HANDOFF_20260427_v2.md
git add CLAUDE.md

# 4. Commit + push (Railway will auto-redeploy)
git commit -m "feat: Investor Engine + Content Marketplace + Control Layer + 5-page Neural migration"
git push origin master

# 5. Push the website repo
cd D:\SLH_ECOSYSTEM\website
git add command-center.html investor-engine.html investor-portal.html disclosure.html course-ai-tokens.html
git add css/slh-neural.css landing-v2.html
git add index.html about.html wallet.html admin.html js/shared.js
git commit -m "feat: Command Center + Investor Engine UI + Course Marketplace + Disclosure"
git push origin main
```

**Wait ~3 minutes** for Railway to redeploy and GitHub Pages to publish.

---

## Phase 1 — API endpoints to verify (no auth)

Open each in a browser. **All should return JSON (not HTML 404).**

| # | URL | Expected |
|---|-----|----------|
| 1 | https://slhcoil-production.up.railway.app/api/health | `{"ok": true, ...}` |
| 2 | https://slhcoil-production.up.railway.app/api/system/status | `{"ok": true, "api_up": true, ...}` |
| 3 | https://slhcoil-production.up.railway.app/api/system/bots | `{"bots": [...25 items], ...}` |
| 4 | https://slhcoil-production.up.railway.app/api/system/stats | KPIs JSON |
| 5 | https://slhcoil-production.up.railway.app/api/courses/ | `{"items": [], "count": 0}` (empty until you add the AI Tokens course) |

**If ANY returns 404 → Railway didn't redeploy.** Check Railway logs.

---

## Phase 2 — Web pages to verify (visual)

Open each in a browser. **All should render the Neural theme without console errors.**

| # | Page | What to check |
|---|------|----------------|
| 1 | https://slh-nft.com/ | Hero loads, neural background visible, no broken layout |
| 2 | https://slh-nft.com/landing-v2.html | Investor landing prototype - hero, token nodes, roadmap |
| 3 | https://slh-nft.com/command-center.html | Sidebar nav, KPI tiles, bot grid (yellow dots until orchestrator runs) |
| 4 | https://slh-nft.com/investor-engine.html | Admin form for investors/revenues/expenses (legal banner visible) |
| 5 | https://slh-nft.com/investor-portal.html | Login screen (telegram_id input) |
| 6 | https://slh-nft.com/course-ai-tokens.html | Course landing with NFT card visual + checkout box |
| 7 | https://slh-nft.com/disclosure.html | Full legal disclosure document |
| 8 | https://slh-nft.com/about.html | Should now have neural-bg + theme |
| 9 | https://slh-nft.com/wallet.html | Should now have neural-bg + theme |
| 10 | https://slh-nft.com/admin.html | Should still work + neural-bg added |

**Open browser DevTools console** (F12) on each page. **No red errors should appear.**

---

## Phase 3 — Authenticated admin actions (after Railway env vars set)

These require `ADMIN_API_KEYS` env var to be set on Railway.

### Test the Investor Engine
1. Go to https://slh-nft.com/admin.html → log in (sets `localStorage.slh_admin_password`)
2. Go to https://slh-nft.com/investor-engine.html
3. Click "Investors" tab → add a test investor named "Test Investor"
4. Click "Investments In" → record an investment of ₪100 for the test investor
5. Click "Revenues" → add a revenue of ₪500 for period 2026-04
6. Click "Expenses" → add an expense of ₪100 for period 2026-04
7. Click "Distribution" → enter period `2026-04`, distribution_pct `0.5`, click "חשב Preview"
8. **Expected:** Shows Net Profit ₪400, Distributable ₪200, "Test Investor" gets ₪200 (100% share since only investor)
9. Click "אשר וצור Payouts" → confirms
10. Go to "Payouts" tab → see one payout for ₪200 with status `pending`

✅ **If all 10 steps work → Investor Engine is alive.**

### Test the Course Marketplace
1. Open browser DevTools → Console → run:
   ```javascript
   fetch('https://slhcoil-production.up.railway.app/api/courses/', {
     method: 'POST',
     headers: { 'Content-Type': 'application/json', 'X-Admin-Key': localStorage.slh_admin_password },
     body: JSON.stringify({
       slug: 'ai-tokens-master',
       kind: 'course',
       title: 'איך מחושבים טוקנים ב-AI?',
       subtitle: 'הקורס המקיף בעברית',
       price_ils: 149,
       cover_image_url: '/assets/img/tokens-explained.png',
       published: true,
     }),
   }).then(r => r.json()).then(console.log);
   ```
2. **Expected:** `{"ok": true, "item_id": 1, "slug": "ai-tokens-master"}`
3. Open https://slh-nft.com/course-ai-tokens.html → click "רכוש עכשיו"
4. Select payment method, fill name, click "צור הזמנה"
5. **Expected:** Order created with `SLH-XXXXXX` ref + payment instructions
6. Verify in: https://slhcoil-production.up.railway.app/api/courses/ → should show the AI Tokens course

✅ **If checkout works → Marketplace is alive.**

---

## Phase 4 — Broadcast template (only after all above pass)

**Template Hebrew (Telegram broadcast):**

```
🚀 SLH Spark — שדרוג מערכת מלא

🎓 קורס חדש זמין: "איך מחושבים טוקנים ב-AI?"
   ₪149 (במקום ₪399 - השקה!)
   👉 https://slh-nft.com/course-ai-tokens.html

🧬 דף landing מעוצב חדש למשקיעים
   👉 https://slh-nft.com/landing-v2.html

🛠️ פלטפורמה לשותפים עסקיים (שקיפות מלאה)
   👉 https://slh-nft.com/investor-portal.html

📋 גילוי נאות מלא
   👉 https://slh-nft.com/disclosure.html

תשלומים: BSC, TON, העברה בנקאית, PayPal
תמיכה: @osifeu_prog
```

---

## ⛔ Stop signs — DO NOT broadcast if:

- [ ] Any URL in Phase 1 returns 404 or 500
- [ ] Any page in Phase 2 has red errors in DevTools console
- [ ] `ADMIN_API_KEYS` env var still missing on Railway
- [ ] `JWT_SECRET` still missing on Railway (security risk)
- [ ] You haven't shown the disclosure page to a lawyer for review
- [ ] You don't have a way to actually receive payments (bank account / crypto wallet ready)
- [ ] You don't have a way to deliver the course content (video URL, etc.)
- [ ] No legal entity registered (cannot legally accept payments as a business)

---

## ✅ Green light — proceed when:

- All Phase 1 endpoints return JSON ✓
- All Phase 2 pages render correctly ✓
- Phase 3 test scenarios complete successfully ✓
- Disclosure has been read by a lawyer (even informally) ✓
- Payment receiving channels are operational ✓
- Course content (video URL) ready to deliver ✓

When all green → broadcast.
When something red → fix first, broadcast later.
