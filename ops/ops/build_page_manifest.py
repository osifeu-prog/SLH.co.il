#!/usr/bin/env python3
"""
build_page_manifest.py — produce a fresh /data/page-status.json from the live
HTML files in _active/website/.

Output: D:/SLH_ECOSYSTEM/_active/website/data/page-status.json

The JSON is consumed by project-map.html (instead of the hardcoded PAGES array).
This means scores in project-map are always current.

Usage:
    python ops/build_page_manifest.py
    python ops/build_page_manifest.py --dry-run  # preview only

Run after each session OR before each commit, OR on a CI hook.
"""

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

# Reuse the scanner's pattern definitions
sys.path.insert(0, str(Path(__file__).parent))
from scan_page import CHECKS, ANTI_PATTERNS, EXEMPT, scan_file  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent  # D:/SLH_ECOSYSTEM/
WEBSITE = ROOT / "_active" / "website"
OUTPUT = WEBSITE / "data" / "page-status.json"

# ─── Page metadata: role + h1 + title hints (kept tiny on purpose) ────────────
# Most pages have role inferable from path/filename; fallback to 'public'.
ROLE_BY_PREFIX = [
    ("admin/", "admin"),
    ("admin.html", "admin"),
    ("ops-", "ops"),
    ("partner-", "user"),
    ("dashboard", "user"),
    ("wallet", "user"),
    ("trade", "user"),
    ("earn", "user"),
    ("staking", "user"),
    ("invite", "user"),
    ("referral", "user"),
    ("rotate", "user"),
    ("member", "user"),
    ("p2p", "user"),
    ("morning-", "ops"),
    ("overnight", "ops"),
    ("system-health", "ops"),
    ("test-bots", "ops"),
    ("risk-dashboard", "ops"),
    ("control-center", "ops"),
    ("test_", "ops"),
    ("broadcast-", "admin"),
    ("dex-launch", "promo"),
    ("launch-event", "promo"),
    ("partner-launch", "promo"),
    ("promo-", "promo"),
    ("about", "marketing"),
    ("for-therapists", "marketing"),
    ("guides", "marketing"),
    ("getting-started", "user"),
    ("community", "marketing"),
    ("daily-blog", "marketing"),
    ("blog", "marketing"),
    ("healing-vision", "marketing"),
    ("jubilee", "marketing"),
    ("ecosystem-guide", "public"),
    ("blockchain", "public"),
    ("network", "public"),
    ("buy", "public"),
    ("liquidity", "public"),
    ("roadmap", "public"),
    ("voice", "public"),
    ("swarm", "public"),
    ("whitepaper", "public"),
    ("terms", "public"),
    ("privacy", "public"),
    ("index", "public"),
    ("bots", "public"),
    ("onboarding", "user"),
    ("challenge", "user"),
    ("wallet-guide", "user"),
    ("referral-card", "user"),
    ("project-map", "admin"),
    ("my", "admin"),
    ("dashboard-therapist", "user"),
]

TITLE_RE = re.compile(r'<title[^>]*>([^<]+)</title>', re.IGNORECASE)
H1_RE = re.compile(r'<h1[^>]*>(.*?)</h1>', re.IGNORECASE | re.DOTALL)
TAG_RE = re.compile(r'<[^>]+>')


def role_for(rel: str) -> str:
    rel_lower = rel.lower()
    for prefix, role in ROLE_BY_PREFIX:
        if rel_lower.startswith(prefix) or ("/" + prefix in rel_lower):
            return role
    return "public"


def extract_title_h1(text: str):
    title = ''
    h1 = ''
    m_title = TITLE_RE.search(text)
    if m_title:
        title = m_title.group(1).strip()
    m_h1 = H1_RE.search(text)
    if m_h1:
        h1 = TAG_RE.sub('', m_h1.group(1)).strip()
    # Truncate
    return title[:120], h1[:120]


def gap_text(features: dict) -> str:
    missing = []
    if not features["theme"]["ok"]:
        missing.append("theme")
    if not features["i18n_js"]["ok"] or (not features["i18n_attr"]["ok"] and not features["i18n_attr"]["exempt"]):
        missing.append("i18n")
    if not features["analytics"]["ok"]:
        missing.append("analytics")
    if not features["ai"]["ok"]:
        missing.append("ai")
    if not features["topnav"]["ok"] or not features["init_call"]["ok"]:
        missing.append("nav")
    if not missing:
        return "✅ עמוד מלא — תחזוקה שוטפת בלבד"
    return "חסר: " + ", ".join(missing)


def build_entry(html_path: Path) -> dict:
    rel = html_path.relative_to(WEBSITE).as_posix()
    raw = scan_file(html_path)
    text = html_path.read_text(encoding='utf-8', errors='replace')
    title, h1 = extract_title_h1(text)

    feats = raw["features"]
    role = role_for(rel)

    return {
        "f": rel,
        "t": title or rel,
        "h1": h1 or title or "",
        "r": role,
        "theme": feats["theme"]["ok"],
        "i18n": feats["i18n_js"]["ok"] and (feats["i18n_attr"]["ok"] or feats["i18n_attr"]["exempt"]),
        "analytics": feats["analytics"]["ok"],
        "ai": feats["ai"]["ok"],
        "nav": feats["topnav"]["ok"] and feats["init_call"]["ok"],
        "web3": "web3.js" in text and "web3.js?" in text,
        "lines": raw["lines"],
        "gap": gap_text(feats),
        "score": raw["score"],
        "anti_patterns_found": [
            k for k, v in raw["anti_patterns"].items() if v["found"]
        ],
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="Print to stdout, do not write file")
    ap.add_argument("--include-subdirs", action="store_true",
                    help="Also scan admin/, miniapp/, blog/, academy/, prompts/ subdirectories")
    args = ap.parse_args()

    pages = []

    # Root-level HTML files
    for html in sorted(WEBSITE.glob("*.html")):
        if html.name.startswith("_"):  # skip _underscore files
            continue
        pages.append(build_entry(html))

    # Optional subdirectories
    if args.include_subdirs:
        for subdir in ("admin", "miniapp", "blog", "academy", "prompts"):
            d = WEBSITE / subdir
            if d.exists():
                for html in sorted(d.glob("*.html")):
                    pages.append(build_entry(html))

    # Manifest
    manifest = {
        "_meta": {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "generator": "ops/build_page_manifest.py",
            "website_root": str(WEBSITE),
            "total_pages": len(pages),
            "complete_5_5": sum(1 for p in pages if p["score"] == 5),
            "with_anti_patterns": sum(1 for p in pages if p["anti_patterns_found"]),
            "consumed_by": "https://slh-nft.com/project-map.html",
        },
        "pages": pages,
    }

    payload = json.dumps(manifest, indent=2, ensure_ascii=False)

    if args.dry_run:
        print(payload)
        return

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(payload, encoding='utf-8')
    print(f"✅ Wrote {OUTPUT} — {len(pages)} pages, {manifest['_meta']['complete_5_5']} are 5/5, "
          f"{manifest['_meta']['with_anti_patterns']} have anti-patterns")


if __name__ == "__main__":
    main()
