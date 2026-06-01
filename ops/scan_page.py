#!/usr/bin/env python3
"""
scan_page.py — verify an SLH website HTML page meets the 5/5 quality bar.

Usage:
    python ops/scan_page.py _active/website/whitepaper.html
    python ops/scan_page.py _active/website/whitepaper.html --json
    python ops/scan_page.py _active/website/*.html  # batch

Exit codes:
    0 — all checks passed (5/5 with no anti-patterns)
    1 — failures present (gaps in features OR anti-patterns detected)
    2 — file not found / unreadable

Output: human-readable checklist by default. Pass --json for machine-readable.

Designed to be runnable by the agent (Cursor/Claude Code) BEFORE commit, OR by
the maintainer AFTER receiving an agent's submission.
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple

# Force UTF-8 stdout on Windows so checkmarks/Hebrew don't crash cp1252
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# ─── Feature signatures (heuristics that match the AGENT_PATTERNS.md spec) ────

CHECKS: Dict[str, Tuple[str, re.Pattern]] = {
    "theme":     ("data-theme attribute set on <html>",
                  re.compile(r'<html\b[^>]*\bdata-theme\s*=', re.IGNORECASE)),
    "i18n_js":   ("/js/translations.js included",
                  re.compile(r'<script[^>]+src\s*=\s*[\'"][^\'"]*\bjs/translations\.js', re.IGNORECASE)),
    "i18n_attr": ("data-i18n attribute used on visible text",
                  re.compile(r'\bdata-i18n(?:-html)?\s*=', re.IGNORECASE)),
    "shared_js": ("/js/shared.js included",
                  re.compile(r'<script[^>]+src\s*=\s*[\'"][^\'"]*\bjs/shared\.js', re.IGNORECASE)),
    "init_call": ("initShared({...}) called",
                  re.compile(r'\binitShared\s*\(', re.IGNORECASE)),
    "topnav":    ("<div id=\"topnav-root\"> mount point present",
                  re.compile(r'\bid\s*=\s*[\'"]topnav-root[\'"]', re.IGNORECASE)),
    "footer":    ("<div id=\"footer-root\"> mount point present",
                  re.compile(r'\bid\s*=\s*[\'"]footer-root[\'"]', re.IGNORECASE)),
    "analytics": ("/js/analytics.js included",
                  re.compile(r'<script[^>]+src\s*=\s*[\'"][^\'"]*\bjs/analytics\.js', re.IGNORECASE)),
    "ai":        ("/js/ai-assistant.js included",
                  re.compile(r'<script[^>]+src\s*=\s*[\'"][^\'"]*\bjs/ai-assistant\.js', re.IGNORECASE)),
}

# ─── Anti-patterns: code that's wrong and WILL break in production ────────────

ANTI_PATTERNS: Dict[str, Tuple[str, re.Pattern]] = {
    "applyTheme":  ("applyTheme(...) — wrong function name; use setTheme()",
                    re.compile(r'\bapplyTheme\s*\(')),
    "TR.init":     ("TR.init() — wrong object; use t(key) and T[lang]",
                    re.compile(r'\bTR\s*\.\s*init\s*\(')),
    "TR_object":   ("TR object reference — should be T (capital, no R)",
                    re.compile(r'(?<![\w.])TR\s*\[')),
    "init_translations": ("initTranslations() — does not exist; initShared() handles i18n",
                          re.compile(r'\binitTranslations\s*\(')),
    "load_navbar": ("loadNavbar() — does not exist; use initShared({activePage})",
                    re.compile(r'\bloadNavbar\s*\(')),
    "web3_wallet": ("/js/web3-wallet.js — file does not exist; use /js/web3.js",
                    re.compile(r'web3-wallet\.js')),
    "old_path":    ("D:/SLH_ECOSYSTEM/website/ — wrong path; use _active/website/",
                    re.compile(r'D:[\\/]SLH_ECOSYSTEM[\\/]website[\\/]', re.IGNORECASE)),
    "hardcoded_pw": ("Hardcoded admin password (slh2026admin or similar) — read from localStorage",
                     re.compile(r'[\'"]slh2026admin[\'"]|[\'"]slh_admin_2026[\'"]')),
    "fake_data_no_demo": ("Mock '99%' or 'אלפי משקיעים' style claim without [DEMO] tag",
                          re.compile(r'(?:אלפי\s+(?:משקיעים|נרשמים)|99%\s+(?:rate|הצלחה))(?![^<]*\[DEMO\])')),
}

# ─── Pages that don't need certain features (whitelist) ───────────────────────

# Some pages legitimately skip features — track them here so scanner doesn't false-alarm.
EXEMPT = {
    "blog-legacy-code.html": {"i18n_attr"},   # long-form Hebrew article, no i18n
    "ops-report-20260411.html": {"i18n_attr"},  # ops report
    "overnight-report.html": {"i18n_attr"},
    "morning-handoff.html": {"i18n_attr"},
    # Add more as needed — never grow this without a real reason
}


def scan_file(path: Path) -> Dict:
    if not path.exists() or not path.is_file():
        return {"file": str(path), "error": "file not found", "pass": False}
    try:
        text = path.read_text(encoding='utf-8', errors='replace')
    except Exception as e:
        return {"file": str(path), "error": str(e), "pass": False}

    name = path.name
    exempt = EXEMPT.get(name, set())

    feature_results = {}
    for key, (label, pattern) in CHECKS.items():
        found = bool(pattern.search(text))
        feature_results[key] = {"label": label, "ok": found, "exempt": key in exempt}

    anti_results = {}
    for key, (label, pattern) in ANTI_PATTERNS.items():
        found = bool(pattern.search(text))
        anti_results[key] = {"label": label, "found": found}

    # Compose 5/5 score: theme, i18n (both checks), nav (topnav OR shared+init), analytics, ai
    score_components = [
        feature_results["theme"]["ok"],
        feature_results["i18n_js"]["ok"] and (feature_results["i18n_attr"]["ok"] or "i18n_attr" in exempt),
        feature_results["topnav"]["ok"] and feature_results["init_call"]["ok"],
        feature_results["analytics"]["ok"],
        feature_results["ai"]["ok"],
    ]
    score = sum(1 for c in score_components if c)

    has_anti = any(r["found"] for r in anti_results.values())
    passed = (score == 5) and not has_anti

    return {
        "file": str(path),
        "name": name,
        "score": score,
        "max_score": 5,
        "pass": passed,
        "features": feature_results,
        "anti_patterns": anti_results,
        "lines": len(text.splitlines()),
    }


def render_human(result: Dict) -> str:
    if result.get("error"):
        return f"❌ {result['file']}: {result['error']}"
    name = result["name"]
    score = result["score"]
    lines = []
    badge = "✅" if result["pass"] else "⚠️" if score >= 3 else "❌"
    lines.append(f"\n{badge} {name} — {score}/5 ({result['lines']} lines)")
    lines.append("─" * 60)

    lines.append("Features:")
    for key, r in result["features"].items():
        if r.get("exempt"):
            mark = "⊘ exempt"
        else:
            mark = "✅" if r["ok"] else "❌"
        lines.append(f"  {mark}  {key:11s} — {r['label']}")

    anti_found = [(k, r) for k, r in result["anti_patterns"].items() if r["found"]]
    if anti_found:
        lines.append("\nAnti-patterns DETECTED (must fix):")
        for k, r in anti_found:
            lines.append(f"  ❌  {k:18s} — {r['label']}")
    else:
        lines.append("\nAnti-patterns: ✅ none")

    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description="Scan SLH website HTML pages for 5/5 quality.")
    ap.add_argument("paths", nargs="+", help="HTML files to scan")
    ap.add_argument("--json", action="store_true", help="JSON output for tooling")
    ap.add_argument("--quiet", action="store_true", help="Only print failures")
    args = ap.parse_args()

    results = []
    for raw in args.paths:
        path = Path(raw)
        if path.is_dir():
            for sub in sorted(path.glob("*.html")):
                results.append(scan_file(sub))
        else:
            results.append(scan_file(path))

    if args.json:
        print(json.dumps(results, indent=2, ensure_ascii=False))
    else:
        any_failed = False
        for r in results:
            if args.quiet and r.get("pass"):
                continue
            print(render_human(r))
            if not r.get("pass"):
                any_failed = True
        # Summary
        total = len(results)
        passed = sum(1 for r in results if r.get("pass"))
        print(f"\n{'=' * 60}\nTOTAL: {passed}/{total} passing 5/5")
        if any_failed:
            print("Run again after fixes. Reference: https://slh-nft.com/AGENT_PATTERNS.md")

    # Exit code: non-zero if any file failed or errored
    bad = sum(1 for r in results if not r.get("pass"))
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
