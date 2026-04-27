# Session Handoff — 26.04.2026 — Blog Soundtrack Embed

**Topic:** הוספת נגיעה אנושית לבלוג — embed של שיר יוטיוב + חתימה אישית
**Owner:** Osif Ungar (`@osifeu_prog`)
**Operator:** Claude (sonnet)
**Status:** ✅ LIVE on production
**Commit:** `fd3bfd4`
**Repo:** `osifeu-prog/osifeu-prog.github.io` → `main`
**Deploy time:** 2026-04-26 10:29:35 +0300
**Live verification:** GitHub Pages serving new bytes (HTTP 200, marker strings detected)

---

## 1. TL;DR

Osif שלח קישור ליוטיוב (`https://www.youtube.com/watch?v=Mtp3QIKHnjk`) ושאל איך להכניס את זה לבלוג כדי שירגיש "קצת יותר אנושי". התוצאה:

- **`blog-legacy-code.html`** — נוספה סקציית `.soundtrack-box` בין כרטיס האוטור ל-CTA, עם הסבר אישי בעברית + iframe יוטיוב privacy-friendly.
- **`blog.html`** — נוספה שורת חתימה איטליק תחת ה-hero ("✍️ נכתב על ידי Osif Ungar · בלילות, בין קוד לקפה · עם מוזיקה ברקע").
- **Total diff:** +38 / −6 שורות, 2 קבצים, פעולה אחת של push.

לא נוצרו קבצים חדשים. אין שינויי API/DB/shared.js. אין עדכוני docker/Railway.

---

## 2. שינויי קוד (מפורט)

### 2.1 `D:\SLH_ECOSYSTEM\website\blog-legacy-code.html`

**Change A: CSS חדש לסקציית סאונדטרק**
- **מיקום:** שורות 86-92 (אחרי `.share-btn.copy`, לפני `.community-template`)
- **גודל:** 7 שורות CSS חדשות + שורה ריקה
- **מחלקות חדשות:** `.soundtrack-box`, `.soundtrack-box h3`, `.soundtrack-box .vibe-note`, `.soundtrack-box .yt-wrap`, `.soundtrack-box .yt-wrap iframe`, `.soundtrack-box .credit`, `.soundtrack-box .credit a`
- **עקרון עיצוב:** משכפל את התבנית של `.share-box` הקיים (gradient רך + border צבעוני + padding נדיב + text-align center), משתמש ב-`var(--purple)` כצבע ראשי כדי להבדיל מ-`.share-box` הירוק.
- **טריק רספונסיבי:** `padding-top:56.25%` על `.yt-wrap` שומר יחס 16:9 בכל רוחב מסך.
- **RTL:** `direction:ltr` על ה-wrapper מונע מ-RTL לעוות את ה-iframe.

**Change B: HTML של סקציית סאונדטרק**
- **מיקום:** שורות 584-603 (בתוך `<article>`, אחרי `</div>` של `.author-card` בשורה 582, לפני `<!-- CTA -->` של ה-`.share-box` הסופי)
- **תגית:** `<aside class="soundtrack-box" aria-label="Soundtrack of this post">` — semantic HTML + accessibility
- **תוכן:**
  - `<h3>🎵 הסאונדטרק של הפוסט הזה</h3>`
  - `<p class="vibe-note">` — 2 שורות עברית באיטליקס שמסבירות את הקשר בין השיר לכתיבה
  - `<iframe>` ל-`youtube-nocookie.com/embed/Mtp3QIKHnjk?rel=0` עם `loading="lazy"` + `referrerpolicy="strict-origin-when-cross-origin"` + `allow=...` + `allowfullscreen`
  - `<div class="credit">` — לינק חזרה ל-YouTube (target=_blank, rel=noopener)
- **video ID בלבד:** `Mtp3QIKHnjk`. הוסר במכוון `&list=RD7aE_Q6Z1CoE&index=2` שהיה ב-URL המקורי, אחרת היוטיוב היה ממשיך אוטומטית לרדיו-מיקס.

### 2.2 `D:\SLH_ECOSYSTEM\website\blog.html`

**Change C: שורת חתימה אישית ב-hero**
- **מיקום:** שורות 126-128 (בתוך `<section class="hero">`, אחרי ה-`<p>` הראשי של ה-tagline)
- **שינוי:** הוספת `<p class="author-signoff">` עם inline-style קצר (size 13px, color text3, font-style italic, margin-top 18px)
- **טקסט:** `✍️ נכתב על ידי Osif Ungar · בלילות, בין קוד לקפה · עם מוזיקה ברקע`
- **רציונל:** שורה אחת, לא מתחרה עם המבנה הקיים, מוסיפה זהות אנושית לעמוד הקטלוג בלי לדרוש תחזוקה (אין נתון מתחלף).

---

## 3. בחירות טכניות (תקציר ההחלטות)

| בחירה | למה |
|---|---|
| `youtube-nocookie.com` במקום `youtube.com` | אין tracking cookies עד שהמשתמש מנגן (privacy-enhanced mode הרשמי של יוטיוב) |
| `loading="lazy"` על ה-iframe | iframe של יוטיוב כבד (~500KB+) — נטען רק כשגוללים אליו |
| video ID בלבד (`Mtp3QIKHnjk`) | בלי `list=...` כדי שלא יתחיל autoplay של רדיו-מיקס |
| `padding-top:56.25%` wrapper | יחס 16:9 רספונסיבי, עובד בכל דפדפן (כולל ישנים) |
| `direction:ltr` על `.yt-wrap` | RTL לא יעוות את מסגרת ה-iframe |
| `aria-label` על ה-`<aside>` | semantic HTML + screen reader friendly |
| מיקום אחרי author-card, לפני CTA | זרימה: פרקים → ביו → השיר שהיה ברקע → שיתוף |
| `rel=0` על ה-embed URL | לא מציג סרטונים מומלצים זרים בסוף |
| `referrerpolicy="strict-origin-when-cross-origin"` | privacy + תאימות עם youtube-nocookie |
| Hard-code, לא API | הבלוג סטטי, אין צורך לבנות endpoint רק בשביל וידאו אחד |
| לא ווידג'ט "now playing" בקטלוג | היה דורש החלפה תקופתית — overhead שלא הבטחנו לתחזק |
| לא פוסט חדש נפרד | "אנושי קצת יותר" = משהו קל ומהיר, לא תוכן חדש |

**התאמה אסתטית מקרית:** ה-`<p>` של הביו של אוסיף במאמר אומר "ארכיטקט מערכות · ניורולוג־מוסיקאי" (שורה 567). הסאונדטרק יושב על זה כאילו תוכנן מההתחלה.

---

## 4. אימות (Verification)

### 4.1 שלב מקומי (קוד)
| בדיקה | סטטוס |
|---|---|
| `Edit` בקובץ blog-legacy-code.html — CSS | ✅ הצליח |
| `Edit` בקובץ blog-legacy-code.html — HTML | ✅ הצליח |
| `Edit` בקובץ blog.html — signoff | ✅ הצליח |
| Read-back של 3 הסקציות לאחר עריכה | ✅ קוד זהה למתוכנן |
| `git status` בריפו `website/` | ✅ 2 קבצים `M`, ללא הוספות לא רצויות |

### 4.2 שלב Push
| בדיקה | סטטוס |
|---|---|
| Branch מקומי | ✅ `main` |
| Remote | ✅ `https://github.com/osifeu-prog/osifeu-prog.github.io.git` |
| `slh-push.ps1` (pre-commit hook) | ✅ עבר |
| Commit | ✅ `fd3bfd4` (2 files, +38 / −6) |
| Push | ✅ `4a5752f..fd3bfd4 main -> main` |
| `git diff-tree fd3bfd4` | ✅ רק blog-legacy-code.html + blog.html |

### 4.3 שלב Production (GitHub Pages)
| URL | HTTP | מארקר נמצא? |
|---|---|---|
| `https://slh-nft.com/blog-legacy-code.html` | ✅ 200 (41,896 bytes) | ✅ `soundtrack-box` (רגקס True) |
| `https://slh-nft.com/blog.html` | ✅ 200 (21,802 bytes) | ✅ `author-signoff` (רגקס True) |

**זמן build של GitHub Pages:** פחות מדקה (verified live ב-`Invoke-WebRequest` מיד אחרי ה-push).

---

## 5. תופעות לוואי / Side Effects

### 5.1 Telegram broadcast — **דולג**
`slh-push.ps1` שלח `WARNING: SLH_ADMIN_BROADCAST_KEY env var not set — notification skipped.` ה-push עצמו הצליח, רק ההתראה ל-`@SLH_Claude_bot` לא נשלחה.

**איך לתקן לפעם הבאה** (לפני הפעלת `slh-push.ps1`):
```powershell
$env:SLH_ADMIN_BROADCAST_KEY = "slh-broadcast-2026-change-me"
```
(המפתח מתועד ב-`MEMORY.md` תחת "Broadcast Keys".)

**להתראה ידנית עכשיו** (אופציונלי):
```powershell
$body = @{
  message = "[deploy] blog: add YouTube soundtrack embed + author signoff for warmth`n`nCommit: fd3bfd4`nhttps://slh-nft.com/blog-legacy-code.html"
} | ConvertTo-Json
Invoke-RestMethod -Uri "https://slh-api-production.up.railway.app/api/broadcast/send" -Method POST -Headers @{"X-Admin-Key"="slh-broadcast-2026-change-me"} -Body $body -ContentType "application/json"
```

### 5.2 Working tree — **לא נקי**
ה-`git status` בעת ה-push חשף **20+ קבצים אחרים במצב Modified** בריפו `website/` שלא קשורים לעבודה הזו (about.html, academia.html, admin.html, ועוד). הם נשארו ב-working tree, **לא** נדחפו (`slh-push.ps1` במכוון מבצע staging רק לרשימת `-Files`).

**פעולה מומלצת לפני ה-push הבא:**
```powershell
Set-Location D:\SLH_ECOSYSTEM\website
git status --short  # סקירה
git stash push -m "wip-pre-soundtrack-deploy" -- $(git status --short | Where-Object { $_ -match '^ M' } | ForEach-Object { ($_ -split '\s+',3)[2] })
# או, אם השינויים stale וניתנים לזריקה:
# git restore <file>
```

### 5.3 ביצועים
- **iframe lazy-load** מבטיח שהיוטיוב לא נטען בכניסה לעמוד.
- **תוספת weight ל-HTML:** ~1.5KB CSS + ~600 bytes HTML = ~2KB. זניח.
- **No new JS** — אין קוד שצריך לעבור tree-shaking או minification.

### 5.4 SEO / Social
- אין שינוי במטא-תגיות (og:title / og:description / og:image) — ה-share preview של המאמר נשאר אותו דבר.
- Schema markup לא הוסף לסאונדטרק (פוטנציאל לעתיד: `<script type="application/ld+json">` עם `MusicRecording`).

---

## 6. Rollback (אם נחוץ)

```powershell
Set-Location D:\SLH_ECOSYSTEM\website
git revert fd3bfd4 --no-edit
git push origin main
# או, אם רוצים rollback מלא בלי שמירת היסטוריה:
# git reset --hard 4a5752f && git push --force-with-lease origin main  # CAREFUL
```

GitHub Pages ירעננן את עצמו תוך דקה.

---

## 7. Follow-ups (לא חוסמים)

- [ ] **לא חובה:** להגדיר `SLH_ADMIN_BROADCAST_KEY` ב-PowerShell profile (`$PROFILE`) כדי שהתראת `@SLH_Claude_bot` תישלח אוטומטית בכל push עתידי.
- [ ] **לא חובה:** לנקות 20+ קבצי WIP ב-`website/` working tree (stash או restore).
- [ ] **רעיון לעתיד:** אם פוסטים עתידיים בבלוג ירצו את אותה תבנית, פשוט להעתיק את ה-`<aside class="soundtrack-box">` ולהחליף את ה-video ID + ה-vibe-note. ה-CSS כבר הוגדר.
- [ ] **רעיון אופציונלי:** להוסיף JSON-LD `MusicRecording` schema בעתיד כדי שגוגל יראה את השיר כתוכן structured.

---

## 8. הקשר תכנוני שלא נכלל בעבודה (תיעדוף מודע)

האפשרויות הבאות **לא בוצעו** במכוון:

- ❌ **ווידג'ט "Now Playing" בקטלוג עם החלפת שיר** — היה דורש תחזוקה (בכל פוסט / שבוע צריך לעדכן). Cost > value בשלב הזה.
- ❌ **פוסט חדש `blog-night-music.html`** — overkill לבקשה "אנושי קצת יותר". יוצר עוד placeholder בקטלוג שלא יוכר.
- ❌ **API endpoint לסאונדטרקים** — הבלוג סטטי, אין צורך.
- ❌ **שינוי בנווטים / `shared.js`** — אין צורך, השינויים נמצאים בתוך ה-`<article>`.
- ❌ **autoplay** — בכוונה כבוי, חוויית משתמש גרועה ב-mobile.

---

## 9. עדכון מומלץ ל-`MEMORY.md`

הצעה לרישום ב-`memory/`:

```md
- [Blog Soundtrack 26.4](project_blog_soundtrack_20260426.md) — commit fd3bfd4: blog-legacy-code.html קיבל סקציית `.soundtrack-box` עם YouTube embed (Mtp3QIKHnjk, privacy mode), blog.html קיבל author-signoff. תקדים reusable לפוסטים עתידיים. Telegram notification דולג (env var חסר).
```

---

## 10. סיכום מנהלים (1 שורה)

הבלוג עכשיו מרגיש קצת פחות "institutional", עם שיר אחד שנשמע ברקע ושורת חתימה אחת — כל זה בלי לטשטש את העיצוב המקצועי, ובלי תחזוקה שוטפת. ✅ Production live, GitHub Pages confirmed serving.

---

*Generated: 2026-04-26 by Claude · Saved to `ops/SESSION_HANDOFF_20260426_BLOG_SOUNDTRACK.md`*
