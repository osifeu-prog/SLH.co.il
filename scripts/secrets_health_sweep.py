#!/usr/bin/env python3
"""SLH Secrets Vault — scheduled health sweep.

Designed to be invoked by Windows Task Scheduler every 6h. Calls the
admin endpoint `POST /api/admin/secrets/sweep` on the live API which
iterates secrets_catalog, runs health probes, fires Telegram alerts
on transitions, and records to secret_alerts.

Reads ADMIN_API_KEYS from D:\\SLH_ECOSYSTEM\\.env (first key is used).
The actual key never appears in this script.

Exit codes:
    0 = sweep ran (regardless of how many alerts fired)
    1 = config error (no admin key)
    2 = API unreachable
    3 = API returned non-200

Usage:
    python secrets_health_sweep.py             # production (Railway API)
    python secrets_health_sweep.py --local     # localhost API for testing
    python secrets_health_sweep.py --verbose   # print full response
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

API_PROD = "https://slh-api-production.up.railway.app"
API_LOCAL = "http://localhost:8899"
ENV_PATH = Path("D:/SLH_ECOSYSTEM/.env")


def load_admin_key(env_path: Path) -> str:
    if not env_path.exists():
        return ""
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        if k.strip() == "ADMIN_API_KEYS":
            v = v.strip().strip('"').strip("'")
            # Comma-separated; first one wins
            return v.split(",")[0].strip()
        if k.strip() == "ADMIN_API_KEY":
            return v.strip().strip('"').strip("'")
    return ""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--local", action="store_true", help="hit localhost:8899 instead of Railway")
    ap.add_argument("--verbose", action="store_true")
    ap.add_argument("--env", default=str(ENV_PATH))
    args = ap.parse_args()

    api = API_LOCAL if args.local else API_PROD
    admin_key = os.getenv("ADMIN_API_KEY") or load_admin_key(Path(args.env))
    if not admin_key:
        print("[ERR] ADMIN_API_KEYS not found in env or .env", file=sys.stderr)
        return 1

    url = f"{api}/api/admin/secrets/sweep"
    req = urllib.request.Request(
        url,
        method="POST",
        headers={"X-Admin-Key": admin_key, "Content-Type": "application/json"},
        data=b"{}",
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            body = r.read().decode("utf-8")
            data = json.loads(body)
    except urllib.error.HTTPError as e:
        print(f"[ERR] HTTP {e.code}: {e.read().decode('utf-8','replace')[:300]}", file=sys.stderr)
        return 3
    except Exception as e:
        print(f"[ERR] {type(e).__name__}: {e}", file=sys.stderr)
        return 2

    if args.verbose:
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        print(
            f"[SWEEP] checked={data.get('checked',0)} "
            f"transitions={data.get('transitions',0)} "
            f"alerts_sent={data.get('alerts_sent',0)} "
            f"overdue={data.get('overdue_alerts',0)} "
            f"cooldown={data.get('skipped_cooldown',0)} "
            f"no_probe={data.get('skipped_no_probe',0)}"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
