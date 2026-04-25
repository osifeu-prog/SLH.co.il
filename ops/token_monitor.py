"""SLH Token Monitor — pure module + CLI entrypoint.

Two consumers:
1. CLI: `python ops/token_monitor.py` → colored health table for terminal
2. Bot: `from ops.token_monitor import check_all` → use in bot commands

Design:
- Token VALUES never stored here. Only env var NAMES (from ops/tokens.json).
- A bot's token is checked only if its env var is present in the running environment.
- `getMe` is the canonical Telegram health endpoint (read-only, idempotent, fast).
- 401 = revoked. 200 = healthy. timeout / connect error = unknown (probably ok).

Add to a bot:
    from ops.token_monitor import check_all
    statuses = await check_all()
    # render in /tokens command

Run from CLI:
    python ops/token_monitor.py            # text table
    python ops/token_monitor.py --json     # machine-readable
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional

try:
    import urllib.request
    import urllib.error
except ImportError:
    urllib = None  # type: ignore

# Force UTF-8 on Windows so Hebrew / emojis don't crash
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass


REGISTRY_PATH = Path(__file__).parent / "tokens.json"
TIMEOUT_SEC = 10


@dataclass
class TokenStatus:
    name: str
    username: str
    owner: str
    tier: str
    env_var: str
    env_set: bool
    state: str  # "healthy" / "revoked" / "unknown" / "no_token_in_env"
    detail: str
    checked_at: str

    def emoji(self) -> str:
        return {
            "healthy": "✅",
            "revoked": "❌",
            "unknown": "⚠️",
            "no_token_in_env": "⚪",
        }.get(self.state, "❓")


def load_registry(path: Path = REGISTRY_PATH) -> list[dict]:
    if not path.exists():
        raise FileNotFoundError(f"Token registry not found: {path}")
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return data.get("monitored_bots", [])


async def _check_one_async(entry: dict) -> TokenStatus:
    env_var = entry["env_var"]
    token = os.getenv(env_var, "")
    now = datetime.utcnow().isoformat(timespec="seconds")
    base = dict(
        name=entry.get("name", "?"),
        username=entry.get("username", "?"),
        owner=entry.get("owner", "?"),
        tier=entry.get("tier", "?"),
        env_var=env_var,
        env_set=bool(token),
        checked_at=now,
    )

    if not token:
        return TokenStatus(state="no_token_in_env", detail=f"{env_var} not in env", **base)

    url = f"https://api.telegram.org/bot{token}/getMe"
    try:
        # Run blocking urllib in a thread to keep async-friendly
        body = await asyncio.to_thread(_http_get_json, url)
        if body.get("ok"):
            uname = body.get("result", {}).get("username", "?")
            return TokenStatus(state="healthy", detail=f"@{uname} responding", **base)
        return TokenStatus(state="revoked", detail=body.get("description", "ok=false"), **base)
    except urllib.error.HTTPError as e:  # type: ignore
        if e.code == 401:
            return TokenStatus(state="revoked", detail="HTTP 401 Unauthorized — token revoked", **base)
        return TokenStatus(state="unknown", detail=f"HTTP {e.code} {e.reason}", **base)
    except Exception as e:
        return TokenStatus(state="unknown", detail=f"{type(e).__name__}: {e}", **base)


def _http_get_json(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": "slh-token-monitor/1.0"})
    with urllib.request.urlopen(req, timeout=TIMEOUT_SEC) as resp:
        return json.loads(resp.read())


async def check_all(registry_path: Optional[Path] = None) -> list[TokenStatus]:
    """Concurrent check of every bot in the registry."""
    bots = load_registry(registry_path or REGISTRY_PATH)
    return await asyncio.gather(*(_check_one_async(b) for b in bots))


def render_table(statuses: list[TokenStatus]) -> str:
    by_state: dict[str, int] = {}
    for s in statuses:
        by_state[s.state] = by_state.get(s.state, 0) + 1

    lines = [
        "=== SLH Bot Token Health ===",
        f"checked at {datetime.utcnow().isoformat(timespec='seconds')}Z",
        "",
        f"{'Bot':<28}{'Tier':<14}{'Env':<8}{'State':<14}{'Detail'}",
        "-" * 100,
    ]
    for s in statuses:
        env_mark = "✓" if s.env_set else "—"
        lines.append(
            f"{s.emoji()} {s.name:<26}{s.tier:<14}{env_mark:<8}{s.state:<14}{s.detail}"
        )
    lines.append("")
    lines.append("Summary: " + " · ".join(f"{k}={v}" for k, v in sorted(by_state.items())))
    needs_action = [s for s in statuses if s.state == "revoked"]
    if needs_action:
        lines.append("")
        lines.append("⚠ NEEDS ROTATION:")
        for s in needs_action:
            lines.append(f"  {s.name} (@{s.username}) — {s.detail}")
            lines.append(f"    1) BotFather: /mybots → @{s.username} → API Token → Revoke")
            lines.append(f"    2) Railway: update env var {s.env_var}")
    return "\n".join(lines)


def render_telegram(statuses: list[TokenStatus]) -> str:
    """Markdown render for sending in a Telegram message via bot."""
    lines = ["🩺 *Bot Token Health*", ""]
    for s in statuses:
        lines.append(f"{s.emoji()} `{s.name}` · {s.state}")
    revoked = [s for s in statuses if s.state == "revoked"]
    if revoked:
        lines.append("")
        lines.append("⚠️ *Needs rotation:*")
        for s in revoked:
            lines.append(f"  • `{s.name}` — env var `{s.env_var}`")
    no_env = [s for s in statuses if s.state == "no_token_in_env"]
    if no_env:
        lines.append("")
        lines.append(f"_⚪ {len(no_env)} bots not checked from this service (env vars not set here)_")
    return "\n".join(lines)


async def main_cli():
    parser = argparse.ArgumentParser(description="SLH bot token monitor")
    parser.add_argument("--json", action="store_true", help="JSON output")
    args = parser.parse_args()

    statuses = await check_all()
    if args.json:
        print(json.dumps([asdict(s) for s in statuses], ensure_ascii=False, indent=2))
    else:
        print(render_table(statuses))

    revoked_count = sum(1 for s in statuses if s.state == "revoked")
    sys.exit(1 if revoked_count else 0)


if __name__ == "__main__":
    asyncio.run(main_cli())
