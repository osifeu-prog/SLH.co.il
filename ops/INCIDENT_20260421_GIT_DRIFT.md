# INCIDENT REPORT · Git Drift Near-Miss · 2026-04-21
**Severity:** HIGH (would have reverted 348 lines of live production code).
**Outcome:** NO production impact. Caught before commit.

---

## Summary
While fixing a 2-line bug in `api/main.py` + `main.py` (`_require_admin` tuple-unpacking), the working tree had drifted 694 lines from `origin/master`. A naive `git commit -am` would have committed the drift alongside the fix, silently reverting the entire `/api/events/public` endpoint family (commit `98cb7e4`) — 5 public API endpoints would have disappeared from production.

## Timeline
| Time | Event |
|------|-------|
| T+0 | Identified bug: line 10770 `admin_id, _role = _require_admin(...)` but fn returns `int` |
| T+2m | `Edit` tool applied fix to api/main.py + main.py |
| T+3m | `git diff --stat` reported `694 insertions, 694 deletions` for a 2-line fix — HALT |
| T+4m | Diagnosed: `git diff api/main.py` showed 348-line block deletion of `/api/events/public` + `PUBLIC_EVENT_TYPES` |
| T+6m | `git stash push`, `git fetch origin`, `git log HEAD..origin/master` — but HEAD == origin/master (0/0) |
| T+8m | Realized: working tree was stale relative to HEAD — Edit tool had written back pre-`98cb7e4` content |
| T+10m | `git checkout origin/master -- api/main.py main.py` — restored |
| T+11m | `Edit` tool retried → SAME 694-line drift reappeared (Edit cache still held stale snapshot) |
| T+13m | Switched to Python `open(..., 'rb') → replace → write(..., 'wb')` — binary-exact |
| T+14m | `git diff --stat` = 4 lines. Verified. Committed as `e0f8973`. Pushed. |

## Root cause
`Edit` tool (Claude Code) reads file content into an in-session cache on first access. When the working tree is modified externally (e.g., `git checkout origin/master -- <file>`) but the tool still holds the pre-checkout snapshot, a subsequent `Edit` call writes back the cached (old) content — plus the requested string replacement — silently reverting the external change.

This is NOT a bug in Edit per se; it's an expected cache-consistency behavior. But it interacts dangerously with git operations that mutate tracked files between Reads and Edits.

## Why diff --stat flagged it
The single-blob hash `f416bfb4..5dbece3` showed the file was entirely different — not just 2 lines. `--stat` compared working tree to index: 694 lines changed because the working tree had reverted to a pre-`98cb7e4` version while the index still held `98cb7e4` content.

## What would have broken in production
Endpoints that would have been silently removed:
- `GET /api/events/public` (homepage live-activity feed)
- `POST /api/ops/credit` (manual credit)
- `POST /api/ops/approve-payment` (payment approval)
- `POST /api/ops/ban` (user ban)
- `GET /api/performance` (research dashboard data)

Plus helper constants: `PUBLIC_EVENT_TYPES`, `PUBLIC_STRIP_META_KEYS`.

Visible to users: `chain-status.html`, `performance.html`, `admin/reality.html`, homepage activity ticker — all broken silently (200s turning into empty payloads or 404s).

## Prevention (shipped in same session)
1. **Pre-commit guard script** — aborts commits where diff size is disproportionate to commit message scope. → `.githooks/pre-commit` + `ops/HOOKS_IMPROVEMENT_PLAN_20260421.md`
2. **Discipline:** for any edit on a file that may have drifted: `git fetch && git checkout origin/master -- <file>` BEFORE editing, verify hash matches HEAD, then apply patch via `python -c "open().replace()"` (not via Edit tool with prior Read).
3. **Verification:** `git diff --stat` is mandatory before `git add`. Threshold rule: if stat shows more lines than the edit intended, STOP and diagnose — never commit through uncertainty.

## Lessons
- `Edit` cache is session-scoped; external tool mutations (git checkout, external editor, linter) invalidate it but the tool doesn't always detect that.
- `git diff --stat` is the single most important pre-commit check.
- `git hash-object <file>` vs `git ls-tree HEAD -- <file>` is the ground-truth drift detector.
- Python binary replace (`open('rb') / replace / write('wb')`) is safer than Edit for post-checkout patching because it reads the current disk content, not a cached snapshot.
