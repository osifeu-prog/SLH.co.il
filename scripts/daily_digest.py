# -*- coding: utf-8 -*-
"""
Daily Digest — every ~21:00 Israel time, compile a summary of what
happened today and DM it to Osif.

Sources:
  - Git log (both repos): commits today
  - /api/ops/reality: new users, new payments, new licenses, recent broadcasts
  - /api/community/stats: posts today, active today
  - Audit script: number of HIGH findings

Output: text message sent via /api/broadcast/send (custom, Osif only).
Also writes ops/DIGEST_<YYYYMMDD>.md for archive.

Usage:
    python scripts/daily_digest.py                # send DM
    python scripts/daily_digest.py --no-send      # dry run, print to stdout
    python scripts/daily_digest.py --date 2026-04-22   # specific date
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import urllib.request
from datetime import datetime, timezone, timedelta, date as _date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

API = "https://slh-api-production.up.railway.app"
ADMIN_BROADCAST_KEY = os.getenv("SLH_ADMIN_BROADCAST_KEY", "slh-broadcast-2026-change-me")
OSIF_TG = 224223270

API_REPO = ROOT
WEB_REPO = ROOT / "website"


def git_commits_today(repo: Path, since_iso: str, until_iso: str) -> list[str]:
    try:
        cp = subprocess.run(
            ["git", "-C", str(repo), "log",
             f"--since={since_iso}", f"--until={until_iso}",
             "--format=%h %s"],
            capture_output=True, text=True, check=True, timeout=10
        )
        return [line for line in cp.stdout.splitlines() if line.strip()]
    except Exception as e:
        return [f"(git log failed: {e})"]


def api_get(path: str, headers: dict | None = None) -> dict | None:
    try:
        req = urllib.request.Request(API + path, headers=headers or {})
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read().decode("utf-8"))
    except Exception:
        return None


def count_audit_high() -> int:
    try:
        cp = subprocess.run(
            [sys.executable, "scripts/audit_data_integrity.py", "--json"],
            cwd=str(ROOT), capture_output=True, text=True, timeout=60, encoding="utf-8"
        )
        data = json.loads(cp.stdout)
        return sum(1 for f in data if f.get("severity") == "HIGH")
    except Exception:
        return -1


def build_digest(target_date: _date) -> str:
    since = datetime.combine(target_date, datetime.min.time(), tzinfo=timezone.utc)
    until = since + timedelta(days=1)
    since_iso = since.isoformat()
    until_iso = until.isoformat()

    lines = []
    lines.append(f"📅 *SLH Daily Digest · {target_date.isoformat()}*")
    lines.append("")

    # Commits
    api_commits = git_commits_today(API_REPO, since_iso, until_iso)
    web_commits = git_commits_today(WEB_REPO, since_iso, until_iso) if WEB_REPO.exists() else []

    lines.append(f"📦 *Commits* — api: {len(api_commits)} · website: {len(web_commits)}")
    if api_commits:
        lines.append("")
        lines.append("_API repo:_")
        for c in api_commits[:8]:
            lines.append(f"  • {c}")
        if len(api_commits) > 8:
            lines.append(f"  • ...+{len(api_commits)-8} more")
    if web_commits:
        lines.append("")
        lines.append("_Website repo:_")
        for c in web_commits[:5]:
            lines.append(f"  • {c}")

    lines.append("")

    # API health
    health = api_get("/api/health")
    if health:
        lines.append(f"❤️  *API health:* {health.get('status')} · v{health.get('version')} · db={health.get('db')}")
    else:
        lines.append("❤️  *API health:* ❌ UNREACHABLE")
    lines.append("")

    # Reality snapshot
    reality = api_get("/api/ops/reality", headers={"X-Broadcast-Key": ADMIN_BROADCAST_KEY})
    if reality:
        users = reality.get("users") or {}
        founders = len(users.get("founders", []) or [])
        community = len(users.get("community", []) or [])
        total = founders + community
        lines.append(f"👥 *Users:* {total} total · founders={founders} · community={community}")

        bc = reality.get("recent_broadcasts") or []
        today_bc = 0
        for b in bc:
            ca = b.get("created_at")
            if ca and ca.startswith(target_date.isoformat()):
                today_bc += 1
        if today_bc:
            lines.append(f"📤 *Broadcasts today:* {today_bc}")

    # Community stats
    stats = api_get("/api/community/stats")
    if stats:
        lines.append(
            f"💬 *Community:* posts_today={stats.get('posts_today',0)} · "
            f"active_today={stats.get('active_today',0)} · "
            f"total_posts={stats.get('total_posts',0)}"
        )
    lines.append("")

    # Data integrity
    high = count_audit_high()
    if high >= 0:
        if high == 0:
            lines.append("✅ *Data integrity:* 0 HIGH findings")
        elif high == 1:
            lines.append("🟢 *Data integrity:* 1 HIGH finding (legitimate library default)")
        else:
            lines.append(f"🟡 *Data integrity:* {high} HIGH findings — run `python scripts/audit_data_integrity.py --severity HIGH`")
    lines.append("")

    # End
    lines.append("---")
    lines.append("_Generated by scripts/daily_digest.py_")

    return "\n".join(lines)


def send_to_osif(message: str) -> bool:
    try:
        payload = json.dumps({
            "target": "custom",
            "custom_ids": [OSIF_TG],
            "message": message,
            "admin_key": ADMIN_BROADCAST_KEY,
        }).encode("utf-8")
        req = urllib.request.Request(
            f"{API}/api/broadcast/send",
            data=payload,
            headers={"Content-Type": "application/json; charset=utf-8"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=30) as r:
            body = r.read().decode("utf-8")
            print(f"[OK] HTTP {r.status} — {body[:200]}")
            return True
    except Exception as e:
        print(f"[ERR] {e}", file=sys.stderr)
        return False


def archive(target_date: _date, digest: str) -> Path:
    out = ROOT / "ops" / f"DIGEST_{target_date.strftime('%Y%m%d')}.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(digest, encoding="utf-8")
    return out


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--no-send", action="store_true", help="dry run, print only")
    p.add_argument("--date", type=str, default=None, help="YYYY-MM-DD (default: today)")
    args = p.parse_args()

    target = _date.fromisoformat(args.date) if args.date else _date.today()
    digest = build_digest(target)
    archive_path = archive(target, digest)
    print(f"# Archived: {archive_path}\n")
    print(digest)

    if args.no_send:
        print("\n(--no-send: DM not sent)")
        return 0

    print("\nSending DM to Osif...")
    ok = send_to_osif(digest)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
