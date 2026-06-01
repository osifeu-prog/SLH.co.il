#!/usr/bin/env python3
"""Create a pending_payment_intent on the SLH Railway API so the monitor can
auto-match an incoming BSC/TON transfer to a user.

Background:
  * `POST /api/payment/monitor/intent` on Railway inserts a row into
    pending_payment_intents.
  * The BSC monitor polls Genesis every 30s; when a new incoming tx lands,
    it looks for an open intent with matching chain + amount (+/- tolerance)
    and flips premium for the matched user.
  * TON has no active poller; for TON you still need to call
    /api/payment/ton/auto-verify with the tx_hash (see docstring at bottom).

Usage:
  python ops/create_payment_intent.py <user_id> <bsc|ton> <amount> [plan_key] [bot_name]

Examples:
  python ops/create_payment_intent.py 224223270 bsc 0.001
  python ops/create_payment_intent.py 224223270 ton 0.01 academy_1 academia
"""
from __future__ import annotations

import json
import sys
import urllib.parse
import urllib.request

API_BASE = "https://slh-api-production.up.railway.app"


def main(argv: list[str]) -> int:
    if len(argv) < 4:
        print(__doc__)
        return 2

    user_id = int(argv[1])
    chain = argv[2].lower()
    expected_amount = float(argv[3])
    plan_key = argv[4] if len(argv) > 4 else "premium"
    bot_name = argv[5] if len(argv) > 5 else "ecosystem"

    if chain not in ("bsc", "ton"):
        print(f"ERR: chain must be 'bsc' or 'ton' (got {chain!r})", file=sys.stderr)
        return 2

    qs = urllib.parse.urlencode({
        "user_id": user_id,
        "chain": chain,
        "expected_amount": expected_amount,
        "plan_key": plan_key,
        "bot_name": bot_name,
    })
    url = f"{API_BASE}/api/payment/monitor/intent?{qs}"

    req = urllib.request.Request(url, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            body = r.read().decode("utf-8")
    except Exception as e:
        print(f"ERR: request failed: {e}", file=sys.stderr)
        return 1

    data = json.loads(body)
    if not data.get("ok"):
        print(f"ERR: API returned {body}", file=sys.stderr)
        return 1

    print(json.dumps(data, indent=2, ensure_ascii=False))
    print()
    print(f"  intent_id   : {data['intent_id']}")
    print(f"  chain       : {chain}")
    print(f"  amount      : {expected_amount}")
    print(f"  expires_at  : {data['expires_at']}")
    print()
    if chain == "bsc":
        print("Next step: send EXACTLY the amount to:")
        print("  0xd061de73b06d5e91bfa46b35efb7b08b16903da4 (BSC Genesis)")
        print("Monitor auto-matches within 30-60 seconds.")
    else:
        print("Next step: send EXACTLY the amount to:")
        print("  UQCr743gEr_nqV_0SBkSp3CtYS_15R3LDLBvLmKeEv7XdGvp (TON wallet)")
        print("TON has no auto-poller; after paying, call:")
        print(f"  POST {API_BASE}/api/payment/ton/auto-verify")
        print(f'  body: {{"user_id":{user_id},"bot_name":"{bot_name}",'
              f'"plan_key":"{plan_key}","tx_hash":"<hash from @wallet>"}}')
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
