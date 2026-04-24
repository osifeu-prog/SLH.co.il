# -*- coding: utf-8 -*-
"""
Railway Deploy Watchdog — runs a tight health check and alerts if the Railway
API version is stuck (i.e. commits accumulate on master but the live API
doesn't update for N minutes).

Designed for: Windows Task Scheduler every 5 minutes, OR manual one-shot run.

Alert channel: sends a Telegram DM to Osif via /api/broadcast/send
  (target=custom, custom_ids=[224223270]).

Exit codes:
  0 — healthy (version updated recently or within grace period)
  1 — stuck (new commits on master but API version unchanged for > threshold)
  2 — unreachable (health endpoint down)

Usage:
    python scripts/railway_watchdog.py               # one-shot check
    python scripts/railway_watchdog.py --verbose
    python scripts/railway_watchdog.py --no-alert    # check only, don't DM
    python scripts/railway_watchdog.py --state /path/to/state.json
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_STATE = ROOT / "ops" / ".railway_watchdog_state.json"

API = "https://slh-api-production.up.railway.app"
HEALTH_URL = f"{API}/api/health"
BROADCAST_URL = f"{API}/api/broadcast/send"
ADMIN_BROADCAST_KEY = os.getenv("SLH_ADMIN_BROADCAST_KEY", "slh-broadcast-2026-change-me")
OSIF_TG = 224223270

STUCK_THRESHOLD_MINUTES = 15  # alert if new commits on master for more than this without version change
GRACE_PERIOD_MINUTES = 5      # after detecting stuck state, wait this long before second alert


def log(msg: str, verbose: bool) -> None:
    if verbose:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")


def fetch_health(verbose: bool) -> dict | None:
    try:
        req = urllib.request.Request(HEALTH_URL, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=10) as r:
            return json.loads(r.read().decode("utf-8"))
    except Exception as e:
        log(f"health fetch failed: {e}", verbose)
        return None


def git_latest_commit(verbose: bool) -> tuple[str, datetime] | None:
    try:
        cp = subprocess.run(
            ["git", "-C", str(ROOT), "log", "origin/master", "-1", "--format=%H|%cI"],
            capture_output=True, text=True, check=True, timeout=10
        )
        line = cp.stdout.strip()
        if "|" not in line:
            return None
        sha, iso = line.split("|", 1)
        return sha[:7], datetime.fromisoformat(iso)
    except Exception as e:
        log(f"git log failed: {e}", verbose)
        return None


def send_alert(message: str, verbose: bool) -> None:
    try:
        payload = json.dumps({
            "target": "custom",
            "custom_ids": [OSIF_TG],
            "message": message,
            "admin_key": ADMIN_BROADCAST_KEY,
        }).encode("utf-8")
        req = urllib.request.Request(
            BROADCAST_URL,
            data=payload,
            headers={"Content-Type": "application/json; charset=utf-8"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=30) as r:
            log(f"alert DM queued: HTTP {r.status}", verbose)
    except Exception as e:
        log(f"alert send failed (API may be the thing that's down): {e}", verbose)


def load_state(path: Path) -> dict:
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


def save_state(path: Path, state: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--verbose", "-v", action="store_true")
    p.add_argument("--no-alert", action="store_true", help="run checks but don't send DM")
    p.add_argument("--state", type=Path, default=DEFAULT_STATE)
    args = p.parse_args()

    now = datetime.now(timezone.utc)
    state = load_state(args.state)

    health = fetch_health(args.verbose)
    if health is None:
        msg = f"🚨 SLH Railway Watchdog\n\nAPI /api/health unreachable at {now.isoformat()[:19]}Z"
        log(msg, args.verbose)
        if not args.no_alert:
            # Don't try to alert via the same API that's down — log and exit
            print(msg, file=sys.stderr)
        return 2

    version = str(health.get("version", "unknown"))
    log(f"health OK, version={version}", args.verbose)

    latest_commit = git_latest_commit(args.verbose)
    if latest_commit:
        sha, commit_dt = latest_commit
        age_min = (now - commit_dt).total_seconds() / 60
        log(f"origin/master head: {sha} ({age_min:.1f} min ago)", args.verbose)
    else:
        sha, age_min = "unknown", 0

    prev_version = state.get("last_version")
    first_stuck_seen = state.get("first_stuck_seen")
    last_alert_at = state.get("last_alert_at")

    # If version changed → healthy, clear state
    if prev_version != version:
        log(f"version changed: {prev_version} -> {version}", args.verbose)
        state = {
            "last_version": version,
            "last_check": now.isoformat(),
            "last_commit_sha": sha,
            "first_stuck_seen": None,
            "last_alert_at": None,
        }
        save_state(args.state, state)
        return 0

    # Version unchanged. Is there a new commit that hasn't deployed?
    if latest_commit is None:
        state.update({"last_check": now.isoformat()})
        save_state(args.state, state)
        return 0

    # Same version as before. If commit is RECENT (< threshold), still in grace period.
    if age_min < STUCK_THRESHOLD_MINUTES:
        log(f"latest commit still within grace ({age_min:.1f} < {STUCK_THRESHOLD_MINUTES} min)", args.verbose)
        state.update({"last_check": now.isoformat(), "last_commit_sha": sha})
        save_state(args.state, state)
        return 0

    # Commit older than threshold with no version change → STUCK.
    if first_stuck_seen is None:
        state["first_stuck_seen"] = now.isoformat()

    # Don't spam alerts — only every GRACE_PERIOD_MINUTES
    if last_alert_at:
        last_alert_dt = datetime.fromisoformat(last_alert_at.replace("Z", "+00:00") if "Z" in last_alert_at else last_alert_at)
        mins_since_alert = (now - last_alert_dt).total_seconds() / 60
        if mins_since_alert < GRACE_PERIOD_MINUTES:
            log(f"already alerted {mins_since_alert:.1f} min ago, skipping", args.verbose)
            save_state(args.state, state)
            return 1

    msg = (
        f"🚨 SLH Railway Watchdog\n"
        f"\n"
        f"Deploy stuck for {age_min:.0f} minutes.\n"
        f"\n"
        f"API version: {version}\n"
        f"Latest commit: {sha}\n"
        f"Commit age: {age_min:.0f} min\n"
        f"\n"
        f"Open https://railway.app/project/slh-api → Deployments"
    )
    print(msg)

    if not args.no_alert:
        send_alert(msg, args.verbose)
        state["last_alert_at"] = now.isoformat()

    state.update({"last_check": now.isoformat(), "last_commit_sha": sha})
    save_state(args.state, state)
    return 1


if __name__ == "__main__":
    sys.exit(main())
