"""SLH.co.il daily digest — readable summary of today's + 7-day activity.

Usage:
    railway run python ops/daily_digest.py               # text, default
    railway run python ops/daily_digest.py --json        # machine-readable
    railway run python ops/daily_digest.py --period 30   # 30 days instead of 7

No secrets printed. Safe to pipe to a file or Telegram message.
"""
import argparse
import json
import os
import sys
from datetime import datetime, timedelta

# Force UTF-8 stdout on Windows so Hebrew / emoji chars in user data don't crash print().
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

try:
    import psycopg2
except ImportError:
    print("psycopg2 not installed — run via 'railway run' or install locally", file=sys.stderr)
    sys.exit(1)


def parse_args():
    p = argparse.ArgumentParser(description="SLH.co.il daily activity digest")
    p.add_argument("--json", action="store_true", help="Machine-readable JSON output")
    p.add_argument("--period", type=int, default=7, help="Window in days for stats (default: 7)")
    return p.parse_args()


def iso_days_ago(n):
    return (datetime.utcnow() - timedelta(days=n)).isoformat()


def collect(conn, period_days):
    cur = conn.cursor()
    data = {
        "generated_at_utc": datetime.utcnow().isoformat(timespec="seconds"),
        "period_days": period_days,
    }

    cur.execute("SELECT COUNT(*) FROM users")
    data["users_total"] = cur.fetchone()[0]
    cur.execute(
        "SELECT COUNT(*) FROM users WHERE first_seen IS NOT NULL "
        "AND first_seen::timestamp::date = CURRENT_DATE"
    )
    data["users_today"] = cur.fetchone()[0]
    cur.execute(
        "SELECT COUNT(*) FROM users WHERE first_seen IS NOT NULL AND first_seen >= %s",
        (iso_days_ago(period_days),),
    )
    data["users_period"] = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM roi_records")
    data["roi_total"] = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM roi_records WHERE DATE(created_at) = CURRENT_DATE")
    data["roi_today"] = cur.fetchone()[0]
    cur.execute(
        "SELECT COUNT(*) FROM roi_records WHERE created_at >= NOW() - INTERVAL '%s days'"
        % period_days
    )
    data["roi_period"] = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM feedback")
    data["feedback_total"] = cur.fetchone()[0]
    cur.execute(
        "SELECT COUNT(*) FROM feedback WHERE timestamp IS NOT NULL "
        "AND timestamp::timestamp::date = CURRENT_DATE"
    )
    data["feedback_today"] = cur.fetchone()[0]
    cur.execute(
        "SELECT COUNT(*) FROM feedback WHERE timestamp IS NOT NULL AND timestamp >= %s",
        (iso_days_ago(period_days),),
    )
    data["feedback_period"] = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM preorders")
    data["preorders_total"] = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM preorders WHERE DATE(created_at) = CURRENT_DATE")
    data["preorders_today"] = cur.fetchone()[0]
    cur.execute("SELECT status, COUNT(*) FROM preorders GROUP BY status ORDER BY status")
    data["preorders_by_status"] = {row[0]: row[1] for row in cur.fetchall()}

    cur.execute(
        "SELECT id, username, first_name, product, created_at FROM preorders "
        "ORDER BY created_at DESC LIMIT 3"
    )
    data["recent_preorders"] = [
        {
            "id": r[0],
            "user": r[1] or r[2] or "unknown",
            "product": r[3],
            "at": r[4].isoformat(timespec="seconds") if r[4] else None,
        }
        for r in cur.fetchall()
    ]

    cur.execute(
        "SELECT id, username, message, timestamp FROM feedback "
        "ORDER BY id DESC LIMIT 3"
    )
    data["recent_feedback"] = [
        {
            "id": r[0],
            "user": r[1] or "unknown",
            "message": (r[2] or "")[:80],
            "at": r[3],
        }
        for r in cur.fetchall()
    ]

    cur.close()
    return data


def render_text(d):
    lines = [
        f"=== SLH.co.il Daily Digest — {d['generated_at_utc']}Z ===",
        f"    period: last {d['period_days']} days",
        "",
        "USERS",
        f"  total        {d['users_total']}",
        f"  today        {d['users_today']}",
        f"  last {d['period_days']}d      {d['users_period']}",
        "",
        "ROI RECORDS",
        f"  total        {d['roi_total']}",
        f"  today        {d['roi_today']}",
        f"  last {d['period_days']}d      {d['roi_period']}",
        "",
        "FEEDBACK",
        f"  total        {d['feedback_total']}",
        f"  today        {d['feedback_today']}",
        f"  last {d['period_days']}d      {d['feedback_period']}",
        "",
        "PREORDERS (Guardian early-bird)",
        f"  total        {d['preorders_total']}",
        f"  today        {d['preorders_today']}",
    ]
    if d["preorders_by_status"]:
        lines.append("  by status:")
        for status, count in d["preorders_by_status"].items():
            lines.append(f"    {status}: {count}")

    if d["recent_preorders"]:
        lines.append("")
        lines.append("RECENT PREORDERS")
        for p in d["recent_preorders"]:
            lines.append(f"  #{p['id']} · {p['user']} · {p['product']} · {p['at']}")

    if d["recent_feedback"]:
        lines.append("")
        lines.append("RECENT FEEDBACK (last 3)")
        for f in d["recent_feedback"]:
            lines.append(f"  #{f['id']} · {f['user']}: {f['message']}")

    return "\n".join(lines)


def main():
    args = parse_args()
    url = os.getenv("DATABASE_URL")
    if not url:
        print("DATABASE_URL not set — run via 'railway run'", file=sys.stderr)
        sys.exit(1)
    conn = psycopg2.connect(url)
    try:
        data = collect(conn, args.period)
    finally:
        conn.close()
    if args.json:
        print(json.dumps(data, default=str, indent=2, ensure_ascii=False))
    else:
        print(render_text(data))


if __name__ == "__main__":
    main()
