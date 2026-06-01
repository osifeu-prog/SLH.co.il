# Git Hooks Improvement Plan · 2026-04-21
**Goal:** turn the near-miss from `INCIDENT_20260421_GIT_DRIFT.md` into an automated check.

---

## Priority order
| # | Hook | Purpose | Status |
|---|------|---------|--------|
| 1 | `pre-commit` | Block over-sized diffs, large net-deletions, drift | **Ready** — `.githooks/pre-commit` |
| 2 | `commit-msg` | Enforce `<type>(<scope>): <subject>` (feat/fix/docs/refactor/chore) | Planned |
| 3 | `pre-push` | Run `python -m py_compile` on `api/main.py`, `main.py` | Planned |
| 4 | `post-checkout` | Re-sync `main.py` ↔ `api/main.py` if diverged | Planned |

## Activation (one-time)
```bash
cd /d/SLH_ECOSYSTEM
git config core.hooksPath .githooks
chmod +x .githooks/pre-commit  # Git Bash / WSL; irrelevant on native Windows
```
After this, every `git commit` routes through `.githooks/pre-commit`.

## Hook #1 · pre-commit rules
Location: `.githooks/pre-commit`.

Blocks commit if ANY of:
1. **Total staged diff > 300 lines** AND commit message does NOT start with `feat(`, `refactor(`, or `docs(` → likely unintended scope creep.
2. **Any single file shows > 100 net deletions** (removed > added by 100+) → likely drift revert.
3. **Staged file's HEAD blob hash disagrees with `origin/master` blob hash** → possible out-of-date working tree.

Bypass for legitimate large commits:
```bash
GUARD_CONFIRMED=1 git commit -m "feat(massive): refactor X"
```

Never bypass without reading the diff.

## Hook #2 · commit-msg (planned)
Regex: `^(feat|fix|docs|refactor|chore|test|ops)(\([a-z0-9-]+\))?!?: .{8,}$`

Rationale: enables automatic changelog generation + scope-aware routing in `pre-commit`.

## Hook #3 · pre-push (planned)
```bash
python -m py_compile api/main.py main.py || exit 1
```
Catches syntax errors before they reach Railway.

## Hook #4 · post-checkout (planned)
After checkout, if `main.py` and `api/main.py` have different content, warn (don't auto-fix — surfacing drift is the whole point).

## Bypassing the guard
`--no-verify` bypasses ALL hooks. **Never use it.** If a hook fails, read its output and fix the underlying issue. Adding new legitimate-but-large commit types → update the hook's allow-list, don't bypass.

## Future: repo-side enforcement
Local hooks can be bypassed per-developer. For enforced checks, add:
- GitHub Actions workflow that reruns the same checks on `pull_request`
- Branch protection rule on `master` requiring the workflow to pass

Not needed for solo-dev SLH repo yet, but documented for when team grows.

## Success metric
Zero commits with stat `>300 insertions, >300 deletions` that don't have `feat(*)` in the message. Measured monthly via:
```bash
git log --shortstat --since="1 month ago" --format="%H %s" | \
  awk '/^[a-f0-9]+ [^f]/ {msg=$0} /insertions/ {print msg, $0}'
```
