#!/usr/bin/env python3
"""SLH Secrets Vault — daily digest sender.

Designed to be invoked by Windows Task Scheduler at 21:00 Israel time.
Calls `POST /api/admin/secrets/digest/send` which composes a Hebrew
Telegram digest of the last 24h transitions + currently overdue secrets
and sends it to Osif's tg_id (224223270).

Reads ADMIN_API_KEYS from D:\\SLH_ECOSYSTEM\\.env (first key wins). Same
auth pattern as secrets_health_sweep.py.

Exit codes mirror secrets_health_sweep.py.

Usage:
    python secrets_daily_digest.py               # production
    python secrets_daily_digest.py --local       # localhost for testing
    python secrets_daily_digest.py --verbose
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
            return v.split(",")[0].strip()
        if k.strip() == "ADMIN_API_KEY":
            return v.strip().strip('"').strip("'")
    return ""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--local", action="store_true")
    ap.add_argument("--verbose", action="store_true")
    ap.add_argument("--env", default=str(ENV_PATH))
    args = ap.parse_args()

    api = API_LOCAL if args.local else API_PROD
    admin_key = os.getenv("ADMIN_API_KEY") or load_admin_key(Path(args.env))
    if not admin_key:
        print("[ERR] ADMIN_API_KEYS not found", file=sys.stderr)
        return 1

    url = f"{api}/api/admin/secrets/digest/send"
    req = urllib.request.Request(
        url,
        method="POST",
        headers={"X-Admin-Key": admin_key, "Content-Type": "application/json"},
        data=b"{}",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
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
        s = data.get("summary", {})
        print(
            f"[DIGEST] sent={data.get('ok',False)} "
            f"total={s.get('total',0)} broken={s.get('broken',0)} "
            f"overdue={s.get('overdue',0)} alerts_24h={s.get('alerts_24h',0)}"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
