# -*- coding: utf-8 -*-
"""Build ops/PAGE_INVENTORY_20260425.md — categorize all HTML pages.

Output: a markdown file with every page classified into a bucket.
Osif marks his decisions inline; agent runs cleanup based on annotated file.
"""
from pathlib import Path
import re

WEB = Path("website")
OUT = Path("ops/PAGE_INVENTORY_20260425.md")

NAV_FILE = WEB / "js" / "shared.js"

# ── Read nav targets ────────────────────────────────────────────────
nav = set()
if NAV_FILE.exists():
    text = NAV_FILE.read_text(encoding="utf-8", errors="ignore")
    for m in re.finditer(r'href="/([a-zA-Z0-9_-]+\.html)"', text):
        nav.add(m.group(1))


# ── Bucket rules (keyword/regex based) ──────────────────────────────
def classify(name: str) -> str:
    n = name.lower()
    if name == "index.html":
        return "🌐 HOMEPAGE"
    if name in {"about.html", "getting-started.html", "how-it-works.html",
                "ecosystem-guide.html", "join-guide.html", "join.html",
                "guides.html", "wallet-guide.html"}:
        return "🎯 PUBLIC FUNNEL"
    if name in {"buy.html", "pay.html", "pay-test.html", "pay-creator-package.html",
                "creator-intake.html", "card-payment.html"}:
        return "💳 PUBLIC FUNNEL · PAYMENT"
    if name in {"academia.html", "academia-courses.html"}:
        return "🎓 PUBLIC · ACADEMIA"
    if name in {"trade.html", "earn.html", "staking.html", "p2p.html"}:
        return "💰 PUBLIC · ECONOMICS"
    if name in {"bots.html"}:
        return "🤖 PUBLIC · BOTS LIST"
    if name in {"community.html", "blog.html", "daily-blog.html", "blog-legacy-code.html"}:
        return "📰 PUBLIC · COMMUNITY/BLOG"
    if name in {"dashboard.html", "wallet.html", "referral.html", "invite.html",
                "challenge.html", "leaderboard.html", "member.html",
                "investment-tracker.html", "expenses.html"}:
        return "👤 USER ZONE (logged in)"
    if name in {"voice.html", "swarm.html", "kosher-wallet.html", "encryption.html",
                "healing-vision.html", "jubilee.html"}:
        return "🌅 PUBLIC · VISION/MARKETING"
    if name in {"launch-event.html", "dex-launch.html", "for-therapists.html",
                "ambassador.html", "experts.html", "broker-dashboard.html"}:
        return "📢 PUBLIC · MARKETING/CAMPAIGN"
    if name in {"whitepaper.html", "blockchain.html", "roadmap.html",
                "privacy.html", "terms.html", "risk.html", "gallery.html"}:
        return "📜 PUBLIC · LEGAL/REFERENCE"
    if name in {"network.html", "project-map.html", "project-map-advanced.html",
                "status.html", "performance.html", "system-audit.html",
                "alpha-progress.html", "analytics.html", "ops-dashboard.html",
                "overnight-report.html", "test-bots.html",
                "agent-brief.html", "agent-hub.html", "agent-tracker.html",
                "command-center.html", "control-center.html", "morning-handoff.html",
                "morning-checklist.html", "ops-report-20260411.html",
                "upgrade-tracker.html", "bot-registry.html", "guardian-diag.html",
                "chain-status.html", "ops-viewer.html"}:
        return "🛠 INTERNAL/DEV (hide from customers)"
    if name in {"admin.html", "admin-bugs.html", "admin-experts.html",
                "admin-tokens.html", "broadcast-composer.html", "rotate.html",
                "leads.html", "device-pair.html", "live.html"}:
        return "🔒 ADMIN ONLY (hide from customers)"
    if name in {"bug-report.html"}:
        return "🐛 PUBLIC · UTILITY (bug report)"
    if name in {"member.html", "partner-dashboard.html", "partner-launch-invite.html",
                "referral-card.html", "onboarding.html"}:
        return "👤 PARTNER/MEMBER ZONE"
    if "test" in n or "demo" in n or "old" in n or "legacy" in n:
        return "🗑 CANDIDATE FOR DELETION (test/demo/legacy)"
    if "promo" in n or "campaign" in n or "shekel" in n:
        return "📢 PUBLIC · MARKETING/CAMPAIGN"
    return "❓ UNCLASSIFIED — review needed"


# ── Collect all HTML files ──────────────────────────────────────────
def collect(dir_: Path, prefix: str = ""):
    out = []
    if not dir_.exists():
        return out
    for f in sorted(dir_.glob("*.html")):
        out.append((prefix + f.name, f.stat().st_size))
    return out


root_pages = collect(WEB)
admin_pages = collect(WEB / "admin", prefix="admin/")
miniapp_pages = collect(WEB / "miniapp", prefix="miniapp/")

# Group by bucket
buckets: dict[str, list[tuple[str, int, bool]]] = {}
for name, size in root_pages:
    bucket = classify(name)
    in_nav = name in nav
    buckets.setdefault(bucket, []).append((name, size, in_nav))


# ── Write inventory ─────────────────────────────────────────────────
lines: list[str] = []
lines.append("# SLH Spark · Page Inventory · 2026-04-25\n")
lines.append("**Purpose:** classify every HTML page into a bucket. Operator marks decisions inline. Agent runs cleanup based on annotations.\n")
lines.append(f"**Total:** {len(root_pages)} pages in /root + {len(admin_pages)} in /admin + {len(miniapp_pages)} in /miniapp = **{len(root_pages)+len(admin_pages)+len(miniapp_pages)}**\n")
lines.append(f"**In main nav (shared.js):** {len(nav)} pages\n")
lines.append("\n---\n")

lines.append("## How to mark decisions\n")
lines.append("Add one of these tags AFTER the page name on the line you want to act on:\n")
lines.append("- `[KEEP]` — leave as is\n")
lines.append("- `[HIDE]` — add `<meta name=\"robots\" content=\"noindex,nofollow\">` + remove from nav\n")
lines.append("- `[DELETE]` — `git rm` the file (irreversible — must be on a branch)\n")
lines.append("- `[MERGE→<target>.html]` — content moves into target, file deleted\n")
lines.append("- `[RENAME→<new>.html]` — file renamed, redirects added\n")
lines.append("\nDefault if unmarked: keep current state.\n")
lines.append("\n---\n")

# Sort buckets by an explicit priority
order = [
    "🌐 HOMEPAGE",
    "🎯 PUBLIC FUNNEL",
    "💳 PUBLIC FUNNEL · PAYMENT",
    "🎓 PUBLIC · ACADEMIA",
    "💰 PUBLIC · ECONOMICS",
    "🤖 PUBLIC · BOTS LIST",
    "📰 PUBLIC · COMMUNITY/BLOG",
    "👤 USER ZONE (logged in)",
    "👤 PARTNER/MEMBER ZONE",
    "🌅 PUBLIC · VISION/MARKETING",
    "📢 PUBLIC · MARKETING/CAMPAIGN",
    "📜 PUBLIC · LEGAL/REFERENCE",
    "🐛 PUBLIC · UTILITY (bug report)",
    "🛠 INTERNAL/DEV (hide from customers)",
    "🔒 ADMIN ONLY (hide from customers)",
    "🗑 CANDIDATE FOR DELETION (test/demo/legacy)",
    "❓ UNCLASSIFIED — review needed",
]

for bucket in order:
    items = buckets.get(bucket, [])
    if not items:
        continue
    lines.append(f"## {bucket}  ({len(items)})\n")
    for name, size, in_nav in items:
        nav_marker = " · 🧭 in-nav" if in_nav else ""
        lines.append(f"- `/{name}` ({size:,} B){nav_marker} — _________________")
    lines.append("")

# Admin + miniapp separately
lines.append("## 🔒 /admin/ (4 — admin-only by URL convention)\n")
for name, size in admin_pages:
    lines.append(f"- `/{name}` ({size:,} B) — _________________")
lines.append("")

lines.append("## 📱 /miniapp/ (4 — Telegram Mini App, only via Telegram client)\n")
for name, size in miniapp_pages:
    lines.append(f"- `/{name}` ({size:,} B) — _________________")
lines.append("")

# Summary action
lines.append("---\n")
lines.append("## Quick filters (for review session with operator)\n")
lines.append("\n### What customers see in public nav (29 — too many)\n")
for n in sorted(nav):
    lines.append(f"- `/{n}`")
lines.append("\n### Recommended public nav after cleanup (7-9 items)\n")
lines.append("- `/` (home)\n- `/about.html`\n- `/getting-started.html`\n- `/bots.html`\n- `/earn.html`\n- `/buy.html`\n- `/dashboard.html` (logged-in)\n- `/whitepaper.html`\n- `/community.html`\n")
lines.append("")

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text("\n".join(lines), encoding="utf-8")
print(f"Wrote: {OUT}  ({len(lines)} lines, {sum(len(v) for v in buckets.values())} root pages classified)")
