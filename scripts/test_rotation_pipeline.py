"""E2E smoke test harness for the SLH Token Rotation Pipeline.

Purpose:
    Validate that the pipeline is wired correctly BEFORE you do a live
    rotation against any production bot token. Three modes:

    --offline   (default) — config + module imports + endpoint introspection.
                Safe anywhere, no env vars needed, no network.

    --health    — calls /api/admin/rotation-pipeline/health on the live API.
                Requires: ADMIN_API_KEY env var. Read-only. No mutations.

    --live      — runs an actual rotation against TEST_BOT_TOKEN (Low tier).
                Requires: ADMIN_API_KEY + a fresh BotFather token in
                NEW_TOKEN env var. Will push to Railway + redeploy.

    --history   — pulls the last 20 audit entries to confirm structure.
                Requires: ADMIN_API_KEY.

Usage:
    cd D:\\SLH_ECOSYSTEM
    python scripts\\test_rotation_pipeline.py                  # offline
    python scripts\\test_rotation_pipeline.py --health
    python scripts\\test_rotation_pipeline.py --history
    $env:NEW_TOKEN = "<from BotFather>"
    python scripts\\test_rotation_pipeline.py --live
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

API_BASE = os.getenv("SLH_API_BASE", "https://slh-api-production.up.railway.app")


# ─── colored print helpers ─────────────────────────────────────────────────


def _ok(msg: str) -> None:
    print(f"  \033[92m✓\033[0m {msg}")


def _warn(msg: str) -> None:
    print(f"  \033[93m⚠\033[0m {msg}")


def _fail(msg: str) -> None:
    print(f"  \033[91m✗\033[0m {msg}")


def _h(msg: str) -> None:
    print(f"\n\033[1m{msg}\033[0m")


# ─── Tests ──────────────────────────────────────────────────────────────────


def test_offline() -> int:
    """Static-only checks. No network, no env vars."""
    failed = 0

    _h("[1/5] Validate config files")
    cfg_path = ROOT / "config" / "railway_services.json"
    if not cfg_path.exists():
        _fail(f"missing: {cfg_path}")
        return 1
    try:
        cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
        n = sum(1 for k in cfg["services"] if not k.startswith("_"))
        ids_filled = sum(
            1 for k, v in cfg["services"].items()
            if not k.startswith("_") and v.get("project_id")
        )
        by_tier: dict[str, int] = {}
        for k, v in cfg["services"].items():
            if k.startswith("_"):
                continue
            by_tier[v["tier"]] = by_tier.get(v["tier"], 0) + 1
        _ok(f"railway_services.json: {n} entries, by tier: {by_tier}")
        if ids_filled == 0:
            _warn(
                f"  IDs not yet resolved (0/{n}). "
                "Run: python scripts/railway_resolve_ids.py --write"
            )
        elif ids_filled < n:
            _warn(f"  partial IDs: {ids_filled}/{n}")
        else:
            _ok(f"  all {n} IDs resolved")
    except Exception as e:
        _fail(f"railway_services.json invalid: {e}")
        failed += 1

    cmds_path = ROOT / "config" / "bot_commands.json"
    if not cmds_path.exists():
        _fail(f"missing: {cmds_path}")
        failed += 1
    else:
        try:
            cmds = json.loads(cmds_path.read_text(encoding="utf-8"))
            n_default = len(cmds.get("default", []))
            n_per = len(cmds.get("per_bot", {}))
            _ok(f"bot_commands.json: {n_default} default, {n_per} per-bot")
        except Exception as e:
            _fail(f"bot_commands.json invalid: {e}")
            failed += 1

    _h("[2/5] Import modules")
    try:
        from routes import railway_client  # noqa: F401
        _ok("routes.railway_client imports clean")
    except Exception as e:
        _fail(f"routes.railway_client import failed: {e}")
        failed += 1
    try:
        from routes import rotation_pipeline
        _ok("routes.rotation_pipeline imports clean")
    except Exception as e:
        _fail(f"routes.rotation_pipeline import failed: {e}")
        failed += 1
        return failed  # everything below depends on this import

    _h("[3/5] Verify endpoints registered")
    expected = {
        "POST /api/admin/rotate-bot-token-pipeline",
        "GET /api/admin/rotation-history",
        "GET /api/admin/rotation-pipeline/health",
    }
    actual = set()
    for r in rotation_pipeline.router.routes:
        for m in r.methods:
            actual.add(f"{m} {r.path}")
    missing = expected - actual
    extra = actual - expected
    if missing:
        for m in missing:
            _fail(f"missing endpoint: {m}")
        failed += len(missing)
    else:
        _ok(f"all {len(expected)} endpoints registered")
    for e in extra:
        _ok(f"  (also: {e})")

    _h("[4/5] Verify security knobs")
    sec = rotation_pipeline._SECURITY_HEADERS
    required_headers = {"Cache-Control", "X-Robots-Tag", "X-Content-Type-Options"}
    missing_h = required_headers - sec.keys()
    if missing_h:
        _fail(f"missing security headers: {missing_h}")
        failed += 1
    else:
        _ok(f"security headers: {sorted(sec.keys())}")
    cd = rotation_pipeline.COOLDOWN_BY_TIER
    if cd.get("critical", 0) < cd.get("high", 0) or cd.get("high", 0) < cd.get("medium", 0):
        _fail(f"cooldown ordering wrong: {cd}")
        failed += 1
    else:
        _ok(f"cooldowns ordered correctly: {cd}")

    _h("[5/5] Verify main.py wiring (both copies)")
    for path in ("main.py", "api/main.py"):
        full = ROOT / path
        text = full.read_text(encoding="utf-8")
        has_import = "from routes.rotation_pipeline import router as rotation_pipeline_router" in text
        has_include = "app.include_router(rotation_pipeline_router)" in text
        if has_import and has_include:
            _ok(f"{path}: import + include_router both present")
        else:
            _fail(f"{path}: import={has_import} include_router={has_include}")
            failed += 1

    return failed


async def test_health() -> int:
    import httpx
    admin = os.getenv("ADMIN_API_KEY", "").strip()
    if not admin:
        _fail("ADMIN_API_KEY not set in env")
        return 1
    _h(f"GET {API_BASE}/api/admin/rotation-pipeline/health")
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.get(
            f"{API_BASE}/api/admin/rotation-pipeline/health",
            headers={"X-Admin-Key": admin},
        )
    if r.status_code != 200:
        _fail(f"HTTP {r.status_code}: {r.text[:300]}")
        return 1
    j = r.json()
    failed = 0
    for k in ("config_loaded", "railway_token_ok", "broadcast_bot_token_set"):
        if j.get(k):
            _ok(f"{k} = True")
        else:
            _warn(f"{k} = False/None ({j.get(k)})")
            failed += 1
    _ok(f"config_entries: {j.get('config_entries')}")
    _ok(f"railway_me_email: {j.get('railway_me_email')}")
    _ok(f"admin_telegram_ids: {j.get('admin_telegram_ids_count')}")
    if j.get("railway_error"):
        _warn(f"railway_error: {j['railway_error']}")
    return failed


async def test_history() -> int:
    import httpx
    admin = os.getenv("ADMIN_API_KEY", "").strip()
    if not admin:
        _fail("ADMIN_API_KEY not set in env")
        return 1
    _h(f"GET {API_BASE}/api/admin/rotation-history?limit=20")
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.get(
            f"{API_BASE}/api/admin/rotation-history?limit=20",
            headers={"X-Admin-Key": admin},
        )
    if r.status_code != 200:
        _fail(f"HTTP {r.status_code}: {r.text[:300]}")
        return 1
    j = r.json()
    events = j.get("events") or []
    _ok(f"got {len(events)} audit events")
    by_action: dict[str, int] = {}
    for e in events:
        a = e.get("action", "?")
        by_action[a] = by_action.get(a, 0) + 1
    for a, n in sorted(by_action.items()):
        _ok(f"  {a}: {n}")
    if events:
        latest = events[0]
        _ok(f"latest: {latest.get('action')} on {latest.get('resource_id')} at {latest.get('created_at')}")
    return 0


async def test_live() -> int:
    """Run an actual rotation against TEST_BOT_TOKEN (Low tier, no cooldown).

    Requires:
        ADMIN_API_KEY  — admin auth header
        NEW_TOKEN      — a fresh token revoked from BotFather just now
    """
    import httpx
    admin = os.getenv("ADMIN_API_KEY", "").strip()
    new_token = os.getenv("NEW_TOKEN", "").strip()
    if not admin:
        _fail("ADMIN_API_KEY not set")
        return 1
    if not new_token:
        _fail("NEW_TOKEN not set (paste from BotFather → /revoke @SLH_Test_bot)")
        return 1
    if not new_token.count(":") == 1 or len(new_token) < 35:
        _fail("NEW_TOKEN doesn't look like a Telegram token")
        return 1

    _h("Live rotation against TEST_BOT_TOKEN (Low tier, swap-target)")
    payload = {
        "env_var": "TEST_BOT_TOKEN",
        "new_token": new_token,
        "expect_handle": "@SLH_Test_bot",
    }
    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post(
            f"{API_BASE}/api/admin/rotate-bot-token-pipeline",
            headers={"X-Admin-Key": admin, "Content-Type": "application/json"},
            json=payload,
        )
    j = r.json() if r.headers.get("content-type", "").startswith("application/json") else {"raw": r.text[:500]}
    print(f"  HTTP {r.status_code}")
    print(f"  body: {json.dumps(j, indent=2, ensure_ascii=False)[:800]}")
    if r.status_code != 200:
        _fail("rotation returned non-200")
        return 1
    if j.get("ok") is True:
        _ok(f"rotation OK — deploy_id={j.get('deploy_id')}, last4={j.get('last4')}")
        _ok(f"verified as @{j.get('tg_username')} (id={j.get('tg_bot_id')})")
        return 0
    if j.get("phase") == "healthcheck_failed":
        _warn("healthcheck_failed — variable was pushed but bot not responding")
        _warn("  → check Railway logs; may need manual revert")
        return 1
    _fail(f"unexpected response shape: {j}")
    return 1


def main() -> int:
    ap = argparse.ArgumentParser(description="SLH Rotation Pipeline E2E test harness")
    ap.add_argument("--health", action="store_true", help="hit live /api/admin/rotation-pipeline/health")
    ap.add_argument("--history", action="store_true", help="pull last 20 audit events")
    ap.add_argument("--live", action="store_true", help="rotate TEST_BOT_TOKEN (requires NEW_TOKEN env)")
    args = ap.parse_args()

    print("\n\033[1mSLH Rotation Pipeline — E2E Smoke Test\033[0m")
    print(f"API base: {API_BASE}")

    failed = 0
    failed += test_offline()

    if args.health:
        failed += asyncio.run(test_health())
    if args.history:
        failed += asyncio.run(test_history())
    if args.live:
        failed += asyncio.run(test_live())

    print()
    if failed == 0:
        print("\033[92m✓ all tests passed\033[0m")
        return 0
    print(f"\033[91m✗ {failed} test(s) failed\033[0m")
    return 1


if __name__ == "__main__":
    sys.exit(main())
