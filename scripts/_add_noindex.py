# -*- coding: utf-8 -*-
"""Add <meta name="robots" content="noindex,nofollow"> to internal/admin pages.

Skips pages that already have it. Verifies HTML structure isn't broken.
"""
from pathlib import Path
import re

WEB = Path("website")

PAGES = [
    # INTERNAL/DEV (clearly not customer-facing)
    "alpha-progress.html",
    "analytics.html",
    "command-center.html",
    "control-center.html",
    "ops-dashboard.html",
    "overnight-report.html",
    "system-audit.html",
    "test-bots.html",
    "upgrade-tracker.html",
    "ops-report-20260411.html",
    "morning-handoff.html",
    "morning-checklist.html",
    "agent-brief.html",
    "agent-hub.html",
    "agent-tracker.html",
    "chain-status.html",
    "guardian-diag.html",
    # ADMIN ONLY
    "admin.html",
    "admin-bugs.html",
    "admin-experts.html",
    "admin-tokens.html",
    "broadcast-composer.html",
    "leads.html",
    "rotate.html",
    # /admin/* subdirectory
    "admin/control-center.html",
    "admin/mission-control.html",
    "admin/reality.html",
    "admin/tokens.html",
]

NOINDEX_TAG = '<meta name="robots" content="noindex,nofollow">'

results = {"added": [], "already_present": [], "missing": [], "errors": []}

for rel in PAGES:
    p = WEB / rel
    if not p.exists():
        results["missing"].append(rel)
        continue

    try:
        text = p.read_text(encoding="utf-8")
    except Exception as e:
        results["errors"].append(f"{rel}: read err {e}")
        continue

    # Already has noindex? skip
    if re.search(r'<meta\s+name=["\']robots["\']\s+content=["\'][^"\']*noindex', text, re.I):
        results["already_present"].append(rel)
        continue

    # Insert after <head> opening tag (case-insensitive, handles attributes)
    new_text, count = re.subn(
        r'(<head[^>]*>)',
        r'\1\n  ' + NOINDEX_TAG,
        text,
        count=1,
        flags=re.IGNORECASE,
    )

    if count == 0:
        results["errors"].append(f"{rel}: no <head> tag found")
        continue

    # Sanity: head/closing-head should still match
    if not re.search(r'</head>', new_text, re.I):
        results["errors"].append(f"{rel}: missing </head> after edit (aborting)")
        continue

    p.write_text(new_text, encoding="utf-8")
    results["added"].append(rel)


print(f"\n✅ Added noindex to {len(results['added'])} pages:")
for r in results["added"]:
    print(f"  + {r}")

if results["already_present"]:
    print(f"\n⏭ Skipped (already had noindex) — {len(results['already_present'])}:")
    for r in results["already_present"]:
        print(f"  · {r}")

if results["missing"]:
    print(f"\n⚠ Missing files — {len(results['missing'])}:")
    for r in results["missing"]:
        print(f"  ? {r}")

if results["errors"]:
    print(f"\n❌ Errors — {len(results['errors'])}:")
    for r in results["errors"]:
        print(f"  ✗ {r}")
