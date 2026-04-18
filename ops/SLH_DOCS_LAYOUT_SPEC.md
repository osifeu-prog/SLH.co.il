# SLH Docs Layout — Design Spec
**Status:** Spec / Backlog · **Priority:** P1 · **Effort:** ~12-16h for full rollout
**Inspired by:** Microsoft Learn, Stripe Docs, Notion Docs, Vercel Docs
**Goal:** Turn every long-form content page on slh-nft.com into a modern, dynamic, docs-style experience.

---

## 1. Why

Today our content pages (`whitepaper.html`, `guides.html`, `wallet-guide.html`, `ecosystem-guide.html`, `roadmap.html`, `for-therapists.html`, `healing-vision.html`, `onboarding.html`, `getting-started.html`, `jubilee.html`) are long scrolls with no navigation aid. Users get lost. The docs-layout Osif saw on `learn.microsoft.com` has 4 superpowers:

1. **Left tree nav** — shows your place in the whole docs hierarchy
2. **Right "In this article" TOC** — auto-scroll-spy, always know where you are
3. **Breadcrumbs** — one-click jump up
4. **Feedback + edit-on-GitHub + last-updated** — builds trust

We bolt these onto our existing `slh-design-system.css` — we don't replace it.

---

## 2. Architecture

```
┌─────────────────────────────────────────────────────────────┐
│ Top bar · logo · search · lang · theme · signin             │  sticky
├──────────┬──────────────────────────────────────┬───────────┤
│          │ Breadcrumb: Home › Guides › Wallet    │           │
│          ├──────────────────────────────────────┤           │
│  Left    │                                      │  Right    │
│  Tree    │   <main content — article body>     │  "In this │
│  Nav     │                                      │  article" │
│          │   H1                                 │  TOC       │
│ (250px)  │   H2 ────────── scroll-spy ──────    │  (220px)   │
│          │   p                                  │            │
│ loaded   │   H2                                 │  auto from │
│ from     │   p                                  │  H2/H3     │
│ manifest │                                      │            │
│          ├──────────────────────────────────────┤            │
│          │ ✅ Was this helpful?   Edit on GitHub │           │
│          │ Last updated: 2026-04-18              │           │
├──────────┴──────────────────────────────────────┴───────────┤
│ Bottom bar · copyright · privacy · terms · contact           │
└─────────────────────────────────────────────────────────────┘
```

- **Desktop** (≥1200px): 3 columns as shown
- **Tablet** (768-1199px): collapse right TOC into floating button
- **Mobile** (<768px): both side panels become drawers from top

---

## 3. Files to create

| File | Role | LOC (est.) |
|------|------|-----------|
| `website/css/slh-docs.css` | Layout + components | ~350 |
| `website/js/slh-docs.js` | TOC autogen, scroll-spy, drawer toggle, breadcrumb, search | ~250 |
| `website/docs-manifest.json` | Sidebar structure (single source of truth) | ~80 |
| `website/templates/docs-page.html` | Reference template, copy-paste boilerplate | ~60 |
| API: `GET /api/docs/manifest` | Live-serve manifest (future — for dynamic edits without redeploy) | — |

---

## 4. Sidebar manifest format

`website/docs-manifest.json`:

```json
{
  "version": 1,
  "updated_at": "2026-04-18",
  "sections": [
    {
      "title": "התחלה",
      "icon": "🚀",
      "items": [
        {"title": "מהו SLH?", "url": "/index.html"},
        {"title": "שלבים ראשונים", "url": "/getting-started.html"},
        {"title": "Onboarding", "url": "/onboarding.html"}
      ]
    },
    {
      "title": "ארנק ותשלומים",
      "icon": "💳",
      "items": [
        {"title": "מדריך ארנק", "url": "/wallet-guide.html"},
        {"title": "תשלום", "url": "/pay.html"},
        {"title": "P2P", "url": "/p2p.html"}
      ]
    },
    {
      "title": "מסחר ועסקאות",
      "icon": "📈",
      "items": [
        {"title": "מסחר", "url": "/trade.html"},
        {"title": "סטייקינג", "url": "/staking.html"},
        {"title": "Launch Event", "url": "/launch-event.html"}
      ]
    },
    {
      "title": "קהילה",
      "icon": "👥",
      "items": [
        {"title": "קהילה", "url": "/community.html"},
        {"title": "בלוג יומי", "url": "/daily-blog.html"},
        {"title": "הפניות", "url": "/referral.html"}
      ]
    },
    {
      "title": "תיעוד",
      "icon": "📚",
      "items": [
        {"title": "Whitepaper", "url": "/whitepaper.html"},
        {"title": "מדריכים", "url": "/guides.html"},
        {"title": "מפת המערכת", "url": "/ecosystem-guide.html"},
        {"title": "Roadmap", "url": "/roadmap.html"}
      ]
    }
  ]
}
```

Page marks itself active via `<body data-docs-page="/wallet-guide.html">`.
Sidebar highlights that item and auto-expands its section.

---

## 5. Page template

Any page opts in with 5 lines:

```html
<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
  <link rel="stylesheet" href="/css/slh-design-system.css">
  <link rel="stylesheet" href="/css/slh-docs.css">           <!-- NEW -->
  <script src="/js/slh-docs.js" defer></script>              <!-- NEW -->
</head>
<body class="docs-layout" data-docs-page="/wallet-guide.html" <!-- NEW -->
      data-docs-breadcrumb='[{"title":"בית","url":"/"},{"title":"מדריכים","url":"/guides.html"},{"title":"ארנק"}]'>
  <article class="docs-article">
    <h1>מדריך ארנק</h1>
    <h2 id="setup">התקנה</h2>
    <p>...</p>
    <h2 id="backup">גיבוי</h2>
    <p>...</p>
  </article>
</body>
</html>
```

`slh-docs.js` on load:
1. Wraps `<article>` in the 3-column layout
2. Fetches `/docs-manifest.json` → builds left sidebar
3. Scans `h2, h3` in `<article>` → builds right TOC (auto-IDs if missing)
4. Reads `data-docs-breadcrumb` → renders breadcrumb bar
5. Attaches IntersectionObserver → scroll-spy highlights current section
6. Injects feedback + "edit on GitHub" + last-updated footer (from `<meta name="docs-updated">`)

---

## 6. Dynamic layer (Phase 2)

Static JSON works fine for v1. Phase 2 moves it to the API:

```
GET /api/docs/manifest → live JSON (same shape) from PostgreSQL `docs_nav` table
POST /api/docs/manifest/reorder → admin-only, drag-drop reorder in admin panel
GET /api/docs/toc/:slug → server-side extracted headings (for pages that need auth-gated content)
```

This unlocks: editing the sidebar from the admin panel without a website redeploy.

---

## 7. Components (on top of existing design tokens)

All reuse `slh-design-system.css` tokens — no new colors:

- `.docs-layout` — the 3-column grid
- `.docs-sidebar` — left tree
- `.docs-sidebar__section` / `.docs-sidebar__item` / `.docs-sidebar__item--active`
- `.docs-toc` — right TOC, position: sticky; top: var(--topbar-h)
- `.docs-toc__item` / `.docs-toc__item--active`
- `.docs-breadcrumb` — above article
- `.docs-article` — typography + spacing
- `.docs-feedback` — bottom helpful/not helpful
- `.docs-meta` — last-updated + edit-on-GitHub
- `.docs-search` — sidebar-top quick filter

---

## 8. Accessibility

- Skip link: "דלג לתוכן הראשי" (match MS Learn's pattern)
- Sidebar: `<nav aria-label="ניווט תיעוד">`, each section `<h2>`
- TOC: `<nav aria-label="בתוך המאמר">`, aria-current="location" on active
- All drawers: focus-trap when open, ESC closes, `aria-expanded` on trigger
- Color contrast ≥ AA in all 5 themes (already guaranteed by `slh-design-system.css`)
- Touch targets ≥ 44px

---

## 9. Rollout plan

| Phase | Pages | Effort | When |
|-------|-------|--------|------|
| **P1 · Foundation** | Build `slh-docs.css` + `slh-docs.js` + manifest + prototype on `whitepaper.html` | 4h | Session A |
| **P2 · Core content** | Roll to `guides.html`, `wallet-guide.html`, `ecosystem-guide.html`, `roadmap.html` | 3h | Session A/B |
| **P3 · Vision pages** | `for-therapists.html`, `healing-vision.html`, `jubilee.html` | 2h | Session B |
| **P4 · Onboarding** | `getting-started.html`, `onboarding.html`, `daily-blog.html` | 2h | Session B |
| **P5 · Admin docs** | `admin-guide.html` (new) — operator runbook | 3h | Session C |
| **P6 · Dynamic** | API endpoints + admin UI for manifest editing | 4h | Session C |

Total: **~18h** for full rollout. Foundation alone = **4h**.

---

## 10. Success metrics

| Metric | Before | Target |
|--------|--------|--------|
| Pages with docs-layout | 0/10 | 10/10 |
| Avg time-on-page (content pages) | baseline | +40% |
| Bounce rate on guides | baseline | -25% |
| "Was this helpful? Yes" rate | — | ≥75% |

---

## 11. Open questions

- Should sidebar also appear on non-content pages (dashboard, trade)? → **No.** Those get their own app-shell. Docs-layout is content-only.
- RTL breadcrumb direction? → Mirror ‹ becomes › automatically via `dir="rtl"` + `flex-direction: row-reverse` + logical properties.
- Search inside sidebar — client-side only for v1. v2 can hit `GET /api/search/docs?q=...`.
- Multi-lang: sidebar items use `title` per current language. Manifest can grow `title_he / title_en / title_ru / title_ar`.

---

## Files touched (rollout)

```
NEW:
  website/css/slh-docs.css
  website/js/slh-docs.js
  website/docs-manifest.json
  website/templates/docs-page.html

MODIFIED (add 3 lines each):
  website/whitepaper.html
  website/guides.html
  website/wallet-guide.html
  website/ecosystem-guide.html
  website/roadmap.html
  website/for-therapists.html
  website/healing-vision.html
  website/jubilee.html
  website/getting-started.html
  website/onboarding.html
  website/daily-blog.html
```
