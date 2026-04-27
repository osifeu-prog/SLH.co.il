# SLH Neural — Migration Plan
**Date:** 2026-04-27
**Author:** Claude (Cowork mode session)
**Goal:** Apply the new SLH Neural design system to all 140 pages without breaking anything.

---

## What was delivered in this session

### New files (zero impact on existing pages)
- `website/css/slh-neural.css` — Design system extension (~480 lines)
- `website/landing-v2.html` — Prototype investor landing page using the new system

### Why the existing site is untouched
The new CSS file:
- Adds a **new theme** `[data-theme="neural"]` — only activates when explicitly set
- Adds **new component classes** prefixed with `.neural-*` — no collisions with existing classes
- Loads **after** `shared.css` so it can override safely when needed
- Falls back gracefully on browsers that don't support `backdrop-filter`

You can preview the prototype at `https://slh-nft.com/landing-v2.html` after the next GitHub Pages deploy.

---

## Design system at a glance

### CSS variables (in `[data-theme="neural"]`)
| Variable | Value | Purpose |
|----------|-------|---------|
| `--bg`, `--bg2`, `--bg3` | Deep cosmic blues | Backgrounds |
| `--surface`, `--surface2` | Translucent panels | Glassmorphism cards |
| `--accent` | `#5ed6ff` | Synaptic cyan — primary CTA |
| `--accent2` | `#b18bff` | Neuron purple — secondary |
| `--gold` | `#ffd166` | SLH token premium |
| `--token-slh/mnh/zvk/rep/zuz` | per-token colors | Token visualizations |
| `--glow-cyan/purple/gold` | Neon shadow values | Glow effects |

### Component classes
| Class | Use |
|-------|-----|
| `.neural-bg` | Animated grid + radial-gradient background (fixed, z-index -1) |
| `.neural-card` | Glassmorphism card with hover scan-line |
| `.neural-headline` | Gradient hero text |
| `.neural-eyebrow` | Pill label above headline (with pulsing dot) |
| `.neural-btn`, `.neural-btn-primary/ghost/gold` | CTA buttons with glow |
| `.neural-stat` | KPI tile (large gradient number + label) |
| `.token-node[data-token="..."]` | Animated token visualization with pulsing rings |
| `.synapse-line` | SVG line with animated dash flow |
| `.dna-divider` | Section divider with DNA helix SVG |
| `.roadmap-timeline` + `.roadmap-item.done/.active` | Timeline component |
| `.trust-badge` | Audit/contract badge with status dot |
| `.live-indicator` | Pulsing "LIVE" indicator |

### Design principles enforced
- **Hebrew first**: `dir="rtl"`, `lang="he"`, Heebo font primary
- **English code**: All class names and IDs in English
- **Accessibility**: `prefers-reduced-motion` honored; ARIA labels on visuals
- **Performance**: Pure CSS animations (GPU-accelerated), no JS framework
- **Theme coexistence**: Doesn't break existing `[data-theme="terminal/crypto/light/cyberpunk"]`

---

## Phase 1: Validate the prototype (30 min — Osif manual)

1. Push `slh-neural.css` and `landing-v2.html` to the `osifeu-prog/osifeu-prog.github.io` repo:
   ```powershell
   cd D:\SLH_ECOSYSTEM\website
   git add css/slh-neural.css landing-v2.html
   git commit -m "feat: SLH Neural design system + landing-v2 investor prototype"
   git push origin main
   ```
2. Wait 1-2 min for GitHub Pages deploy.
3. Open `https://slh-nft.com/landing-v2.html` on:
   - Desktop Chrome (sanity check)
   - Mobile Chrome (responsive check)
   - Mobile Safari (backdrop-filter compatibility)
4. Send the link to a couple of trusted people (Tzvika, Zohar) — get gut reactions.
5. **Decision point:** Does this feel "investor grade"? If yes, proceed to Phase 2. If no, share the specific feedback in the next session.

---

## Phase 2: High-impact pages (next session — ~3 hours)

Apply the neural theme to the **5 most visible pages** first. These are the ones investors and contributors actually open:

| Page | Why first | Migration approach |
|------|-----------|--------------------|
| `index.html` | Homepage — first impression | Set `data-theme="neural"`, swap hero to use `.neural-headline` + token constellation |
| `about.html` | Investor reads this second | Add `.neural-card` for team bios, `.dna-divider` between sections |
| `tokens.html` | Tokenomics page | Use `.neural-card` per token, `.token-node` for visual identity |
| `wallet.html` | First page after signup | `.neural-stat` for balances, `.live-indicator` for sync status |
| `admin.html` | Daily-use page for the team | Set theme, use `.neural-card` for sidebar items |

### Migration recipe per page
```html
<!-- 1. Add data-theme to <html> -->
<html lang="he" dir="rtl" data-theme="neural">

<!-- 2. Add the neural CSS after shared.css -->
<link rel="stylesheet" href="css/shared.css?v=...">
<link rel="stylesheet" href="css/slh-neural.css?v=...">

<!-- 3. Add the ambient background as first child of <body> -->
<body>
  <div class="neural-bg" aria-hidden="true"></div>
  ...

<!-- 4. Replace ad-hoc hero/cards with .neural-* components -->
```

### Before/after example
**Before** (current pattern):
```html
<div class="card" style="background:#14142b; padding:24px;">
  <h3 style="color:#a29bfe">Title</h3>
  <p>Content</p>
</div>
```
**After** (neural pattern):
```html
<article class="neural-card">
  <div class="card-icon"><i class="fas fa-bolt"></i></div>
  <h3>Title</h3>
  <p style="color:var(--text2);">Content</p>
</article>
```

---

## Phase 3: Bulk migration (sessions 3-4 — ~4 hours total)

Migrate the remaining **~135 pages** using sub-agents in parallel:
- Batch 1: Marketing/info pages (about, faq, contact, careers) — visual upgrade only
- Batch 2: Product pages (botshop, factory, game, airdrop) — keep functionality, refresh visuals
- Batch 3: Admin sub-pages (admin/*.html) — use `.neural-card` for sidebar items
- Batch 4: Blog & academy (blog/*, academy/*) — long-form readable variant of the theme
- Batch 5: Mini-apps (miniapp/*) — Telegram-themed adaptation

### Why sub-agents
Each batch can be delegated to a parallel sub-agent with a clear template:
> "For each HTML file in `website/[batch-folder]/`, set `data-theme='neural'`, add `<link rel='stylesheet' href='css/slh-neural.css'>` after `shared.css`, and add `<div class='neural-bg'></div>` as the first child of `<body>`. Do NOT modify any existing class names or scripts."

This is a **safe, mechanical change** that doesn't touch business logic.

---

## Phase 4: New investor pages (session 5 — ~2 hours)

Build dedicated investor materials using the design system:
- `investors.html` — Pitch deck embedded, video, contact form
- `tokenomics.html` — Interactive supply/demand visualization
- `audit-status.html` — Live contract verification, audit reports
- `team.html` — Founder bio, advisors, contributors

---

## Phase 5: ESP32 integration (session 6 — ~3 hours)

Connect the device-registry to the website:
- New page `devices.html` — User can see their paired ESP32 devices
- Use `.neural-card` per device with `.live-indicator` for connection status
- Live data via `/api/devices/list/{user_id}` endpoint (if not exists, build it)
- QR pairing flow with neural-themed scanner overlay

---

## Cleanup tasks (parallel to all phases)

These don't block the design migration but should be done during the same window:

- [ ] Move 7 `docker-compose.yml.backup-*` files into `_backups/` subfolder
- [ ] Move `main.py.bak_20260422_162309` into `_backups/`
- [ ] Delete `website/js/shared.js.backup_*` (2 files) after confirming current shared.js is good
- [ ] Update `CLAUDE.md` with new endpoint count after each session
- [ ] Add `.gitignore` entries for `*.bak`, `*.backup-*`, `*.bak_*` patterns

---

## Risk register

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| backdrop-filter unsupported on old browsers | Low | Already has fallback to solid color via `var(--surface)` |
| RTL layout issue with new components | Medium | Test landing-v2.html on real Hebrew content first |
| Existing JS depends on specific class names | Low | We only ADD classes, never remove |
| Theme switcher doesn't include "neural" | Medium | Update `js/shared.js` theme switcher in Phase 2 |
| Investor reactions don't match "DNA/neural" vision | Medium | Get 3 quick gut reactions before Phase 2 |

---

## Success metrics

After Phase 2 completion (5 pages migrated):
- All 5 pages should look visually consistent — common header, common card style, common buttons
- Mobile responsive (verified in mobile Safari + Chrome)
- Page weight added < 30KB (CSS) per page
- No regressions in existing functionality (admin login, wallet linking, etc.)
- Lighthouse score: Performance > 85, Accessibility > 90

After Phase 5 completion (full migration):
- 100% of pages on neural theme by default (others available as alternates)
- Investor pack live at `/investors.html`
- ESP32 dashboard live at `/devices.html`
- Ready for institutional pitch
