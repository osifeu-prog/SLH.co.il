# E — Frontend Audit
**164 דפי HTML — osifeu-prog.github.io**
**נוצר:** 2026-05-04

---

## 📊 סיכום

| מדד | מצב | יעד |
|-----|-----|-----|
| סה"כ דפים | 164 | 164 |
| `data-theme="neural"` | **21** (13%) | 164 (100%) |
| `translations.js` / `data-i18n` | **64** (39%) | 164 (100%) |
| שניהם | 9 (5%) | 164 |
| שניהם חסרים | **88** (54%) | 0 |

---

## 🔴 P1 — דפים ליבה (לתקן ראשון)

14 דפים שמשתמשים רואים — **IDO-critical**:

| דף | neural | i18n | פעולה |
|----|--------|------|-------|
| `index.html` | ✅ | ✅ | — |
| `wallet.html` | ✅ | ✅ | — |
| `whitepaper.html` | ✅ | ✅ | — |
| `investors.html` | ✅ | ✅ | — |
| `genesis.html` | ✅ | ✅ | — |
| `ido.html` | ✅ | ❌ | הוסף i18n |
| `disclosure.html` | ✅ | ❌ | הוסף i18n |
| `founder.html` | ✅ | ❌ | הוסף i18n |
| `pitch.html` | ✅ | ❌ | הוסף i18n |
| `nft-cards.html` | ✅ | ❌ | הוסף i18n |
| `dashboard.html` | ❌ | ✅ | הוסף neural |
| `earn.html` | ❌ | ✅ | הוסף neural |
| `join.html` | ❌ | ❌ | הוסף שניהם |
| `profile.html` | ❌ | ❌ | הוסף שניהם |

---

## 🟠 P2 — Admin Panel (12 דפים)

| דף | neural | i18n |
|----|--------|------|
| `admin.html` | ✅ | ✅ |
| `admin/bot-registry.html` | ✅ | ❌ |
| `admin/control-center.html` | ❌ | ❌ |
| `admin/devices-catalog.html` | ❌ | ❌ |
| `admin/ido-mission-control.html` | ❌ | ❌ |
| `admin/mission-control.html` | ❌ | ❌ |
| `admin/reality.html` | ❌ | ❌ |
| `admin/rotate-token.html` | ❌ | ❌ |
| `admin/rotation-history.html` | ❌ | ❌ |
| `admin/secrets-vault.html` | ❌ | ❌ |
| `admin/security-hub.html` | ❌ | ❌ |
| `admin/tokens.html` | ❌ | ❌ |
| `admin/therapists.html` | ❌ | ❌ |

---

## 🟠 P2 — דפים עם i18n, חסר neural (20 דפים — הוסף theme בלבד)

```
agent-brief.html
analytics.html
blockchain.html
bots.html           ← ALSO: תוכן חסר ("Coming Soon")
broadcast-composer.html
buy.html
challenge.html
community.html
control-center.html
daily-blog.html
dashboard-therapist.html
dashboard.html
dex-launch.html
earn.html
ecosystem-guide.html
for-therapists.html
getting-started.html
guides.html
healing-vision.html
invite.html
+ עוד 20 נוספים
```

---

## 🟡 P3 — Blog (17 דפים)

כולם חסרי neural ו-i18n. אפשר לעשות batch migration אחד:

```
blog/aic-ai-credits-guide.html
blog/anti-facebook-manifesto.html
blog/crypto-yoga-attention.html
blog/dating-without-algorithm.html
blog/earn-crypto-sudoku.html
blog/expert-verification-process.html
blog/how-to-buy-slh-israel.html
blog/index.html
blog/neurology-meets-meditation.html
blog/slh-community-join-guide.html
blog/slh-ecosystem-map.html
blog/slh-token-for-beginners.html
blog/slh-vs-other-networks.html
blog/ton-vs-bsc-comparison.html
+ 3 נוספים
```

---

## 🟡 P3 — Academy (2 דפים)

```
academia.html
academy/course-1-dynamic-yield.html
academy/course-1-dynamic-yield/calculator.html
```

---

## 🔴 Bugs ידועים — לתקן לפני IDO

### 1. `/tokens.html` — 404
מקושר מהדף הראשי בכרטיס "5 Tokens". הדף לא קיים.  
**פעולה:** צור `tokens.html` עם תוכן 5 הטוקנים.

### 2. `/bots.html` — ריק
מציג "Coming Soon" בלבד אבל מקושר מ-3 דפים.  
**פעולה:** מלא עם 25 בוטים, תיאור קצר לכל אחד.

### 3. Supply inconsistency — 3 מספרים שונים
| דף | מספר |
|----|------|
| `index.html` | 110.75M |
| `network.html` | 111M |
| `whitepaper.html` | 1,000,000,000 (!) |
**פעולה:** עדכן לכולם: **110,750,000 SLH**

### 4. Whitepaper — Founder שגוי
`whitepaper.html` כותב "Zvika Kaufman — Founder & Lead Developer"  
**פעולה:** תקן ל: "Osif Kaufman Ungar — Founder & Lead Developer"

### 5. Staking plans — ריגולטורי
`dashboard.html` + `whitepaper.html` מבטיחים "4%-5.4% monthly" ללא asterisk.  
**פעולה:** הוסף: `*תשואה משתנה, אינה מובטחת`

---

## ⚡ Migration Template — כיצד להוסיף neural + i18n לדף

```html
<!-- 1. ב-<html> tag — הוסף: -->
<html lang="he" dir="rtl" data-theme="neural">

<!-- 2. ב-<head> — הוסף CSS (אחרי קישורי CSS קיימים): -->
<link rel="stylesheet" href="/css/slh-neural.css">

<!-- 3. ב-<body> — הוסף script (לפני </body>): -->
<script src="/js/translations.js"></script>
<script src="/js/shared.js"></script>

<!-- 4. לטקסטים שרוצים לתרגם — הוסף data-i18n: -->
<h1 data-i18n="page.title">כותרת</h1>
<p data-i18n="page.desc">תיאור</p>
```

**batch migration script (PowerShell):**
```powershell
# מוסיף data-theme="neural" לכל HTML שחסר
$pages = Get-ChildItem -Path "D:\SLH_ECOSYSTEM\website" -Filter "*.html" -Recurse |
    Where-Object { (Get-Content $_.FullName -Raw) -notmatch 'data-theme="neural"' }

foreach ($page in $pages) {
    $content = Get-Content $page.FullName -Raw
    # החלף <html> → <html data-theme="neural">
    $new = $content -replace '<html([^>]*lang="he"[^>]*)>', '<html$1 data-theme="neural">'
    # אם אין lang="he" כלל:
    if ($new -eq $content) {
        $new = $content -replace '<html>', '<html lang="he" dir="rtl" data-theme="neural">'
    }
    Set-Content $page.FullName $new -Encoding UTF8
    Write-Host "Updated: $($page.Name)"
}
```

---

## 📋 עדיפויות לפי שבוע

| שבוע | מה | דפים |
|------|----|------|
| 1 | P1 core — i18n לדפי IDO | ido, disclosure, founder, pitch, nft-cards (5 דפ') |
| 1 | P1 core — neural לdashboard, earn, join, profile | 4 דפים |
| 2 | Admin panel — batch neural+i18n | 12 דפים |
| 2 | bug fixes: tokens.html + bots.html + supply fix | — |
| 3 | Batch neural לכל "neural NO, i18n YES" | ~20 דפים |
| 4 | Blog batch migration | 17 דפים |
| 5+ | שאר 88 דפי "both NO" | בהתאם לעדיפות |
