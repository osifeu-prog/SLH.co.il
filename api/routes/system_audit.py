"""
System Audit — live monitoring infrastructure for the SLH Spark ecosystem.

Single aggregator endpoint that powers /system-audit.html. Every field is
computed defensively: if one query fails, that field comes back `null` —
the whole response never 500s because a single sub-query broke.

Endpoints:
  GET /api/system/audit               — full JSON audit snapshot
  GET /api/system/audit/health-check  — tiny quick health for Uptime Robot
"""
from __future__ import annotations

import os
import time
import subprocess
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Request


router = APIRouter(prefix="/api/system", tags=["System Audit"])

# Global connection pool (set by main.py, mirror of other routers' pattern)
_pool = None

# Process start time — used for uptime. Captured at module import.
_PROCESS_START = time.time()

API_VERSION = "1.1.0"

# Tokens we track. Each entry: (symbol, holders_table, supply_table_or_none, supply_col)
# For internal tokens, holders = distinct user_ids in token_balances. Supply = SUM(balance).
# For on-chain tokens (SLH), "supply" is a fixed cap reported elsewhere; we return null here.
_TOKENS = ["SLH", "ZVK", "MNH", "REP", "ZUZ", "AIC"]


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
        return {"connected": False, "tables": None, "total_rows": None, "latest_backup": None}

    connected = False
    tables = None
    total_rows = None
    latest_backup = None

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

            # Total rows across all public tables — uses reltuples statistic (cheap, approximate)
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

            # Latest backup — only if a backups table exists
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
            except Exception:
                latest_backup = None
    except Exception:
        pass

    return {
        "connected": connected,
        "tables": tables,
        "total_rows": total_rows,
        "latest_backup": latest_backup,
    }


async def _collect_bots() -> dict:
    """Total is fixed (25 from the ecosystem spec). Active is queried if a bots table exists."""
    active = None
    if _pool is not None:
        try:
            async with _pool.acquire() as conn:
                has_bots = await conn.fetchval(
                    "SELECT EXISTS (SELECT 1 FROM information_schema.tables "
                    "WHERE table_schema='public' AND table_name='bots')"
                )
                if has_bots:
                    # Try common "active" column names without blowing up if schema differs
                    for col_expr in ("is_active=TRUE", "active=TRUE", "status='active'"):
                        try:
                            active = await conn.fetchval(
                                f"SELECT COUNT(*) FROM bots WHERE {col_expr}"
                            )
                            break
                        except Exception:
                            continue
                    if active is None:
                        # Fall back to total row count — better than null
                        try:
                            active = await conn.fetchval("SELECT COUNT(*) FROM bots")
                        except Exception:
                            active = None
        except Exception:
            active = None
    return {"total": 25, "active": active}


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
    """Shell out to git — swallow any failure (Railway build may not ship .git)."""
    sha = None
    message = None
    try:
        repo_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        sha_raw = subprocess.run(
            ["git", "-C", repo_dir, "rev-parse", "HEAD"],
            capture_output=True, text=True, timeout=3,
        )
        if sha_raw.returncode == 0:
            sha = sha_raw.stdout.strip() or None
        msg_raw = subprocess.run(
            ["git", "-C", repo_dir, "log", "-1", "--pretty=%s"],
            capture_output=True, text=True, timeout=3,
        )
        if msg_raw.returncode == 0:
            message = msg_raw.stdout.strip() or None
    except Exception:
        pass
    return {"last_commit_sha": sha, "last_commit_message": message}


async def _collect_errors_last_hour() -> Optional[int]:
    """Count rows in an `errors_log` table (if one exists) within the last 60 minutes."""
    if _pool is None:
        return None
    try:
        async with _pool.acquire() as conn:
            exists = await conn.fetchval(
                "SELECT EXISTS (SELECT 1 FROM information_schema.tables "
                "WHERE table_schema='public' AND table_name='errors_log')"
            )
            if not exists:
                return None
            cutoff = datetime.utcnow() - timedelta(hours=1)
            return int(await conn.fetchval(
                "SELECT COUNT(*) FROM errors_log WHERE created_at >= $1",
                cutoff,
            ) or 0)
    except Exception:
        return None


# ------------------------------------------------------------------
# Main endpoints
# ------------------------------------------------------------------
@router.get("/audit")
async def system_audit(request: Request):
    """Full JSON audit snapshot. Each field degrades to null on its own failure."""
    api_data = await _safe(_collect_api(request), {
        "version": API_VERSION,
        "uptime_seconds": int(time.time() - _PROCESS_START),
        "endpoint_count": None,
    })
    db_data = await _safe(_collect_database(), {
        "connected": False, "tables": None, "total_rows": None, "latest_backup": None,
    })
    bots_data = await _safe(_collect_bots(), {"total": 25, "active": None})
    tokens_data = await _safe(
        _collect_tokens(),
        {sym: {"holders": None, "supply": None} for sym in _TOKENS},
    )
    git_data = await _safe(_collect_git(), {"last_commit_sha": None, "last_commit_message": None})
    errors_data = await _safe(_collect_errors_last_hour(), None)

    return {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "api": api_data,
        "database": db_data,
        "bots": bots_data,
        "tokens": tokens_data,
        "git": git_data,
        "errors_last_hour": errors_data,
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
