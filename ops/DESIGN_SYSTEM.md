# SLH Design System v1.0

**CSS:** `website/css/slh-design-system.css`
**JS helpers:** `website/js/slh-nav.js`, `website/js/slh-skeleton.js`

---

## 1. Design Tokens
CSS custom properties exposed at `:root` and `[data-theme="..."]`. Never hardcode colors or spacing — always reference a token (`var(--color-brand-primary)`, `var(--space-4)`, `var(--radius-md)`).

## 2. Color Modes
5 themes supported via `data-theme` on `<html>`: `dark` (default), `light`, `midnight`, `forest`, `sunset`. All tokens remap automatically.

## 3. Typography
- Primary: `Rubik` (400/500/600/700)
- Mono: `Space Mono`
- Scale: `--font-size-xs` → `--font-size-4xl`
- Line-height tokens: `--line-height-tight | normal | relaxed`

## 4. Spacing + Radius
- Spacing: 8-step scale `--space-1` (0.25rem) → `--space-10` (5rem)
- Radius: `--radius-sm | md | lg | xl | full`

## 5. Components
Prebuilt classes: `.card`, `.btn`, `.btn-primary`, `.btn-secondary`, `.alert`, `.alert-error`, `.alert-success`, `.badge`, `.chip`, `.input`, `.select`, `.table`.

## 6. RTL + i18n
All components use logical properties (`padding-inline-start`, `margin-inline-end`). Language switching via `js/translations.js`. Dir is set on `<html>` by language (`he`/`ar` → `rtl`).

## 7. Accessibility
- Focus rings on all interactive elements (`:focus-visible`)
- `prefers-reduced-motion` disables animations
- ARIA tokens: `aria-busy`, `aria-live`, `role="alert"` on error states
- Min tap target 44px
- Contrast ≥ AA on all themes

## 8. Unified Nav (`js/slh-nav.js`)
Role-based menu, RTL-aware, mobile drawer. Initializes on DOMContentLoaded. Drops into any page: `<script src="/js/slh-nav.js"></script>`.

## 9. BETA Banner + Bug FAB (`js/shared.js`)
Floating 🐛 button opens `/bug-report.html?source=<page>`. BETA banner top-of-page. Both auto-inject on every page via `shared.js`.

---

## 10. Skeleton Loaders (`js/slh-skeleton.js`)

Shimmer placeholders while data loads. Two ways to use:

### Declarative (HTML attributes)
```html
<div data-skeleton="card" data-lines="4"></div>
<div data-skeleton="text" data-lines="3"></div>
<div data-skeleton="list" data-count="5"></div>
<div data-skeleton="avatar"></div>
<div data-skeleton="title"></div>

<!-- Auto-clear after 5s -->
<div data-skeleton="card" data-skeleton-auto="5000"></div>
```
Skeleton auto-applies on DOMContentLoaded. Remove manually: `SLHSkeleton.reveal(el, contentHtml)`.

### Imperative (JS API)
| Method | Purpose |
|---|---|
| `SLHSkeleton.show(el, type, opts)` | Save original content, inject skeleton, set `aria-busy` |
| `SLHSkeleton.hide(el)` | Restore original content |
| `SLHSkeleton.withSkeleton(target, fetchFn, type)` | Wrap a promise, auto-hide on resolve/reject |
| `SLHSkeleton.fetchJson(target, url, opts, type)` | Convenience wrapper around `fetch().then(r=>r.json())` |
| `SLHSkeleton.apply(root)` | Re-scan DOM for `[data-skeleton]` elements |
| `SLHSkeleton.reveal(el, content)` | Remove skeleton + optionally set content |
| `SLHSkeleton.track(promise, el, options)` | Chain skeleton with a promise + success/error template |
| `SLHSkeleton.createSkeleton(type, opts)` | Build a skeleton node (no insertion) |

### Types
- `text` — N lines (default 3), last line 60% width
- `title` — single 60%-width bar
- `avatar` — 2.5rem circle
- `card` — title + N text lines
- `list` — N rows of avatar+2-line

### Recipe: fetch + render + skeleton
```js
SLHSkeleton.withSkeleton('#leaderboard', async () => {
  const r = await fetch('/api/sudoku/leaderboard');
  return r.json();
}, 'list', { count: 10 }).then(data => {
  document.getElementById('leaderboard').innerHTML =
    data.map(p => `<div>${p.rank}. ${p.name} — ${p.score}</div>`).join('');
});
```

### CSS
Skeleton classes live in `slh-design-system.css`:
- `.skeleton` — shimmer background, rounded
- `.skeleton-text` — 1em-height line
- `.skeleton-title` — 1.5em-height, 60% width
- `.skeleton-avatar` — circle

Honors `prefers-reduced-motion` via design-system animation guards.
