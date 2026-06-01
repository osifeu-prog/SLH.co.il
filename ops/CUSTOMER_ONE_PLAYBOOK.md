# Customer #1 Playbook — From Reply to Revenue
**Purpose:** The minute-by-minute flow when the first real user responds. Written for the Yaara case (creator, ₪22,221 package) but generalizes to any funnel. When you see a WhatsApp reply — open this file, follow the sequence. No improvisation needed.

**Filter:** everything here moves the customer forward. Skip nothing. Don't add steps.

---

## Stage 0 · The Reply Landed

Trigger: WhatsApp notification from recipient of `ops/OUTREACH_BATCH_*.md` or the funnel page CTA.

### 0.1 · Screenshot the reply (first 30 seconds)
- Literal screenshot → save to `ops/customer_evidence/<name>_reply_<date>.png`
- Why: attribution + proof of first-contact for your own records + legal paper trail if it ever matters.

### 0.2 · Tag the visitor in analytics
Open F12 Console on any SLH page and run:
```js
SLH_Analytics.trackEvent('customer_reply_received', {
  uid: '<tg_id>',
  src: '<wa|tg|fb>',
  campaign: '<segment-outreach>',
  timestamp: new Date().toISOString()
});
```
(Optional — only if you want the reply itself counted in the funnel dashboard.)

### 0.3 · Read the reply fully, twice
Most first mistakes come from responding too fast. Before you type:
- What are they actually asking?
- Is there a question, a concern, a blocker, or an ambiguous "yes"?
- Is there a number (price, timeline, headcount) mentioned?

---

## Stage 1 · First Response (within 1 hour of reply)

### 1.1 · Respond in same channel (don't switch)
If they wrote on WhatsApp, reply on WhatsApp. Switching channels = friction = drop-off.

### 1.2 · Acknowledge → Mirror → Question
Template (customize per reply):
```
היי [שם],

תודה על התשובה 🙏

[Mirror: paraphrase their main point in 1 sentence — shows you read]

[Question: one specific question that moves the conversation forward,
 NOT "when can we meet?" — that's a deflection]
```

Example (Yaara case):
```
היי יערה,

תודה על התשובה 🙏

שמעתי שאת מעוניינת אבל רוצה להבין קודם את התמחור 
— זה בדיוק למה הזמנתי אותך לטופס, כדי לראות מה בדיוק 
צריך ולהתאים.

שאלה אחת: הקורס המדובר הוא כבר מוכן (מוקלט/כתוב) או שהוא 
בתהליך בנייה? זה משנה את הכיוון.
```

### 1.3 · Log the response
Append to `ops/customer_evidence/<name>_log.md`:
```
[YYYY-MM-DD HH:MM] Reply received via WhatsApp.
Key points: [...]
My response sent at: HH:MM
```

---

## Stage 2 · Zoom Coordination (T+1 to T+24h)

### 2.1 · Offer 3 time slots (don't ask "when")
"When can we meet?" = decision fatigue. Pre-pick 3 times:
```
הצעתי 3 זמנים:
🕐 מחר (ראשון) 17:00–17:30
🕐 יום שני 10:00–10:30
🕐 יום שני 14:00–14:30

תבחרי את הנוח ביותר, או תגידי שעה אחרת.
```

### 2.2 · Zoom link ready before the call
- Use your personal Zoom (not new account) — familiarity = fewer mistakes
- Pre-set waiting room OFF (don't leave them stranded)
- Share screen capability tested 5 min before

### 2.3 · Zoom agenda (max 4 items · 20 minutes total)
1. **2 min:** Introduction — "where we are" (no pitch yet)
2. **10 min:** Listen — their situation, their audience, their offer
3. **5 min:** Match — show them the 2-3 features that fit their case (not all 6)
4. **3 min:** Next step — what you'll do in 24h, what they'll do

Never: close the sale on the first call. Only set up the second.

### 2.4 · Post-Zoom recap message (within 2 hours)
```
היי [שם],

תודה על הזמן היום 🙏

מה שסגרנו:
• [action 1 — you]
• [action 2 — them]
• [next touch — date/time]

אם משהו לא ברור או משתנה, כתבי.
```

---

## Stage 3 · The Fulfillment Commitment (T+24h after Zoom)

This is where SLH delivers — before money changes hands. Proof of value before price negotiation.

### 3.1 · Pick ONE feature to demo live
Not all 6 in the package. The ONE most-visible:
- **Yaara case:** bot skeleton for her (manually create `yaara-course-bot` placeholder, private group, her logo as avatar) — she sees it live within 24h.
- **Eliezer case:** import 5 sample contacts into CRM, show his dashboard view.
- **Investor case:** a customized 1-page Partnership MOU draft.

### 3.2 · Send the live artifact with a screenshot
```
היי [שם],

הנה הדגמה לקורס שלך:
🔗 [link to live demo / admin page / screenshot]

זה בנייה ראשונית. הכל מה שמפריע — עדכני אותי ואתאים.
אחרי שזה מתאים לך, נעבור לדיון על החבילה המלאה.

🙏
```

### 3.3 · Wait for reaction before pitching price
If she loves it → Stage 4.
If she wants edits → do them in 24h, repeat.
If no response in 72h → gentle follow-up from `FOLLOWUP_TEMPLATES.md`.

---

## Stage 4 · The Transaction (T+48h+ after demo)

Only reached if Stage 3 got positive reaction.

### 4.1 · Restate the offer in writing
```
הצעת השירות:
• [deliverables — copied from demo + package]
• מחיר: ₪22,221 חד-פעמי
• הפעלה: תוך X ימי עבודה
• תקופת השלמה: 14 יום
• איך משלמים: Bit/העברה ל-[פרטים]
• חשבונית: עוסק פטור (Tzvika Kaufman)

אם ההצעה מתאימה — אשלח קישור תשלום ונתחיל.
```

### 4.2 · Payment methods (in order of preference)
| Method | Speed | Why ranked this way |
|--------|-------|---------------------|
| **Bit** | Instant | No gateway needed, receipt via screenshot |
| **Bank transfer (עוסק פטור account)** | 1 day | Clean audit trail, no fees |
| **PayBox** | Instant | Backup if Bit fails |
| **Cardcom link** | 1 day setup | Future — after Zvika's account is wired |
| **TON/BNB wallet** | Instant | Avoid unless they prefer crypto |

### 4.3 · On payment receipt
1. Screenshot the confirmation
2. Issue digital receipt via חשבונית (Tzvika account)
3. Send to customer with "קיבלתי, מתחילים. פגישה ראשונה של הקמה ב-[date]."
4. Log in `ops/REVENUE_LEDGER.md` (template below)

---

## Stage 5 · Onboarding Kickoff (same day as payment)

### 5.1 · Add to CRM as funded
```bash
curl -X PATCH -H "X-Admin-Key: $KEY" -H "Content-Type: application/json" \
  -d '{"status":"funded","amount_ils":22221,"notes":"Paid via Bit 2026-XX-XX"}' \
  https://slh-api-production.up.railway.app/api/ambassador/contacts/<id>
```

### 5.2 · Setup checklist (Yaara case)
- [ ] Create her dedicated bot (`@<name>_by_slh_bot` via @BotFather)
- [ ] Add to `docker-compose.yml` as new service
- [ ] Create her course listing in marketplace
- [ ] Generate her personal dashboard URL: `https://slh-nft.com/dashboard.html?uid=<tg>&view=creator`
- [ ] Share the dashboard link + bot link with her
- [ ] Calendar reminder: check-in in 7 days

### 5.3 · First-milestone announcement
Public post to community (with her permission):
```
🎉 ברוכה הבאה ל-SLH Spark, יערה!

הקורס הראשון שלנו כ-Creator Package כבר בחנות. 
[link]

מאחלים הצלחה!
```

---

## Stage 6 · Continuous (first 30 days)

### 6.1 · Weekly check-in (automated reminder)
Add to `scripts/daily_digest.py` — "customers in first 30 days" section.

### 6.2 · First-dollar-for-THEM milestone
Celebrate their first sale loudly:
- Screenshot in your story
- DM their community
- Reference in next outreach to OTHER creators ("our customer Yaara just sold her 3rd course...")

### 6.3 · Collect testimonial at day 14
Never ask "can you give testimony?" — too vague.
Do ask: "What's different for you vs 2 weeks ago?" Their answer IS the testimonial.

---

## Revenue ledger template

Create this when first payment lands: `ops/REVENUE_LEDGER.md`

```markdown
# SLH Revenue Ledger v0
## 2026

| Date | Customer | Amount (₪) | Method | Receipt # | Deliverable | Status |
|------|----------|------------|--------|-----------|-------------|--------|
| YYYY-MM-DD | Yaara Kaiser | 22,221 | Bit | 001 | Creator Package | funded |
```

Manual until Cardcom is wired. That's OK at <20 customers.

---

## Red flags (back away politely)

Any of these = don't take them as customer #1:
- Promises "bringing 100 friends" without payment history
- Aggressive negotiating on price before seeing demo
- Asks for ROI guarantees (we don't offer)
- Crypto-only payment with untraceable wallet
- Time pressure ("I need to decide today")
- Will only talk via Signal/encrypted channels
- Mentions "my lawyer" in first 3 messages

None of these automatic rejections — but flag in `ops/yellow_flags.md` and proceed with caution.

---

## Last rule: document everything

Every customer conversation → log in `ops/customer_evidence/<name>_log.md`.
Every payment → screenshot + receipt.
Every promise you make → in writing, even if copy-pasted.

**Your paper trail is your moat.**

---

Last updated: 2026-04-24 (before customer #1 landed).
Update after Yaara conversion with actual timestamps and lessons learned.
