# Procedure — HTML Page Update + Deploy

| Field | Value |
|-------|-------|
| Status | Active |
| Owner | Osif Ungar (@osifeu_prog) |
| Effective | 2026-04-25 |
| Scope | Single-page edits under `D:\SLH_ECOSYSTEM\website\*.html` deployed to GitHub Pages (slh-nft.com), with auto-notification to @SLH_Claude_bot |

## Pre-conditions

1. Repo working tree on `main`, clean except for the target file(s).
2. `$env:SLH_ADMIN_BROADCAST_KEY` set in the current PowerShell session.
   Set per-session: `$env:SLH_ADMIN_BROADCAST_KEY = "<value>"` (never paste the value into chat or commit it).
3. Local browser opens the page without console errors.

## Steps

### 1. Edit
Make the page change in `D:\SLH_ECOSYSTEM\website\<page>.html`.

### 2. Verify locally
```powershell
cd D:\SLH_ECOSYSTEM\website
start <page>.html
```
DevTools checks:
- Console: zero errors.
- Elements: `<html data-theme="dark">` (or whichever theme was last used) on initial paint — proves no FOUC.
- Theme picker (top-nav) cycles through dark/terminal/crypto/cyberpunk/ocean/sunset/light.
- After theme change + reload: choice persists (`localStorage.slh_theme`).
- If `data-i18n` keys were added: language toggle in top-nav translates them.

### 3. Diff review
```powershell
cd D:\SLH_ECOSYSTEM\website
git status
git diff <page>.html
```

### 4. Push via wrapper
```powershell
D:\SLH_ECOSYSTEM\ops\slh-push.ps1 `
    -Files "<page>.html" `
    -Message "<type>(<page>): <short description>"
```
Multiple files:
```powershell
D:\SLH_ECOSYSTEM\ops\slh-push.ps1 `
    -Files "<page>.html","js/translations.js" `
    -Message "fix(<page>): <description>"
```

The wrapper does, in order:
1. `git add -- <each file>` (never `-A` or `.`)
2. `git commit -m <message>` (pre-commit hooks run normally; no `--no-verify`)
3. `git push origin main`
4. POST to `/api/broadcast/send` with `X-Admin-Key` header (env var)

### 5. Confirm live
Wait ~90 seconds for GitHub Pages CDN propagation, then:
```powershell
curl.exe -s https://slh-nft.com/<page>.html | Select-String "data-theme"
# expect: <html lang="he" dir="rtl" data-theme="dark">
```
Open the live URL in a browser; verify the change is visible.

### 6. Telegram check
Confirm @SLH_Claude_bot received the deploy message in the admins channel.
If notification was warned-skipped (env var unset) — set it for next time and continue.

## Commit message format

`<type>(<page>): <description>`

Types: `feat` (new feature), `fix` (bug fix), `style` (CSS/visual only), `refactor` (no behavior change), `docs`, `chore`.

Examples:
- `fix(daily-blog): data-theme bootstrap, web3-wallet.js, dedup footer-root`
- `feat(experts): add filter-by-domain UI`
- `style(dashboard): tighten mobile breakpoint`
- `chore(footer): bump shared.js cache-bust`

## Rollback

```powershell
cd D:\SLH_ECOSYSTEM\website
git revert HEAD --no-edit
git push origin main
```
GitHub Pages re-deploys the previous version within ~90s. Notify the channel manually since `git revert` does not invoke `slh-push.ps1`.

## When NOT to use this procedure

- Multi-file refactor spanning >2 pages → use a feature branch + PR review.
- Schema or API changes → use the slh-api repo procedure (root, master branch, Railway auto-deploy).
- Anything that touches production env vars → manual via Railway dashboard, not via git.
- Edits to `.env`, secrets, or anything that the repo's `.gitignore` excludes.

## Failure modes + responses

| Failure | Response |
|---------|----------|
| `File not found` | `cd` into the correct repo (`D:\SLH_ECOSYSTEM\website` for website files). |
| `Commit failed` | Pre-commit hook flagged something. Read the hook output, fix the underlying issue, rerun. Do NOT use `--no-verify`. |
| `Push failed` | Pull first (`git pull --rebase origin main`), resolve conflicts, rerun. |
| `Notification failed` warning | Push succeeded. Verify env var is set; check `/api/health`; rerun the curl manually if needed. |
| GitHub Pages still showing old version after 5min | Hard-refresh (Ctrl+Shift+R); check Cloudflare cache; in last resort, push a no-op commit to re-trigger the build. |

## References

- Wrapper script: [D:/SLH_ECOSYSTEM/ops/slh-push.ps1](slh-push.ps1)
- Endpoint: `POST /api/broadcast/send` (auth: `X-Admin-Key`)
- Bot: @SLH_Claude_bot (Telegram)
- Memory rule: "Never Paste Secrets" — keys live in env vars only.
- Memory rule: "PowerShell vs Browser Console" — this procedure is shell-only.
