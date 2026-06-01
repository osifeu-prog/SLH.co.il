# 🗺️ SLH Spark · Upgrade Plan · 2026-04-20
**Data-driven review** · מבוסס על live audit שרץ ב-10:29 UTC · API v1.2.0 · 280 endpoints · 95 tables · 108,945 rows

---

## 📊 Part 1 · סקירת מצב (Live State Snapshot)

### ✅ מה עובד ברמה A+

| תחום | מצב | ראיה |
|---|---|---|
| **API backend** | v1.2.0 LIVE · 280 endpoints · 0 errors/hour | `/api/health` + `/api/system/audit` |
| **Railway hardening** | `/docs=404` · `/redoc=404` · `/openapi=404` · rate-limit active | `curl -o /dev/null -w "%{http_code}"` |
| **Database** | PostgreSQL healthy · 95 tables · 108,945 rows | `/api/system/audit` |
| **Docker infrastructure** | 24/25 containers UP · uptime 18h · 0 crashes | `docker ps` |
| **Git hygiene** | working tree clean · 4 commits ahead of origin merged · 2 repos synced | `git status` |
| **Website scale** | 93 HTML pages (גדל מ-83 אתמול) | `ls website/*.html` |
| **Tokens live** | 5/6 live (SLH 200K · ZVK 3K · MNH 3.1K · REP 1.2K · ZUZ 9.6K) | `/api/tokenomics/stats` |
| **Premium conversion** | 12/22 = **54.5%** — מעולה | `/api/stats` |

### ⚠️ מה שבור או בעייתי (ראיות)

| # | בעיה | ראיה | השפעה |
|---|---|---|---|
| 1 | **backups לא מוגדרים** | `latest_backup: "not_configured"` | 🔴 אסון אם DB נופל |
| 2 | **bots.active = 0** אבל 24 רצים | `/api/system/audit` טבלת bots לא מתעדכנת | 🟠 UI משקר |
| 3 | **esp32.configured = false** ב-Railway | `reason: "local control stack not connected"` | 🟡 ESP לא נראה בדשבורד live |
| 4 | **0 deposits, 10 TON staked בלבד** | `/api/stats: total_deposits_ton: 0` | 🔴 revenue engine רדום |
| 5 | **Community מת היום** | `posts_today: 0, active_today: 0` | 🟠 engagement זעום |
| 6 | **AIC inconsistency** | audit אומר 0 holders · stats אומר 1 | 🟡 false positive ב-UI |
| 7 | **רק 22 משתמשים רשומים** | `/api/stats: total_users: 22` | 🔴 volume בעיה #1 של הפרויקט |
| 8 | **`@SLH_ledger_bot` מושבת** | 401 Telegram · טוקן revoked | 🟠 bot פיננסי לא עובד |
| 9 | **`@SLH_Claude_bot` מושבת** | חסר ANTHROPIC_API_KEY | 🟡 no executor via Telegram |
| 10 | **30 bot tokens עוד לא סובבו** | 1/31 done | 🔴 אבטחה (טוקנים בהיסטוריית צ'אטים) |
| 11 | **i18n coverage 37%** · theme coverage 42% | grep על 93 דפים | 🟡 UX לא-עולמי |
| 12 | **0 webhook migration** · 22 bots polling | `grep webhook docker-compose.yml` | 🟡 latency + קונפליקטים |
| 13 | **`latest_backup: null`** | זהה ל-#1 | duplicate |
| 14 | **אין mobile app** | external | 🟠 חסר channel |
| 15 | **אין log aggregation** | external | 🟠 debug קשה |
| 16 | **Community.html אין WebSocket** | הכל polling | 🟡 real-time חסר |

---

## 🎯 Part 2 · תוכנית שדרוג (5 Tiers · 4-6 שבועות)

### Tier 1 · Production Hardening (🔴 CRITICAL) · סה"כ ~6 שעות
**מטרה:** מערכת שתשרוד לקוח שגדל פי 10 פתאום.

| # | משימה | זמן | סיכון | תלות | בעלים |
|---|---|---|---|---|---|
| 1.1 | **pg_dump cron יומי + העלאה ל-S3** | 2h | נמוך | Railway env var (S3 keys) | אני+אתה |
| 1.2 | **Bot heartbeat endpoint** — `/api/bots/heartbeat` + table update | 1h | נמוך | אין | אני |
| 1.3 | **רוטציית 30 tokens נותרים** | 30min × 30 | אפס | BotFather | אתה |
| 1.4 | **Log aggregation** — loki/grafana ב-Docker | 2h | נמוך | אין | אני |
| 1.5 | **Sentry error monitoring** — הוסף SENTRY_DSN | 30min | נמוך | sentry.io signup (חינם) | אתה+אני |
| 1.6 | **`@SLH_Claude_bot` launch** — ANTHROPIC_API_KEY | 5min | אפס | console.anthropic.com | אתה |

**Deliverable:** `ops/PRODUCTION_READY.md` — checklist של 6 בדיקות שכולן ירוקות.

---

### Tier 2 · Growth Enablement (🟠 HIGH) · סה"כ ~16 שעות
**מטרה:** להכפיל את 22 המשתמשים ל-100 תוך שבוע.

| # | משימה | זמן | סיכון | תלות | בעלים |
|---|---|---|---|---|---|
| 2.1 | **i18n sweep** — הוסף data-i18n ל-27 דפים | 4h | נמוך | shared.js מוכן | אני |
| 2.2 | **Theme switcher** — הוסף ל-25 דפים | 2h | נמוך | CSS מוכן | אני |
| 2.3 | **Webhook migration** — POC לבוט אחד (@SLH_AIR_bot) | 3h | בינוני | HTTPS + ngrok/cloudflare tunnel | אני |
| 2.4 | **SEO sweep** — meta OG/Twitter לכל 93 דפים | 2h | נמוך | אין | אני |
| 2.5 | **Share buttons enabled** — `/api/shares/track` על 15 דפים עיקריים | 1h | נמוך | endpoint קיים | אני |
| 2.6 | **Mobile PWA** — manifest.json + service worker | 2h | בינוני | אין | אני |
| 2.7 | **Analytics dashboard v2** — חיבור `/api/analytics/stats` ל-charts | 2h | נמוך | endpoint קיים | אני |

**Deliverable:** 100% i18n + theme + SEO coverage · PWA installable · webhook POC live.

---

### Tier 3 · Revenue Engine Activation (🔴 CRITICAL for business) · סה"כ ~40 שעות
**מטרה:** להעלות מ-0 deposits ל-10+ deposits פעילים.

| # | משימה | זמן | סיכון | תלות | בעלים |
|---|---|---|---|---|---|
| 3.1 | **Academia UGC content** — seed 10 קורסים של מרצים אמיתיים | 8h | בינוני | מוצאי מרצים | אתה+אני |
| 3.2 | **Marketplace liquidity** — seed 20 מוצרים ראשונים | 4h | נמוך | צילומי מוצר | אתה+אני |
| 3.3 | **ESP32 preorder page** — /esp-preorder.html עם QR + form | 3h | נמוך | /api/esp/preorder קיים | אני |
| 3.4 | **Campaign shekel_april26 amplification** — 10 affiliates × 10 refs | 16h | גבוה | ambassador onboarding | אתה |
| 3.5 | **Broker onboarding** — 3 ברוקרים ראשונים (צביקה + 2) | 6h | בינוני | הסכם | אתה |
| 3.6 | **Payment flow polishing** — pay.html UX audit + A/B | 3h | בינוני | analytics | אני |

**Deliverable:** 100 users · 10+ paying customers · 30+ SLH sold · 5+ marketplace transactions.

---

### Tier 4 · Platform Features (🟡 MEDIUM) · סה"כ ~60 שעות
**מטרה:** לעלות שכבת תפעול לרמת מוצר.

| # | משימה | זמן | סיכון | תלות | בעלים |
|---|---|---|---|---|---|
| 4.1 | **P2P fiat gateway** — חיבור Bit/PayBox | 16h | גבוה | חשבון עסקי + API | אתה |
| 4.2 | **2FA for admin panel** — TOTP via `@SLH_AIR_bot` | 6h | בינוני | אין | אני |
| 4.3 | **Rate limit per-user** (לא רק per-IP) | 3h | נמוך | JWT auth | אני |
| 4.4 | **Admin UX redesign** — 19 דפים → 5 dashboards unified | 12h | בינוני | אין | אני |
| 4.5 | **Mobile React Native app** — MVP | 24h | גבוה | Apple/Google dev accounts | אני (POC) |
| 4.6 | **Multi-sig wallet** — SLH treasury | 8h | גבוה | Gnosis Safe setup | אתה |

---

### Tier 5 · Visionary (🟣 LONG-TERM) · חודשים
**מטרה:** להפוך ל-ecosystem מוביל בישראל.

| # | משימה | הערה |
|---|---|---|
| 5.1 | **Launchpad** — ambassadors מריצים טוקנים חדשים | $1M+ market |
| 5.2 | **DAO governance** — REP holders מצביעים | יצירת שכבת ממשל |
| 5.3 | **Multi-chain expansion** — Polygon + Solana bridges | TVL growth |
| 5.4 | **Institutional KYC** — Onfido/Sumsub integration | 10+ lead investors |
| 5.5 | **Legal entity** — עוסק מורשה או חברה בע"מ | לא ניתן להימנע יותר |
| 5.6 | **SLH Tower** — דף עיצוב lore (Floor796 concept) | community culture |

---

## 🚀 Part 3 · איך לבצע בצורה היעילה ביותר

### עיקרון: Tier 1 קודם כל · אי-אפשר לגדול על בסיס שבור

**סדר ביצוע מומלץ:**

1. **היום (יום ראשון 20.4):** Tier 1 כולו — 6 שעות. עד הלילה — מערכת production-ready.
2. **מחר (שני 21.4):** Tier 2 items 2.1-2.4 — 9 שעות. סוף יום: כיסוי מלא של i18n/theme/SEO.
3. **שלישי 22.4:** Tier 2 items 2.5-2.7 + Tier 3.3 (ESP preorder) + Tier 3.6 — 8 שעות.
4. **רביעי 23.4:** Tier 3.1 (academia content) — 8 שעות.
5. **חמישי 24.4:** Tier 3.2 + Tier 3.5 — 10 שעות.
6. **שבוע הבא:** Tier 3.4 (campaign) — full week.
7. **חודש הבא:** Tier 4.
8. **רבעון הבא:** Tier 5.

### מבנה מעקב (live tracking)

אני משתמש ב-3 כלים במקביל:
- **TodoWrite** (live בסשן הזה) — מה שאני עובד עליו עכשיו
- **`ops/UPGRADE_PLAN_20260420.md`** (זה הקובץ) — master plan
- **`/api/agent-hub/message`** — עדכונים בזמן אמת לפאנל Agent Hub

### חלוקת עבודה

| אני יכול לעשות | אתה חייב לעשות | שנינו ביחד |
|---|---|---|
| קוד (i18n, theme, webhook, API) | Railway dashboards | החלטות product |
| Git commits + push | BotFather rotations | content strategy |
| Docker scripts | Anthropic/OpenAI keys | financial entities |
| Documentation | Contracts + legal | partnerships |
| Testing (curl + verify_slh) | Phone calls (Tzvika et al) | launch planning |
| Database migrations | Payment providers signup | UX reviews |

### בקרת איכות

לכל משימה:
1. **Pre-commit**: `python verify_slh.py` (מקומי) + `curl /api/health` (Railway)
2. **Commit message**: `<scope>(<component>): <what changed> — <why>`
3. **Push**: אוטומטי ל-origin
4. **Post-deploy verification**: 3 endpoints רלוונטיים מוחזרים 200
5. **Agent Hub note**: `POST /api/agent-hub/message` עם `{source:"claude",priority:"info",content:"..."}` לתיעוד

### בטחונות

- ❌ **אין deployments אחרי 22:00** (production freeze)
- ❌ **אין merge למשתנים חיים** (dry-run always first)
- ✅ **תמיד pg_dump לפני שינוי schema**
- ✅ **תמיד backup של `.env` לפני edit**
- ✅ **תמיד בדיקה של 5 endpoints אחרי deploy**

---

## 📋 Part 4 · משימות לעכשיו (Todo Live)

ראה ב-TodoWrite פעיל בסשן — משימות Tier 1 כבר מסומנות. אני מקפל אותן שוב לנוחיות:

### 🔴 היום (Tier 1 · 6 שעות):
- [x] Railway env vars (5 vars) — **אתה סיימת ב-10:28**
- [x] `/docs` gate verified 404 — **אני אישרתי ב-10:30**
- [ ] Admin password update (localStorage) — **עליך, 30 שניות**
- [ ] BotFather rotate 5 critical tokens — **עליך, 5 דק'**
- [ ] ANTHROPIC_API_KEY ל-claude-bot — **עליך, 2 דק'**
- [ ] pg_dump cron setup — **אני, 2 שעות**
- [ ] Bot heartbeat endpoint — **אני, 1 שעה**
- [ ] Sentry SENTRY_DSN add — **שנינו, 30 דק'**
- [ ] Log aggregation (loki) — **אני, 2 שעות**

### 🟠 מחר (Tier 2 · 9 שעות):
- [ ] i18n sweep 27 pages
- [ ] Theme switcher 25 pages
- [ ] Webhook migration POC
- [ ] SEO sweep

### 🔴 השבוע (Tier 3 essentials):
- [ ] ESP preorder page
- [ ] Seed 10 academia courses
- [ ] Seed 20 marketplace products

---

## ⭐ Part 5 · המטריקות שנמדוד

**KPI ראשי:** מ-22 משתמשים ל-100 תוך 7 ימים.

### Business KPIs (יומי)
- Users registered today (`/api/stats.total_users` delta)
- Premium conversions today (`/api/stats.premium_users` delta)
- Revenue today (ILS + BNB + TON)
- SLH burned today
- New marketplace listings
- New academia courses

### Technical KPIs (שעתי)
- API uptime (`/api/system/audit.api.uptime_seconds`)
- Error rate (`errors_last_hour`)
- DB query p95 latency (Sentry)
- 5 bots heartbeat freshness (מ-Tier 1 1.2)

### Product KPIs (שבועי)
- Community posts/week
- DM sent count
- Sudoku daily completions
- Dating matches made

כל המטריקות האלה יש-להן כבר endpoints. חסר רק: dashboard שמציג אותן. **יתווסף ב-Tier 2 item 2.7** (4 שעות).

---

**כעת אני עובר לביצוע Tier 1 — מתחיל ב-1.2 (Bot heartbeat endpoint) כי זה קוד טהור ולא מחייב אותך.**

*מסמך חי · יעודכן אחרי כל commit · master source ב-`ops/UPGRADE_PLAN_20260420.md`*
