"""SLH public security beacon — sanitized aggregate status, no auth.

Used by /my.html and any other personal/public page that wants to surface a
"is anything broken right now" signal without requiring an admin key.

Returns ONLY non-identifying numeric counts. Never returns:
  - key_name (e.g. ANTHROPIC_API_KEY)
  - display_name (e.g. "Anthropic Claude API")
  - category (could leak which providers we use)
  - rotation_url (could leak vendor relationships)
  - last_health_result per-secret (could leak which key is broken)
  - any per-secret detail

The shape mirrors the shape /my.html will render, so the page can stay
purely declarative.
"""
from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Request

log = logging.getLogger("slh.public_security")

router = APIRouter(prefix="/api/public/security", tags=["public", "security"])


def _pool(request: Request):
    pool = getattr(request.app.state, "db_pool", None)
    if pool is None:
        raise HTTPException(503, "DB pool unavailable")
    return pool


@router.get("/summary")
async def summary(request: Request):
    """Sanitized aggregate of secrets_catalog + secret_alerts.

    No auth required. Response shape (all integers / ISO8601):
        total                — count of all tracked secrets
        configured           — count where status='configured'
        missing_or_default   — count where status in ('missing','default')
        overdue              — count where last_rotated_at + cadence < NOW()
        last_sweep_at        — ISO8601 of last sweep heartbeat (or null)
        alerts_24h           — count of alerts fired in last 24h
        any_broken           — bool — true if missing_or_default > 0
        any_overdue          — bool — true if overdue > 0
        ok                   — bool — true if no broken AND no overdue

    On DB error / table missing: returns 200 with all zeros and `unavailable: true`.
    Frontend should render that gracefully.
    """
    try:
        pool = _pool(request)
    except HTTPException:
        return _empty(unavailable=True, reason="db pool unavailable")

    try:
        async with pool.acquire() as conn:
            # Catalog stats — defensive: if table doesn't exist yet, all zero
            try:
                stats = await conn.fetchrow(
                    """
                    SELECT
                        COUNT(*)                                                                  AS total,
                        COUNT(*) FILTER (WHERE status = 'configured')                             AS configured,
                        COUNT(*) FILTER (WHERE status IN ('missing','default'))                   AS missing_or_default,
                        COUNT(*) FILTER (
                            WHERE last_rotated_at IS NOT NULL
                              AND last_rotated_at < (NOW() - (rotation_cadence_days || ' days')::interval)
                        )                                                                         AS overdue
                    FROM secrets_catalog
                    """
                )
            except Exception as e:
                log.info("secrets_catalog not ready: %s", e)
                return _empty(unavailable=True, reason="catalog not initialized")

            # Last sweep heartbeat — best effort from event_log
            last_sweep = None
            try:
                last_sweep = await conn.fetchval(
                    """
                    SELECT MAX(created_at)
                      FROM event_log
                     WHERE event_type = 'secret.sweep.completed'
                    """
                )
            except Exception:
                pass

            # Alert volume in last 24h
            alerts_24h = 0
            try:
                alerts_24h = int(await conn.fetchval(
                    "SELECT COUNT(*) FROM secret_alerts WHERE fired_at >= NOW() - INTERVAL '24 hours'"
                ) or 0)
            except Exception:
                pass

        total = int(stats["total"] or 0)
        configured = int(stats["configured"] or 0)
        missing_or_default = int(stats["missing_or_default"] or 0)
        overdue = int(stats["overdue"] or 0)

        return {
            "total": total,
            "configured": configured,
            "missing_or_default": missing_or_default,
            "overdue": overdue,
            "alerts_24h": alerts_24h,
            "last_sweep_at": last_sweep.isoformat() if last_sweep else None,
            "any_broken": missing_or_default > 0,
            "any_overdue": overdue > 0,
            "ok": missing_or_default == 0 and overdue == 0,
            "unavailable": False,
        }
    except Exception as e:
        log.warning("public security summary failed: %s", e)
        return _empty(unavailable=True, reason=f"{type(e).__name__}")


def _empty(unavailable: bool, reason: Optional[str] = None) -> dict:
    return {
        "total": 0,
        "configured": 0,
        "missing_or_default": 0,
        "overdue": 0,
        "alerts_24h": 0,
        "last_sweep_at": None,
        "any_broken": False,
        "any_overdue": False,
        "ok": True,  # graceful: no data → render as ok
        "unavailable": unavailable,
        "reason": reason,
    }
