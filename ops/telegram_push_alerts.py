#!/usr/bin/env python3
"""
SLH Telegram Push Alerts — daily digest + threshold-based alerts.

Polls the Railway API for:
  - /api/performance/digest  (daily snapshot)
  - /api/events/public       (new events since last run)
  - /api/health              (system heartbeat)

Sends formatted messages via @SLH_AIR_bot (or any BOT_TOKEN set) to a
configured chat_id (e.g. Osif's admin channel).

Designed to be run by Task Scheduler every N hours. State persists in
~/.slh_push_state.json so we don't resend the same events.

Usage:
    python telegram_push_alerts.py --chat-id 224223270 --mode digest
    python telegram_push_alerts.py --chat-id 224223270 --mode events
    python telegram_push_alerts.py --chat-id 224223270 --mode both

Env vars required (read from D:/SLH_ECOSYSTEM/.env):
    BROADCAST_BOT_TOKEN         — bot token for @SLH_AIR_bot
    ADMIN_BROADCAST_KEY         — for authenticated endpoints (optional)

Exit codes:
    0 = ok (message sent or nothing new)
    1 = config error
    2 = API unreachable
    3 = Telegram send failed
"""
from __future__ import annotations
import argparse
import json
import os
import sys
import urllib.request
import urllib.error
import urllib.parse
from pathlib import Path

API_BASE = "https://slh-api-production.up.railway.app"
STATE_FILE = Path.home() / ".slh_push_state.json"


def load_env(env_path: Path) -> dict:
    if not env_path.exists():
        return {}
    out = {}
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        out[k.strip()] = v.strip().strip('"').strip("'")
    return out


def http_get_json(url: str, headers: dict | None = None, timeout: float = 15) -> dict:
    req = urllib.request.Request(url, headers=headers or {})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def tg_send(bot_token: str, chat_id: int, text: str, parse_mode: str = "HTML") -> bool:
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = urllib.parse.urlencode({
        "chat_id": chat_id,
        "text": text,
        "parse_mode": parse_mode,
        "disable_web_page_preview": "false",
    }).encode("utf-8")
    req = urllib.request.Request(url, data=payload, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            data = json.loads(r.read().decode("utf-8"))
            return bool(data.get("ok"))
    except urllib.error.HTTPError as e:
        print(f"[TG][ERROR] {e.code}: {e.read().decode('utf-8', errors='replace')[:500]}", file=sys.stderr)
        return False
    except Exception as e:
        print(f"[TG][ERROR] {e!r}", file=sys.stderr)
        return False


def load_state() -> dict:
    if not STATE_FILE.exists():
        return {}
    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_state(state: dict) -> None:
    STATE_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")


def mode_digest(bot_token: str, chat_id: int) -> int:
    try:
        data = http_get_json(f"{API_BASE}/api/performance/digest")
    except Exception as e:
        print(f"[DIGEST][ERROR] fetch failed: {e!r}", file=sys.stderr)
        return 2
    text = data.get("text") or "No digest available"
    if not tg_send(bot_token, chat_id, text):
        return 3
    print(f"[DIGEST] sent to {chat_id} ({data.get('token_count','?')} tokens)")
    return 0


def mode_events(bot_token: str, chat_id: int, state: dict) -> int:
    last_id = state.get("last_event_id", 0)
    try:
        data = http_get_json(f"{API_BASE}/api/events/public?limit=20&since_id={last_id}")
    except Exception as e:
        print(f"[EVENTS][ERROR] fetch failed: {e!r}", file=sys.stderr)
        return 2

    events = data.get("events", [])
    if not events:
        print("[EVENTS] nothing new")
        return 0

    # Compact summary (< 4000 chars for Telegram)
    lines = [f"<b>SLH events update</b>  ({len(events)} new)\n"]
    for ev in events[:15]:
        lines.append(f"• <code>{ev['type']}</code>  at {ev.get('at','?')[:19].replace('T',' ')}")

    if len(events) > 15:
        lines.append(f"\n(+{len(events)-15} more)")

    lines.append(f'\n<a href="https://slh-nft.com/chain-status.html">Live status</a>')

    if not tg_send(bot_token, chat_id, "\n".join(lines)):
        return 3

    # Update state to max id
    max_id = max(ev["id"] for ev in events)
    state["last_event_id"] = max_id
    save_state(state)
    print(f"[EVENTS] sent {len(events)} events, last_id={max_id}")
    return 0


def mode_health(bot_token: str, chat_id: int) -> int:
    try:
        health = http_get_json(f"{API_BASE}/api/health")
    except Exception as e:
        # Health failed — alert!
        tg_send(bot_token, chat_id, f"<b>🚨 SLH API is DOWN</b>\n\n<code>{e!r}</code>")
        return 2

    status = health.get("status")
    if status == "ok":
        print(f"[HEALTH] ok (silent)")
        return 0
    text = f"<b>⚠️ SLH API health degraded</b>\n\n<code>{json.dumps(health, ensure_ascii=False)}</code>"
    tg_send(bot_token, chat_id, text)
    return 2


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--chat-id", type=int, required=True, help="Telegram chat_id to send to")
    ap.add_argument("--mode", choices=["digest", "events", "health", "both", "all"], default="digest")
    ap.add_argument("--env", default="D:/SLH_ECOSYSTEM/.env")
    args = ap.parse_args()

    env = load_env(Path(args.env))
    bot_token = env.get("BROADCAST_BOT_TOKEN") or os.getenv("BROADCAST_BOT_TOKEN") or ""
    if not bot_token:
        print("[ERROR] BROADCAST_BOT_TOKEN not found in .env or environment", file=sys.stderr)
        return 1

    state = load_state()
    rc = 0

    if args.mode in ("digest", "both", "all"):
        rc |= mode_digest(bot_token, args.chat_id)
    if args.mode in ("events", "both", "all"):
        rc |= mode_events(bot_token, args.chat_id, state)
    if args.mode in ("health", "all"):
        rc |= mode_health(bot_token, args.chat_id)

    return rc


if __name__ == "__main__":
    sys.exit(main())
