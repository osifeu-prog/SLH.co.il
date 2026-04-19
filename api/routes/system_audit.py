"""
System Audit - live monitoring infrastructure for the SLH Spark ecosystem.

Single aggregator endpoint that powers /system-audit.html. Every field is
computed defensively: if one query fails, that field comes back `null` -
the whole response never 500s because a single sub-query broke.

Endpoints:
  GET /api/system/audit               - full JSON audit snapshot
  GET /api/system/audit/health-check  - tiny quick health for Uptime Robot
"""
from __future__ import annotations

import os
import time
import asyncio
import subprocess
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Request


router = APIRouter(prefix="/api/system", tags=["System Audit"])

# Global connection pool (set by main.py, mirror of other routers' pattern)
_pool = None

# Process start time - used for uptime. Captured at module import.
_PROCESS_START = time.time()

API_VERSION = "1.2.0"

# Tokens we track. Each entry: (symbol, holders_table, supply_table_or_none, supply_col)
# For internal tokens, holders = distinct user_ids in token_balances. Supply = SUM(balance).
# For on-chain tokens (SLH), "supply" is a fixed cap reported elsewhere; we return null here.
_TOKENS = ["SLH", "ZVK", "MNH", "REP", "ZUZ", "AIC"]

# Hardcoded from ecosystem spec (docker-compose services + bot lineup)
_TOTAL_BOTS = 25


def set_pool(pool):
    """Inject the shared asyncpg pool from main.py startup."""
    global _pool
    _pool = pool


# ------------------------------------------------------------------
# Helper: run a coroutine that returns a value, return None on failure
# ------------------------------------------------------------------
async def _safe(coro, default=None):
    try:
        return await coro
    except Exception:
        return default


# ------------------------------------------------------------------
# Individual field collectors (each catches its own exceptions)
# ------------------------------------------------------------------
async def _collect_api(request: Request) -> dict:
    try:
        endpoint_count = len([r for r in request.app.routes if hasattr(r, "path")])
    except Exception:
        endpoint_count = None
    uptime = int(time.time() - _PROCESS_START)
    return {
        "version": API_VERSION,
        "uptime_seconds": uptime,
        "endpoint_count": endpoint_count,
    }


async def _collect_database() -> dict:
    if _pool is None:
        return {
            "connected": False, "tables": None, "total_rows": None,
            "latest_backup": "not_configured",
        }

    connected = False
    tables = None
    total_rows = None
    latest_backup = "not_configured"

    try:
        async with _pool.acquire() as conn:
            # Connectivity probe
            try:
                await conn.fetchval("SELECT 1")
                connected = True
            except Exception:
                connected = False

            # Table count (public schema)
            try:
                tables = await conn.fetchval(
                    "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public'"
                )
            except Exception:
                tables = None

            # Total rows across all public tables - uses reltuples statistic (cheap, approximate)
            try:
                total_rows = await conn.fetchval(
                    """
                    SELECT COALESCE(SUM(reltuples)::BIGINT, 0)
                    FROM pg_class c
                    JOIN pg_namespace n ON n.oid = c.relnamespace
                    WHERE c.relkind = 'r' AND n.nspname = 'public'
                    """
                )
                if total_rows is not None:
                    total_rows = int(total_rows)
            except Exception:
                total_rows = None

            # Latest backup - only if a backups table exists. Differentiate
            # "no data yet" (null) from "feature not set up" (not_configured).
            try:
                has_backup_tbl = await conn.fetchval(
                    "SELECT EXISTS (SELECT 1 FROM information_schema.tables "
                    "WHERE table_schema='public' AND table_name='backups')"
                )
                if has_backup_tbl:
                    latest = await conn.fetchval(
                        "SELECT MAX(created_at) FROM backups"
                    )
                    latest_backup = latest.isoformat() if latest else None
                else:
                    latest_backup = "not_configured"
            except Exception:
                latest_backup = "not_configured"
    except Exception:
        pass

    return {
        "connected": connected,
        "tables": tables,
        "total_rows": total_rows,
        "latest_backup": latest_backup,
    }


async def _collect_bots() -> dict:
    """
    Active bot count.

    We don't have a dedicated `bots` table. Strategy (in priority order):
      1. If a `bots` table exists - prefer it.
      2. Else count distinct `actor_user_id` in `institutional_audit` for
         `actor_type='bot'` within the last 5 minutes (proxy for "live").
      3. Else count distinct telegram_id in recent `analytics_events`
         WHERE data->>'source'='bot' in the last 5 minutes.
      4. Else null.
    """
    active = None
    if _pool is None:
        return {"total": _TOTAL_BOTS, "active": None}

    try:
        async with _pool.acquire() as conn:
            # Strategy 1: explicit bots table
            has_bots = await conn.fetchval(
                "SELECT EXISTS (SELECT 1 FROM information_schema.tables "
                "WHERE table_schema='public' AND table_name='bots')"
            )
            if has_bots:
                for col_expr in ("is_active=TRUE", "active=TRUE", "status='active'"):
                    try:
                        active = await conn.fetchval(
                            f"SELECT COUNT(*) FROM bots WHERE {col_expr}"
                        )
                        break
                    except Exception:
                        continue
                if active is None:
                    try:
                        active = await conn.fetchval("SELECT COUNT(*) FROM bots")
                    except Exception:
                        active = None
                if active is not None:
                    return {"total": _TOTAL_BOTS, "active": int(active)}

            # Strategy 2: audit trail proxy (bots writing in last 5 min)
            try:
                has_audit = await conn.fetchval(
                    "SELECT EXISTS (SELECT 1 FROM information_schema.tables "
                    "WHERE table_schema='public' AND table_name='institutional_audit')"
                )
                if has_audit:
                    cutoff = datetime.utcnow() - timedelta(minutes=5)
                    active = await conn.fetchval(
                        """
                        SELECT COUNT(DISTINCT actor_user_id)
                        FROM institutional_audit
                        WHERE actor_type = 'bot' AND timestamp >= $1
                        """,
                        cutoff,
                    )
                    if active is not None and active > 0:
                        return {"total": _TOTAL_BOTS, "active": int(active)}
            except Exception:
                pass

            # Strategy 3: analytics events proxy
            try:
                has_events = await conn.fetchval(
                    "SELECT EXISTS (SELECT 1 FROM information_schema.tables "
                    "WHERE table_schema='public' AND table_name='analytics_events')"
                )
                if has_events:
                    cutoff = datetime.utcnow() - timedelta(minutes=5)
                    active = await conn.fetchval(
                        """
                        SELECT COUNT(DISTINCT data->>'bot_name')
                        FROM analytics_events
                        WHERE data ? 'bot_name' AND created_at >= $1
                        """,
                        cutoff,
                    )
                    if active is not None and active > 0:
                        return {"total": _TOTAL_BOTS, "active": int(active)}
            except Exception:
                pass
    except Exception:
        active = None

    return {"total": _TOTAL_BOTS, "active": active}


async def _collect_tokens() -> dict:
    """For each token: holders = distinct users with balance>0, supply = SUM(balance)."""
    out = {sym: {"holders": None, "supply": None} for sym in _TOKENS}
    if _pool is None:
        return out

    try:
        async with _pool.acquire() as conn:
            # Check if token_balances table exists
            has_tb = await conn.fetchval(
                "SELECT EXISTS (SELECT 1 FROM information_schema.tables "
                "WHERE table_schema='public' AND table_name='token_balances')"
            )
            if not has_tb:
                return out

            for sym in _TOKENS:
                try:
                    row = await conn.fetchrow(
                        """
                        SELECT
                            COUNT(DISTINCT user_id) FILTER (WHERE balance > 0) AS holders,
                            COALESCE(SUM(balance), 0) AS supply
                        FROM token_balances
                        WHERE token = $1
                        """,
                        sym,
                    )
                    if row is not None:
                        out[sym] = {
                            "holders": int(row["holders"]) if row["holders"] is not None else None,
                            "supply": float(row["supply"]) if row["supply"] is not None else None,
                        }
                except Exception:
                    # keep defaults (null/null) for this token
                    pass
    except Exception:
        pass

    return out


async def _collect_git() -> dict:
    """
    Return last commit sha + message.

    Priority:
      1. Railway-injected env vars (RAILWAY_GIT_COMMIT_SHA,
         RAILWAY_GIT_COMMIT_MESSAGE) - always set on Railway.
      2. Shell out to `git` (works when .git is in image or locally).
      3. Read .git/HEAD + .git/COMMIT_EDITMSG as final fallback.
      4. Both null.
    """
    sha: Optional[str] = None
    message: Optional[str] = None

    # 1. Railway env vars (cleanest)
    sha = os.getenv("RAILWAY_GIT_COMMIT_SHA") or os.getenv("GIT_SHA") or None
    message = (
        os.getenv("RAILWAY_GIT_COMMIT_MESSAGE")
        or os.getenv("GIT_COMMIT_MESSAGE")
        or None
    )
    if sha and message:
        return {"last_commit_sha": sha, "last_commit_message": message}

    # 2. git CLI
    try:
        repo_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if sha is None:
            sha_raw = subprocess.run(
                ["git", "-C", repo_dir, "rev-parse", "HEAD"],
                capture_output=True, text=True, timeout=2,
            )
            if sha_raw.returncode == 0:
                sha = sha_raw.stdout.strip() or None
        if message is None:
            msg_raw = subprocess.run(
                ["git", "-C", repo_dir, "log", "-1", "--pretty=%s"],
                capture_output=True, text=True, timeout=2,
            )
            if msg_raw.returncode == 0:
                message = msg_raw.stdout.strip() or None
    except Exception:
        pass

    # 3. raw .git files (only if git CLI missing / Railway with .git shipped)
    try:
        repo_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if sha is None:
            head_path = os.path.join(repo_dir, ".git", "HEAD")
            if os.path.isfile(head_path):
                with open(head_path, "r", encoding="utf-8", errors="ignore") as f:
                    head = f.read().strip()
                if head.startswith("ref: "):
                    ref_path = os.path.join(repo_dir, ".git", head[5:].strip())
                    if os.path.isfile(ref_path):
                        with open(ref_path, "r", encoding="utf-8", errors="ignore") as f:
                            sha = f.read().strip() or None
                else:
                    sha = head or None
        if message is None:
            msg_path = os.path.join(repo_dir, ".git", "COMMIT_EDITMSG")
            if os.path.isfile(msg_path):
                with open(msg_path, "r", encoding="utf-8", errors="ignore") as f:
                    message = (f.read().strip().split("\n", 1)[0]) or None
    except Exception:
        pass

    return {"last_commit_sha": sha, "last_commit_message": message}


async def _collect_errors_last_hour() -> Optional[int]:
    """
    Count errors in the last 60 minutes.

    Primary: rows in `errors_log` within the last hour (if the table exists).
    Fallback: rows in `institutional_audit` with compliance_flags containing
    an ERROR marker OR risk_score >= 70 in the last hour.
    """
    if _pool is None:
        return None
    try:
        async with _pool.acquire() as conn:
            cutoff = datetime.utcnow() - timedelta(hours=1)

            # Primary source
            try:
                has_errs = await conn.fetchval(
                    "SELECT EXISTS (SELECT 1 FROM information_schema.tables "
                    "WHERE table_schema='public' AND table_name='errors_log')"
                )
                if has_errs:
                    val = await conn.fetchval(
                        "SELECT COUNT(*) FROM errors_log WHERE created_at >= $1",
                        cutoff,
                    )
                    return int(val or 0)
            except Exception:
                pass

            # Fallback: institutional_audit
            try:
                has_audit = await conn.fetchval(
                    "SELECT EXISTS (SELECT 1 FROM information_schema.tables "
                    "WHERE table_schema='public' AND table_name='institutional_audit')"
                )
                if has_audit:
                    val = await conn.fetchval(
                        """
                        SELECT COUNT(*)
                        FROM institutional_audit
                        WHERE timestamp >= $1
                          AND (
                               (risk_score IS NOT NULL AND risk_score >= 70)
                               OR 'ERROR' = ANY(compliance_flags)
                               OR 'FAILURE' = ANY(compliance_flags)
                          )
                        """,
                        cutoff,
                    )
                    return int(val or 0)
            except Exception:
                pass

            return None
    except Exception:
        return None


async def _collect_esp32() -> dict:
    """
    ESP32 local control stack status.

    If ESP32_BRIDGE_URL env var is set, GET <url>/status with a 500ms
    timeout and surface the result. Otherwise return a disabled stub.
    Also enriches with the most recent `devices` row of type esp32
    (device_id, last_seen, last_ip) if available.
    """
    bridge_url = os.getenv("ESP32_BRIDGE_URL", "").strip()
    out: dict = {
        "configured": bool(bridge_url),
        "last_seen": None,
        "ip": None,
        "reason": None if bridge_url else "local control stack not connected to Railway",
    }

    # Enrich from devices table if available
    if _pool is not None:
        try:
            async with _pool.acquire() as conn:
                has_devices = await conn.fetchval(
                    "SELECT EXISTS (SELECT 1 FROM information_schema.tables "
                    "WHERE table_schema='public' AND table_name='devices')"
                )
                if has_devices:
                    row = await conn.fetchrow(
                        """
                        SELECT device_id, last_ip, last_seen
                        FROM devices
                        WHERE device_type = 'esp32'
                        ORDER BY last_seen DESC NULLS LAST
                        LIMIT 1
                        """
                    )
                    if row is not None:
                        if row["last_seen"] is not None:
                            out["last_seen"] = row["last_seen"].isoformat()
                        out["ip"] = row["last_ip"]
                        out["device_id"] = row["device_id"]
        except Exception:
            pass

    # Try the bridge
    if bridge_url:
        try:
            import aiohttp  # imported lazily - no new dep (main.py already uses it)
            async with aiohttp.ClientSession() as session:
                url = bridge_url.rstrip("/") + "/esp/status"
                async with session.get(
                    url, timeout=aiohttp.ClientTimeout(total=0.5)
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        out["bridge"] = data
                        # Promote common fields if present
                        if isinstance(data, dict):
                            if data.get("ip"):
                                out["ip"] = data["ip"]
                            if data.get("last_seen"):
                                out["last_seen"] = data["last_seen"]
                            out["reason"] = None
                    else:
                        out["reason"] = f"bridge HTTP {resp.status}"
        except asyncio.TimeoutError:
            out["reason"] = "bridge timeout"
        except Exception as e:
            out["reason"] = f"bridge unreachable: {type(e).__name__}"

    return out


# ------------------------------------------------------------------
# Main endpoints
# ------------------------------------------------------------------
@router.get("/audit")
async def system_audit(request: Request):
    """Full JSON audit snapshot. Each field degrades to null on its own failure.

    Overall endpoint wrapped in a 1-second guard so no collector can hang
    the dashboard. Individual collectors also have their own timeouts.
    """
    async def _gather():
        return await asyncio.gather(
            _safe(_collect_api(request), {
                "version": API_VERSION,
                "uptime_seconds": int(time.time() - _PROCESS_START),
                "endpoint_count": None,
            }),
            _safe(_collect_database(), {
                "connected": False, "tables": None, "total_rows": None,
                "latest_backup": "not_configured",
            }),
            _safe(_collect_bots(), {"total": _TOTAL_BOTS, "active": None}),
            _safe(
                _collect_tokens(),
                {sym: {"holders": None, "supply": None} for sym in _TOKENS},
            ),
            _safe(_collect_git(), {"last_commit_sha": None, "last_commit_message": None}),
            _safe(_collect_errors_last_hour(), None),
            _safe(_collect_esp32(), {
                "configured": False, "last_seen": None, "ip": None,
                "reason": "collector error",
            }),
        )

    try:
        results = await asyncio.wait_for(_gather(), timeout=1.0)
        api_data, db_data, bots_data, tokens_data, git_data, errors_data, esp32_data = results
    except asyncio.TimeoutError:
        api_data = {
            "version": API_VERSION,
            "uptime_seconds": int(time.time() - _PROCESS_START),
            "endpoint_count": None,
        }
        db_data = {"connected": False, "tables": None, "total_rows": None,
                   "latest_backup": "not_configured"}
        bots_data = {"total": _TOTAL_BOTS, "active": None}
        tokens_data = {sym: {"holders": None, "supply": None} for sym in _TOKENS}
        git_data = {"last_commit_sha": None, "last_commit_message": None}
        errors_data = None
        esp32_data = {"configured": False, "last_seen": None, "ip": None,
                      "reason": "audit collector timeout"}

    return {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "api": api_data,
        "database": db_data,
        "bots": bots_data,
        "tokens": tokens_data,
        "git": git_data,
        "errors_last_hour": errors_data,
        "esp32": esp32_data,
    }


@router.get("/audit/health-check")
async def audit_health_check():
    """Tiny, fast, no-DB-write health check for Uptime Robot / external monitors."""
    db_ok = False
    if _pool is not None:
        try:
            async with _pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
                db_ok = True
        except Exception:
            db_ok = False
    return {
        "status": "ok" if db_ok else "degraded",
        "db": "connected" if db_ok else "down",
        "version": API_VERSION,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }
