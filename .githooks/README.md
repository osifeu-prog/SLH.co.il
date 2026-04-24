# .githooks Â· SLH Spark Git Hooks

Hooks that live in this directory apply to this repo when activated via:

```bash
git config core.hooksPath .githooks
```

Then make executable (Git Bash / WSL only; irrelevant on native Windows git):
```bash
chmod +x .githooks/*
```

## Current hooks
| File | Purpose |
|------|---------|
| `pre-commit` | Block oversized diffs + large net-deletions (drift guard) |

## Deactivate (temporarily)
```bash
git config --unset core.hooksPath
```

## Bypass (per-commit)
For a single legitimate large commit without editing hook logic:
```bash
GUARD_CONFIRMED=1 git commit -m "feat(bulk): ..."
```

Never use `--no-verify` â€” that bypasses ALL hooks silently.

## Rationale
See `ops/INCIDENT_20260421_GIT_DRIFT.md` â€” a 2-line fix almost committed a 694-line revert.
See `ops/HOOKS_IMPROVEMENT_PLAN_20260421.md` â€” roadmap for commit-msg, pre-push, post-checkout hooks.
