# SLH Spark · Incidents Index
**Purpose:** Chronological log of production incidents + postmortems. Each entry links to a detailed incident doc. This file is the INDEX — the timeline.

---

## Log

| Date | Severity | Title | Status | Doc |
|------|----------|-------|--------|-----|
| 2026-04-21 | HIGH | 694-line near-miss git drift | Resolved | [INCIDENT_20260421_GIT_DRIFT.md](INCIDENT_20260421_GIT_DRIFT.md) |
| 2026-04-21 | HIGH | Railway pipeline stuck (curly-quote corruption) | Mitigated | See §1 below |
| 2026-04-21 | HIGH | `_require_admin` tuple-unpacking bug (500s) | Resolved | Commit `e0f8973` |
| 2026-04-21 | MED  | `slh-ledger` crash loop (stale image) | Resolved | Commit n/a — rebuild only |
| 2026-04-21 | MED  | Phantom "47 online" in community.html | Resolved | Commit `d6cc080` |
| 2026-04-21 | LOW  | Yahav DM bounce (bot DM to un-started user) | User-action | OPS_RUNBOOK §4 |

---

## §1 · 2026-04-21 · Curly-quote corruption broke Railway

**What:** Commit `097eafe` (from parallel session) pasted Python code with U+201C/U+201D curly quotes as string delimiters instead of ASCII `"`. This is a SyntaxError. Every Railway build from `097eafe` onward failed. API stayed on the pre-`097eafe` version while master kept accumulating commits.

**Impact:** 5+ commits (`b48a1b1`, `7c06bbc`, `b60cec2`, `8e18c15`) queued, unable to deploy. Features like CRM Phase 0 and Tzvika promotion were invisible to production.

**Detection:** Manual `python -m py_compile api/main.py` while diagnosing why new endpoints returned 404 after push.

**Resolution:**
1. `git checkout e0f8973 -- api/main.py main.py` (last clean commit)
2. Re-applied needed changes (founder_ids + CRM wiring) via Python binary replace
3. Committed as `b60cec2` (`fix(syntax):`)
4. Lost: p2p escrow code from `097eafe` (was non-functional anyway — will be re-added cleanly)

**Prevention (shipped):**
- `.githooks/pre-commit` already enforces diff-size + large-deletion guards (from 694-line drift)
- Added: `python -m py_compile api/main.py main.py` should be in pre-push hook (not yet; on roadmap in `ops/HOOKS_IMPROVEMENT_PLAN_20260421.md`)

**Open questions:**
- Railway auto-deploy may have been disabled after repeated failures; needs Osif to check dashboard.
- Why did the parallel session produce curly quotes? Rich-text copy-paste from another LLM's UI. Should add CI check on GitHub push.

---

## Template for new entries

Create a new file `ops/INCIDENT_<YYYYMMDD>_<slug>.md` with this structure:

```markdown
# INCIDENT REPORT · <Title> · <YYYY-MM-DD>
**Severity:** <LOW | MED | HIGH | CRITICAL>
**Outcome:** <prod-impact? data-loss? etc.>

## Summary
1-2 sentences. What happened, what broke, was there user impact.

## Timeline
| Time | Event |
...

## Root cause
Why.

## Resolution
What was done.

## Prevention
What's been added (hook, doc, process) so this can't recur — or a clear flag if nothing can prevent it.

## Lessons
Bullet list. Keep short. These are what someone reading this in 6 months needs to know.
```

Then add a line to the log table above.

---

## When NOT to create an incident doc
- Reversible mistake caught in under 5 minutes
- Single-line typos with no user-visible effect
- Normal deploy rollbacks for known-good reasons

Do create one when:
- Real-user impact (even brief)
- > 15 min to diagnose
- Novel failure mode
- Would re-bite someone who didn't see it
