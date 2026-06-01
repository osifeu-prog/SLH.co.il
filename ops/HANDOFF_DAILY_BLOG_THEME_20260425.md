# Handoff — daily-blog.html Theme Switcher Fix + Deploy Procedure

**Date:** 2026-04-25
**Session length:** ~1 short session
**Primary goal:** raise daily-blog.html from 4/5 to 5/5 by adding the theme switcher infrastructure
**Secondary goal:** turn the deploy step into a repeatable procedure with auto-notification to @SLH_Claude_bot
**Status:** ✅ All edits done & verified locally · ⏳ Awaiting Osif to run the push

---

## 1. Executive summary

The Project Map flagged daily-blog.html as missing a theme switcher. Investigation revealed `js/shared.js` already exposes a complete theme system (7 variants) and auto-runs `initShared()` on every page — the actual gap was a 1-line `data-theme` attribute and a tiny FOUC-prevention bootstrap. A 600-line rewrite proposed in an earlier draft would have deleted all 7 existing blog entries and called 5 non-existent globals — rejected.

Final fix is **+8 / −1 lines** in daily-blog.html. Two new ops files codify the deploy procedure so future single-page updates take one command.

---

## 2. What was done

### 2.1 daily-blog.html (4 surgical edits)

| # | Change | Line |
|---|--------|------|
| 1 | `<html lang="he" dir="rtl">` → `<html lang="he" dir="rtl" data-theme="dark">` | 2 |
| 2 | Inserted FOUC-prevention bootstrap `<script>` after `<meta charset>` | 5–11 |
| 3 | Removed duplicate `<div id="footer-root"></div>` | (was 763) |
| 4 | Added `<script src="/js/web3-wallet.js?v=20260426a" defer>` after ai-assistant.js | (now 788) |

**Untouched:** all 7 existing static blog post articles (Day 1–7), `.blog-hero` styles, `.blog-entry` styles, `initShared({ activePage: 'blog' })` wiring, the `topnav-root` / `bottomnav-root` / `footer-root` containers (one of two `footer-root`s preserved at the bottom).

**File grew from 785 → 790 lines** (+5 net).

### 2.2 ops/slh-push.ps1 (new, 96 lines)

PowerShell wrapper that:
1. Stages an explicit file list (`-Files "a","b"`) — **never** `git add -A` or `.`
2. Commits with the supplied `-Message` (no `--no-verify`)
3. Pushes to `origin/$Branch` (default `main`)
4. Notifies `@SLH_Claude_bot` via the existing `POST /api/broadcast/send` endpoint, using `$env:SLH_ADMIN_BROADCAST_KEY` (skipped with warning if env var unset; push still succeeds)

Honest correction baked into the docstring: git has **no** native `post-push` hook. The closest alternatives (`pre-push`, server-side `post-receive`) don't fit this case. This wrapper IS the post-push hook.

### 2.3 ops/PROC_HTML_PAGE_UPDATE.md (new, 116 lines)

Active procedure document covering:
- Pre-conditions (env var, clean working tree)
- 6-step flow (edit → local verify → diff → push wrapper → confirm live → telegram check)
- Commit message format (`<type>(<page>): <description>`)
- Rollback (`git revert HEAD --no-edit && git push`)
- Failure-mode table (file-not-found, hook reject, push reject, notify fail, CDN cache)
- When NOT to use this procedure (multi-file, schema, env vars, secrets)

---

## 3. Verification (local, port 8899)

Server: `python -m http.server 8899 --directory D:/SLH_ECOSYSTEM/website` (already configured in `D:\.claude\launch.json`).

| Check | Expected | Got |
|-------|----------|-----|
| URL | `/daily-blog.html` | ✅ `/daily-blog.html` |
| `<html>` has `data-theme` on first paint | `dark` (FOUC fix) | ✅ `dark` |
| `localStorage.slh_theme` reads correctly | `dark` (default) | ✅ `dark` |
| Scripts loaded | translations, shared, analytics, ai-assistant, web3-wallet | ✅ all 5 |
| `#footer-root` count | exactly 1 | ✅ 1 |
| `#topnav-root` rendered (initShared fired) | yes | ✅ yes |
| `#footer-root` rendered (initShared fired) | yes | ✅ yes |
| `data-i18n` keys on page | several | ✅ 47 |
| Console errors | zero | ✅ zero |
| `setTheme('crypto')` → reload → still crypto | persists | ✅ `data-theme="crypto"`, bg `rgb(12,0,20)` |
| Theme reset to dark before handoff | yes | ✅ done |

**Untested (out of scope here):**
- Mobile responsive layout (no resize check this session)
- Each of the 7 themes' visuals (only `dark` and `crypto` were toggled)
- Live deploy through CDN (haven't pushed yet)

---

## 4. ⚠️ IMPORTANT — Outstanding state in website repo

When this session started, the website working tree already had THREE other files dirty (not touched by this session):

```
 M admin/rotate-token.html
 M admin/tokens.html
 M miniapp/dashboard.html
 M daily-blog.html       ← this session
```

**The wrapper script is safe** — it only stages files passed via `-Files`. But please verify before pushing:
```powershell
cd D:\SLH_ECOSYSTEM\website
git status              # confirm 4 modified files
git diff daily-blog.html | head -40
```

If you want to push the other 3 alongside daily-blog.html, pass them all to the wrapper:
```powershell
D:\SLH_ECOSYSTEM\ops\slh-push.ps1 `
  -Files "daily-blog.html","admin/rotate-token.html","admin/tokens.html","miniapp/dashboard.html" `
  -Message "<combined description>"
```
Otherwise pass only `daily-blog.html` and leave the other 3 dirty for later.

The 2 new ops files (`slh-push.ps1`, `PROC_HTML_PAGE_UPDATE.md`) are in the **api repo** (`D:\SLH_ECOSYSTEM\.git` → `origin/master`), not the website repo. They are currently untracked there.

---

## 5. Push procedure (Osif runs this)

### 5.1 One-time per shell — set the broadcast key

```powershell
# Get the value from Railway dashboard env vars (ADMIN_API_KEYS or ADMIN_BROADCAST_KEY).
# Per memory: "Never Paste Secrets" — do NOT paste the value into chat.
$env:SLH_ADMIN_BROADCAST_KEY = "<paste_from_Railway>"
```

If the var is not set, the push still succeeds; only the Telegram notification skips with a warning.

### 5.2 Push the website change

```powershell
cd D:\SLH_ECOSYSTEM\website
git status                                  # sanity check
git diff daily-blog.html                    # review the +8/-1
D:\SLH_ECOSYSTEM\ops\slh-push.ps1 `
  -Files "daily-blog.html" `
  -Message "fix(daily-blog): data-theme bootstrap, web3-wallet.js, dedup footer-root"
```

Expected output:
```
OK Pushed 1 file(s) to origin/main (sha=<short>)
OK Telegram notification sent (sha=<short>)
```

### 5.3 Commit the new ops files (separately, in api repo)

```powershell
cd D:\SLH_ECOSYSTEM
git status ops/slh-push.ps1 ops/PROC_HTML_PAGE_UPDATE.md ops/HANDOFF_DAILY_BLOG_THEME_20260425.md
git add ops/slh-push.ps1 ops/PROC_HTML_PAGE_UPDATE.md ops/HANDOFF_DAILY_BLOG_THEME_20260425.md
git commit -m "ops: add slh-push.ps1 wrapper + HTML page update procedure"
git push origin master
```

(Why two pushes: website is `origin/main` of `osifeu-prog.github.io`, api is `origin/master` of `slh-api`. They are separate repos.)

### 5.4 Confirm live (~90s after website push)

```powershell
curl.exe -s https://slh-nft.com/daily-blog.html | Select-String "data-theme"
# Expected: <html lang="he" dir="rtl" data-theme="dark">
```

Open in browser, verify the top-nav 🎨 picker cycles themes, refresh persists choice.

### 5.5 Telegram check

Look for the deploy message in @SLH_Claude_bot's admins channel. Format:
```
[deploy] fix(daily-blog): ...
Branch: main
Commit: <sha>
Repo:   https://github.com/.../commit/<sha>
Files:
  - daily-blog.html
```

---

## 6. Rollback

If something breaks live:
```powershell
cd D:\SLH_ECOSYSTEM\website
git revert HEAD --no-edit
git push origin main
```
GitHub Pages re-deploys within ~90s. Manually post a revert message in @SLH_Claude_bot since `git revert` doesn't go through the wrapper.

---

## 7. Files reference

| Path | Type | Repo | Status |
|------|------|------|--------|
| `D:/SLH_ECOSYSTEM/website/daily-blog.html` | edited | website (origin/main) | dirty, ready to push |
| `D:/SLH_ECOSYSTEM/ops/slh-push.ps1` | new | api (origin/master) | untracked |
| `D:/SLH_ECOSYSTEM/ops/PROC_HTML_PAGE_UPDATE.md` | new | api (origin/master) | untracked |
| `D:/SLH_ECOSYSTEM/ops/HANDOFF_DAILY_BLOG_THEME_20260425.md` | new (this doc) | api (origin/master) | untracked |
| `C:/Users/Giga Store/.claude/plans/daily-blog-html-steady-seal.md` | plan | personal | reference only |

Untouched (verified, no edit needed):
- `D:/SLH_ECOSYSTEM/website/js/shared.js` — auto-init theme system already complete
- `D:/SLH_ECOSYSTEM/website/js/translations.js` — all 5 `blog_*` keys present in 5 languages (he/en/ru/ar/fr)
- `D:/SLH_ECOSYSTEM/website/css/shared.css` — 7 themes already defined under `[data-theme]`

---

## 8. Lessons captured (relevant for the next agent)

### 8.1 Stale memory entry contradicted by code
Memory previously said "initShared() never fires on 121 HTML pages." Reading `shared.js` lines 1599–1611 reveals an auto-init IIFE that wires `DOMContentLoaded` → `initShared()` for every page. Don't trust that memory entry — the code is the source of truth. Memory updated.

### 8.2 Brief-vs-reality gap
The Project Map said daily-blog.html was missing a theme switcher. Reality: shared.js already injects the theme picker into the top-nav on every page. The actual gap was a 1-line attribute + FOUC prevention. **Always read the actual code before accepting the brief at face value.**

### 8.3 Plan-mode rejection of a 600-line rewrite
An earlier draft proposed replacing the whole file with hand-rolled markup that called 5 non-existent globals (`window.applyTheme`, `window.AIAssistant.ask`, `window.Web3Wallet.connect`, `window.SharedNav.init`, `window.Analytics.pageView`). Surgical edits won — preserved 7 existing blog posts, reused shared.js, ~10 lines instead of ~600.

### 8.4 git has no `post-push` hook
For deploy notifications, the only correct pattern is a wrapper script that pushes then notifies. Anyone who proposes a `.git/hooks/post-push` is wrong about git's hook list.

---

## 9. For the next agent (clean slate prompt)

> The website repo (`D:\SLH_ECOSYSTEM\website\`) had 3 unrelated dirty files when this session ran (admin/rotate-token.html, admin/tokens.html, miniapp/dashboard.html). They were not touched. Ask Osif if they should be reviewed and pushed, or reverted with `git checkout`. Do NOT auto-stage them.
>
> The new wrapper `ops/slh-push.ps1` is the correct way to deploy any single-page website change going forward — see `ops/PROC_HTML_PAGE_UPDATE.md`. Use `-Files "<page>.html" -Message "<type>(<page>): <description>"`. Always pre-set `$env:SLH_ADMIN_BROADCAST_KEY` per shell.
>
> Theme work elsewhere on the site (per CLAUDE.md "Theme coverage: 42% (18/43 pages)") follows the same 4-edit pattern as in section 2.1 of this handoff. Just adapt to wherever the page already loads scripts.
