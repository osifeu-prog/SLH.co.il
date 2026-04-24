# -*- coding: utf-8 -*-
"""
Yom Ha'atzmaut 78 broadcast — ready for 2026-04-22 evening (after Yom Hazikaron ends).

Target: all registered users (target=registered).
Respects the Yom Hazikaron boundary: DO NOT run before 20:00 on 2026-04-22.

Usage (when you're ready):
    python scripts/send_indep_day_20260422.py            # real send
    python scripts/send_indep_day_20260422.py --dry-run  # preview only

Abort with Ctrl-C during the 5s confirmation window.
"""
import argparse
import json
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime

API = "https://slh-api-production.up.railway.app/api/broadcast/send"
KEY = "slh-broadcast-2026-change-me"

MESSAGE = (
    "🇮🇱🤍💙 יום עצמאות שמח! 🤍💙\n"
    "\n"
    "\"שנה הבאה בירושלים הבנויה —\n"
    " שניהיה באמת בני חורין,\n"
    " ממלחמות, מצער, מכאב.\n"
    " שנדע רק אושר ושמחה\n"
    " כמו שנרגיש היום.\"\n"
    "\n"
    "78 שנה למדינת ישראל 🌟\n"
    "\n"
    "מ-SLH Spark —\n"
    "חג עצמאות שמח, משפחה! 🎆🎇\n"
    "נמשיך לבנות יחד את הקהילה שלנו,\n"
    "את הכלכלה שלנו, את העתיד שלנו.\n"
    "\n"
    "עם ישראל חי ✡️💪\n"
    "\n"
    "— Osif + הצוות של SLH Spark"
)


def guard_timing() -> None:
    """Refuse to send before 2026-04-22 20:00 (Yom Hazikaron ends)."""
    now = datetime.now()
    cutoff = datetime(2026, 4, 22, 20, 0)
    if now < cutoff:
        delta = cutoff - now
        hrs = int(delta.total_seconds() / 3600)
        mins = int((delta.total_seconds() % 3600) / 60)
        print(f"⛔ Too early. Yom Hazikaron ends at 20:00 on 2026-04-22.")
        print(f"   Time remaining: {hrs}h {mins}m. Exiting.")
        print(f"   (Override: comment out guard_timing() in this script if you know what you're doing.)")
        sys.exit(2)


def send(dry_run: bool) -> int:
    payload = json.dumps({
        "target": "registered",
        "message": MESSAGE,
        "admin_key": KEY,
        "dry_run": dry_run,
    }, ensure_ascii=False).encode("utf-8")

    req = urllib.request.Request(
        API,
        data=payload,
        headers={
            "Content-Type": "application/json; charset=utf-8",
            "Accept": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            body = resp.read().decode("utf-8")
            print(f"HTTP {resp.status}")
            print(body)
            return 0
    except urllib.error.HTTPError as e:
        print(f"HTTP {e.code}")
        print(e.read().decode("utf-8", errors="replace"))
        return 1


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--dry-run", action="store_true", help="preview recipients only, do not send")
    p.add_argument("--skip-timing-guard", action="store_true", help="(dangerous) send even before Yom Hazikaron ends")
    args = p.parse_args()

    if not args.skip_timing_guard and not args.dry_run:
        guard_timing()

    print("=== Yom Ha'atzmaut 78 broadcast ===")
    print(f"Target:   registered users (all reg=True in web_users)")
    print(f"Mode:     {'DRY-RUN' if args.dry_run else 'REAL SEND'}")
    print(f"Message preview ({len(MESSAGE)} chars):")
    print("---")
    print(MESSAGE)
    print("---\n")

    if not args.dry_run:
        print("Sending in 5 seconds — Ctrl-C to abort...")
        try:
            for i in range(5, 0, -1):
                print(f"  {i}...", end=" ", flush=True)
                time.sleep(1)
            print()
        except KeyboardInterrupt:
            print("\nAborted.")
            return 130

    return send(args.dry_run)


if __name__ == "__main__":
    sys.exit(main())
