# ADDENDUM — Phase 2 Vision: Voice + Swarm
**תאריך:** 2026-04-24 (late)
**מוסף ל:** TEAM_HANDOFF_20260424 (6 קבצים קיימים)
**Trigger:** אוסיף ביקש ניתוח תחרותי של ימות המשיח + תכנון Swarm + אינטגרציה מלאה באתר.

---

## מה נשלח (LIVE כבר)

### Website (commit ccd8281, pushed to GitHub Pages main)
- **חדש**: `/voice.html` — Smart IVR vision page עם השוואה מול ימות + pricing + waitlist
- **חדש**: `/swarm.html` — ESP32 mesh vision עם 3-layer architecture + use cases + roadmap
- **עודכן**: `network.html` — 10 צמתים חדשים (5 voice + 5 swarm), filters, legend, canvas renderers
- **עודכן**: `roadmap.html` — 5 items חדשים (2 ב-Phase 3, 3 ב-Phase 4)
- **עודכן**: `project-map.html` — 52 דפים (+2)
- **עודכן**: `js/shared.js` — site-map FAB section "Phase 2 Vision"
- **Cache-bust**: 37 דפי HTML עודכנו ל-`shared.js?v=20260424a`

### Ops docs (commit c89f4a3, LOCAL only — NOT pushed)
- `ops/VOICE_STACK_COMPETITIVE_20260424.md` — ניתוח ימות המשיח (9 פרקים, ~280 שורות)
- `ops/SWARM_V1_BLUEPRINT_20260424.md` — blueprint טכני מלא (3 שכבות + code stubs, ~310 שורות)
- `ops/SESSION_HANDOFF_20260424_VOICE_SWARM.md` — handoff מלא (~220 שורות)

---

## למה ops commit לא נדחף

ה-API repo (`D:\SLH_ECOSYSTEM`) יש בו עוד עבודה לא-מקושרת ב-master שממתינה ל-push (1 commit ahead) + המון uncommitted changes ב-bots/airdrop/admin-bot שנראים משסשן אחר. לדחוף `c89f4a3` עכשיו יגרור את העבודה הלא-שלמה. **ההמלצה**: שהאוסיף ידחוף ידנית אחרי סיום העבודה האחרת, או ידחוף רק את ops/ עם `git push origin c89f4a3:master` כפעולה סלקטיבית.

---

## מה הצוות צריך לדעת

### Osif (Owner — DROP_OSIF_OWNER.md)
- [ ] לקרוא את 2 מסמכי ops (Voice + Swarm)
- [ ] להחליט: Twilio trial עבור Voice POC?
- [ ] להחליט: הזמנת 3 ESP32 ב-₪150?
- [ ] לדחוף ידנית את ops commit (`c89f4a3`) אחרי סיום עבודה אחרת ב-API repo

### Infra/DevOps (DROP_INFRA_DEVOPS.md)
- **אין משימה מיידית**. Phase 2 הוא vision בלבד. אם הגענו ל-POC:
  - Twilio SDK integration (Python)
  - 5 טבלאות DB חדשות (calls, ivr_flows + swarm_devices, swarm_events, swarm_commands)
  - 22 endpoints חדשים (~15 voice + 7 swarm)
  - S3/R2 בשביל voice recordings

### CRM/Business (DROP_CRM_BUSINESS.md)
- **Leads חדשים**: waitlist forms ב-voice.html/swarm.html שומרים ב-`slh_voice_leads` + `slh_swarm_leads` (localStorage) ו-`POST /api/community/posts` עם prefix `VoiceLead:` / `SwarmLead:`.
- צריך להגדיר mechanism לקריאת ה-leads האלה מ-DB (הם מופיעים כ-`community_posts` עם prefix מיוחד).
- אסטרטגיית מחיר Voice: Free/₪99/₪499/Enterprise — מפורטת ב-VOICE_STACK_COMPETITIVE.
- אסטרטגיית מחיר Swarm: תלוי ב-Kosher Wallet pre-sale (₪888 × 100 = ₪88,800 funding).

### Community/Telegram (DROP_COMMUNITY_TELEGRAM.md)
- 2 דפים חדשים זמינים לשיתוף: `slh-nft.com/voice.html` + `slh-nft.com/swarm.html`
- לא לפרסם כ"שירות חדש" — רק כ-"Phase 2 Vision · בבנייה"
- Badge FAB (🗺️) בכל דף → Phase 2 Vision section

### QA/Testing (DROP_QA_TESTING.md)
- אומת מקומית (preview panel): 10 filter options, 61 nodes, 161 connections, 10 site-map links, 39 roadmap items
- לא נבדק: i18n של voice.html/swarm.html (עברית בלבד כרגע)
- לא נבדק: mobile layout מלא (רק desktop preview)
- לא נבדק: waitlist forms בפרודקשן (endpoint `/api/community/posts` אמור לעבוד — היה LIVE בשבוע שעבר)

---

## בדיקה מהירה אחרי deploy של GitHub Pages (שולחן-דסק של אוסיף)

Links לבדיקה (אחרי שה-GitHub Pages propagation מסתיימת, ~2-5 דקות):

```
https://slh-nft.com/voice.html
https://slh-nft.com/swarm.html
https://slh-nft.com/network.html     ← לוודא 10 צמתים חדשים
https://slh-nft.com/roadmap.html     ← לוודא 5 items חדשים
https://slh-nft.com/project-map.html ← לוודא 52 דפים
```

כפתור 🗺️ בכל דף → צריך להראות section "Phase 2 Vision" עם 2 קישורים.

---

**סוף addendum.** לשאלות ספציפיות לצוות — ראה DROP_*.md המתאים.
