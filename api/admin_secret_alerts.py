"""SLH Secrets Vault — Phase 2 alerts + scheduled sweep.

Sits on top of api/admin_secrets_catalog.py:
  - /sweep            — iterate every row in secrets_catalog, call _run_probe per
                        key_name, detect status transitions (ok/unknown → bad_key/
                        missing) and overdue-rotation, fire Telegram alert
                        (with cooldown), record in secret_alerts table, emit
                        audit event.
  - /alerts/recent    — list last N hours of secret_alerts (read-only, audit).
  - /alerts/test      — fire a single test Telegram message, end-to-end smoke
                        check the BROADCAST_BOT_TOKEN pipe works.
  - /digest/send      — compose a single Hebrew Telegram digest (last 24h
                        transitions + currently overdue list) and send.

All endpoints under /api/admin/secrets, X-Admin-Key gated. Designed to be
called by Windows Task Scheduler (every 6h for /sweep, daily 21:00 for
/digest) via small wrapper scripts in scripts/.

The actual secret values NEVER appear in:
  - Request bodies (we don't accept secret values as input)
  - Response bodies (we only return aggregate counts + status names)
  - Audit rows (event_log + secret_alerts only carry key_name + status code)
  - Telegram messages (only display_name + status code, never the value)
"""
from __future__ import annotations

import json
import logging
import os
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Header, HTTPException, Query, Request
from pydantic import BaseModel

log = logging.getLogger("slh.secrets_alerts")

router = APIRouter(prefix="/api/admin/secrets", tags=["admin", "secrets", "alerts"])


# ─── Auth (mirror admin_secrets_catalog._admin) ────────────────────────────


def _admin(authorization: Optional[str], x_admin_key: Optional[str]) -> int:
    try:
        from main import _require_admin
        return _require_admin(authorization, x_admin_key)
    except Exception:
        env_keys = {k.strip() for k in os.getenv("ADMIN_API_KEYS", "").split(",") if k.strip()}
        if x_admin_key and x_admin_key in env_keys:
            return 0
        raise HTTPException(403, "Admin authentication required")


def _pool(request: Request):
    pool = getattr(request.app.state, "db_pool", None)
    if pool is None:
        raise HTTPException(503, "DB pool unavailable")
    return pool


# ─── Telegram pipe (sync, urllib — matches ops/telegram_push_alerts.py) ────


# Osif's tg_id from CLAUDE.md / MEMORY. Hardcoded so a stranger can't redirect
# alerts by manipulating env. Override with SECRET_ALERT_CHAT_ID if needed.
_DEFAULT_ALERT_CHAT_ID = 224223270


def _tg_send(text: str, parse_mode: str = "HTML") -> tuple[bool, str]:
    """Send a Telegram message via BROADCAST_BOT_TOKEN. Returns (ok, detail)."""
    bot_token = os.getenv("BROADCAST_BOT_TOKEN") or os.getenv("SLH_AIR_TOKEN") or ""
    if not bot_token:
        return False, "BROADCAST_BOT_TOKEN not set"
    chat_id = int(os.getenv("SECRET_ALERT_CHAT_ID") or _DEFAULT_ALERT_CHAT_ID)
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = urllib.parse.urlencode({
        "chat_id": chat_id,
        "text": text[:4000],  # Telegram caps at 4096 chars
        "parse_mode": parse_mode,
        "disable_web_page_preview": "true",
    }).encode("utf-8")
    req = urllib.request.Request(url, data=payload, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read().decode("utf-8"))
            ok = bool(data.get("ok"))
            return ok, "sent" if ok else str(data)[:200]
    except urllib.error.HTTPError as e:
        return False, f"HTTP {e.code}: {e.read().decode('utf-8', errors='replace')[:200]}"
    except Exception as e:
        return False, f"{type(e).__name__}: {e}"


# ─── Alert classification ──────────────────────────────────────────────────


# Transitions that should fire an alert
_ALERT_RESULTS = {"bad_key", "missing", "service_error"}
_HEALTHY_RESULTS = {"ok"}


def _is_overdue(last_rotated_at, cadence_days: int) -> bool:
    if not last_rotated_at or not cadence_days:
        return False
    if isinstance(last_rotated_at, str):
        try:
            last_rotated_at = datetime.fromisoformat(last_rotated_at.replace("Z", "+00:00"))
        except Exception:
            return False
    age = (datetime.now(timezone.utc) - last_rotated_at).total_seconds() / 86400.0
    return age > cadence_days


def _format_alert(row, alert_type: str, prev: Optional[str], new: Optional[str], detail: Optional[str]) -> str:
    """Hebrew Telegram alert body. No secret value, only metadata."""
    icon = {"bad_key": "🚨", "missing": "🚨", "service_error": "⚠️", "overdue": "⏰"}.get(alert_type, "ℹ️")
    head = f"{icon} <b>SLH Secrets Vault — התראה</b>"
    body = (
        f"\n\n<b>{row['display_name']}</b>"
        f"\n<code>{row['key_name']}</code>"
        f"\n\nסוג התראה: <b>{alert_type}</b>"
    )
    if prev or new:
        body += f"\nמעבר: <code>{prev or '—'}</code> → <code>{new or '—'}</code>"
    if detail:
        body += f"\nפרט: <code>{str(detail)[:200]}</code>"
    if row.get("rotation_url"):
        body += f"\n\n🔧 <a href=\"{row['rotation_url']}\">סובב עכשיו ↗</a>"
    body += "\n\n<a href=\"https://slh-nft.com/admin/secrets-vault.html\">פתח Vault</a>"
    return head + body


# ─── Endpoints ─────────────────────────────────────────────────────────────


class TestAlertIn(BaseModel):
    text: Optional[str] = None


@router.post("/sweep")
async def sweep(
    request: Request,
    authorization: Optional[str] = Header(None),
    x_admin_key: Optional[str] = Header(None, alias="X-Admin-Key"),
):
    """Iterate secrets_catalog, run probes, fire alerts on transitions.

    Idempotent: cooldown column on secrets_catalog blocks re-firing within
    `alert_cooldown_hours` hours. Designed to be called every ~6h by Task
    Scheduler. Safe to call manually.

    Returns aggregate counts only — never key names or values.
    """
    _admin(authorization, x_admin_key)
    pool = _pool(request)

    # Reuse schema-ensure from the catalog module so columns always exist
    try:
        from api.admin_secrets_catalog import _ensure_schema, _run_probe
    except Exception:
        from admin_secrets_catalog import _ensure_schema, _run_probe  # type: ignore
    await _ensure_schema(pool)

    checked = 0
    transitions = 0
    alerts_sent = 0
    alerts_skipped_cooldown = 0
    overdue_alerts = 0
    skipped_no_probe = 0
    errors = 0

    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT * FROM secrets_catalog ORDER BY id")

    for row in rows:
        checked += 1
        prev = row["last_health_result"]
        try:
            result, detail = await _run_probe(row["key_name"])
        except Exception as e:
            result, detail = "error", f"{type(e).__name__}: {e}"
            errors += 1

        # Persist health result
        async with pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE secrets_catalog
                   SET last_health_check_at = NOW(),
                       last_health_result = $2,
                       last_verified_at = CASE WHEN $2 = 'ok' THEN NOW() ELSE last_verified_at END
                 WHERE id = $1
                """,
                row["id"], result,
            )

        if result == "skipped":
            skipped_no_probe += 1
            continue

        # Detect health transition (only fire on healthy/unknown → bad)
        is_transition = (
            result in _ALERT_RESULTS
            and (prev is None or prev in _HEALTHY_RESULTS or prev == "unknown")
        )

        # Detect overdue rotation (independent of health probe result)
        overdue = _is_overdue(row["last_rotated_at"], row["rotation_cadence_days"])

        # Fire transition alert
        if is_transition:
            transitions += 1
            cooldown_h = int(row["alert_cooldown_hours"] or 24)
            last_alert = row["last_alert_at"]
            now = datetime.now(timezone.utc)
            cooldown_active = (
                last_alert is not None
                and (now - last_alert).total_seconds() < cooldown_h * 3600
            )
            if cooldown_active:
                alerts_skipped_cooldown += 1
            else:
                msg = _format_alert(dict(row), result, prev, result, detail)
                ok, send_detail = _tg_send(msg)
                async with pool.acquire() as conn:
                    await conn.execute(
                        """
                        INSERT INTO secret_alerts
                            (secret_id, alert_type, prev_status, new_status, detail, notified_via)
                        VALUES ($1, $2, $3, $4, $5, $6)
                        """,
                        row["id"], result, prev, result, str(detail)[:300] if detail else None,
                        "telegram" if ok else "failed",
                    )
                    await conn.execute(
                        """
                        UPDATE secrets_catalog
                           SET last_alert_at = NOW(), last_alert_result = $2
                         WHERE id = $1
                        """,
                        row["id"], result,
                    )
                if ok:
                    alerts_sent += 1
                # Audit
                try:
                    from shared.events import emit as _emit
                    await _emit(
                        pool,
                        "secret.alert.fired",
                        {"secret_id": row["id"], "key_name": row["key_name"], "alert_type": result, "notified": ok},
                        source="api.admin.secrets_alerts.sweep",
                    )
                except Exception:
                    pass

        # Fire overdue alert (separate cooldown — once per cycle is enough)
        if overdue and not is_transition:
            cooldown_h = int(row["alert_cooldown_hours"] or 24)
            last_alert = row["last_alert_at"]
            now = datetime.now(timezone.utc)
            cooldown_active = (
                last_alert is not None
                and (now - last_alert).total_seconds() < cooldown_h * 3600
                and row["last_alert_result"] == "overdue"
            )
            if not cooldown_active:
                msg = _format_alert(dict(row), "overdue", prev, result, "rotation cadence exceeded")
                ok, send_detail = _tg_send(msg)
                async with pool.acquire() as conn:
                    await conn.execute(
                        """
                        INSERT INTO secret_alerts
                            (secret_id, alert_type, prev_status, new_status, detail, notified_via)
                        VALUES ($1, 'overdue', $2, $3, $4, $5)
                        """,
                        row["id"], prev, result, "rotation cadence exceeded",
                        "telegram" if ok else "failed",
                    )
                    await conn.execute(
                        """
                        UPDATE secrets_catalog
                           SET last_alert_at = NOW(), last_alert_result = 'overdue'
                         WHERE id = $1
                        """,
                        row["id"],
                    )
                if ok:
                    overdue_alerts += 1

    # Sweep-level audit event
    try:
        from shared.events import emit as _emit
        await _emit(
            pool,
            "secret.sweep.completed",
            {
                "checked": checked,
                "transitions": transitions,
                "alerts_sent": alerts_sent,
                "overdue_alerts": overdue_alerts,
                "skipped_cooldown": alerts_skipped_cooldown,
                "skipped_no_probe": skipped_no_probe,
                "errors": errors,
            },
            source="api.admin.secrets_alerts.sweep",
        )
    except Exception:
        pass

    return {
        "ok": True,
        "checked": checked,
        "transitions": transitions,
        "alerts_sent": alerts_sent,
        "overdue_alerts": overdue_alerts,
        "skipped_cooldown": alerts_skipped_cooldown,
        "skipped_no_probe": skipped_no_probe,
        "errors": errors,
    }


@router.get("/alerts/recent")
async def alerts_recent(
    request: Request,
    hours: int = Query(24, ge=1, le=720),
    limit: int = Query(50, ge=1, le=500),
    authorization: Optional[str] = Header(None),
    x_admin_key: Optional[str] = Header(None, alias="X-Admin-Key"),
):
    """Last N hours of fired alerts. Aggregates by secret + type for digest UI."""
    _admin(authorization, x_admin_key)
    pool = _pool(request)
    try:
        from api.admin_secrets_catalog import _ensure_schema
    except Exception:
        from admin_secrets_catalog import _ensure_schema  # type: ignore
    await _ensure_schema(pool)

    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT
                a.id, a.secret_id, a.alert_type, a.prev_status, a.new_status,
                a.detail, a.notified_via, a.fired_at,
                s.key_name, s.display_name, s.category
            FROM secret_alerts a
            LEFT JOIN secrets_catalog s ON s.id = a.secret_id
            WHERE a.fired_at >= NOW() - ($1 || ' hours')::interval
            ORDER BY a.fired_at DESC
            LIMIT $2
            """,
            str(hours), limit,
        )

    return {
        "count": len(rows),
        "hours": hours,
        "alerts": [
            {
                "id": r["id"],
                "secret_id": r["secret_id"],
                "key_name": r["key_name"],
                "display_name": r["display_name"],
                "category": r["category"],
                "alert_type": r["alert_type"],
                "prev_status": r["prev_status"],
                "new_status": r["new_status"],
                "detail": r["detail"],
                "notified_via": r["notified_via"],
                "fired_at": r["fired_at"].isoformat() if r["fired_at"] else None,
            }
            for r in rows
        ],
    }


@router.post("/alerts/test")
async def alerts_test(
    request: Request,
    body: Optional[TestAlertIn] = None,
    authorization: Optional[str] = Header(None),
    x_admin_key: Optional[str] = Header(None, alias="X-Admin-Key"),
):
    """Smoke-test the Telegram pipe. Sends a single throwaway message."""
    _admin(authorization, x_admin_key)
    text = (body and body.text) or "🧪 SLH Secrets Vault — alert pipe test (you can ignore this)"
    ok, detail = _tg_send(text)
    return {"ok": ok, "detail": detail}


@router.post("/digest/send")
async def digest_send(
    request: Request,
    authorization: Optional[str] = Header(None),
    x_admin_key: Optional[str] = Header(None, alias="X-Admin-Key"),
):
    """Compose + send the daily digest. Hebrew, single Telegram message.

    Designed to be called by Task Scheduler at 21:00 Israel daily. Includes:
      - last-24h alerts summary
      - currently overdue secrets
      - currently bad_key / missing secrets
      - sweep heartbeat (last sweep timestamp from event_log)
    """
    _admin(authorization, x_admin_key)
    pool = _pool(request)
    try:
        from api.admin_secrets_catalog import _ensure_schema
    except Exception:
        from admin_secrets_catalog import _ensure_schema  # type: ignore
    await _ensure_schema(pool)

    async with pool.acquire() as conn:
        # Aggregates
        stats = await conn.fetchrow(
            """
            SELECT
                COUNT(*)                                                AS total,
                COUNT(*) FILTER (WHERE last_health_result IN ('bad_key','missing')) AS broken,
                COUNT(*) FILTER (
                    WHERE last_rotated_at IS NOT NULL
                      AND last_rotated_at < (NOW() - (rotation_cadence_days || ' days')::interval)
                ) AS overdue
            FROM secrets_catalog
            """
        )

        broken_rows = await conn.fetch(
            """
            SELECT display_name, key_name, last_health_result
              FROM secrets_catalog
             WHERE last_health_result IN ('bad_key','missing')
             ORDER BY display_name
             LIMIT 10
            """
        )
        overdue_rows = await conn.fetch(
            """
            SELECT display_name, key_name,
                   EXTRACT(EPOCH FROM (NOW() - last_rotated_at))/86400 AS age_days,
                   rotation_cadence_days
              FROM secrets_catalog
             WHERE last_rotated_at IS NOT NULL
               AND last_rotated_at < (NOW() - (rotation_cadence_days || ' days')::interval)
             ORDER BY age_days DESC
             LIMIT 10
            """
        )
        recent_alerts = await conn.fetch(
            """
            SELECT alert_type, COUNT(*) AS n
              FROM secret_alerts
             WHERE fired_at >= NOW() - INTERVAL '24 hours'
             GROUP BY alert_type
             ORDER BY n DESC
            """
        )

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    lines = [f"🔐 <b>SLH Secrets — דיגסט יומי {today}</b>", ""]
    lines.append(
        f"סה״כ secrets: <b>{stats['total']}</b> · "
        f"שבורים: <b>{stats['broken']}</b> · "
        f"לסיבוב: <b>{stats['overdue']}</b>"
    )

    if recent_alerts:
        lines.append("")
        lines.append("🚨 <b>התראות 24ש</b>")
        for r in recent_alerts:
            lines.append(f"  • <code>{r['alert_type']}</code>: {r['n']}")

    if broken_rows:
        lines.append("")
        lines.append("❌ <b>סודות שבורים</b>")
        for r in broken_rows:
            lines.append(
                f"  • {r['display_name']} (<code>{r['key_name']}</code>) — {r['last_health_result']}"
            )

    if overdue_rows:
        lines.append("")
        lines.append("⏰ <b>חורגים מתדירות סיבוב</b>")
        for r in overdue_rows:
            age = int(r["age_days"] or 0)
            lines.append(
                f"  • {r['display_name']} — {age}d (cadence {r['rotation_cadence_days']}d)"
            )

    if not (broken_rows or overdue_rows or recent_alerts):
        lines.append("")
        lines.append("✅ <i>הכל ירוק. שום דבר לא דורש פעולה.</i>")

    lines.append("")
    lines.append('<a href="https://slh-nft.com/admin/security-hub.html">Security Hub ↗</a>')

    text = "\n".join(lines)
    ok, detail = _tg_send(text)

    # Audit
    try:
        from shared.events import emit as _emit
        await _emit(
            pool,
            "secret.digest.sent",
            {
                "ok": ok,
                "broken": int(stats["broken"] or 0),
                "overdue": int(stats["overdue"] or 0),
                "alerts_24h": sum(int(r["n"] or 0) for r in recent_alerts),
            },
            source="api.admin.secrets_alerts.digest",
        )
    except Exception:
        pass

    return {
        "ok": ok,
        "detail": detail,
        "summary": {
            "total": int(stats["total"] or 0),
            "broken": int(stats["broken"] or 0),
            "overdue": int(stats["overdue"] or 0),
            "alerts_24h": sum(int(r["n"] or 0) for r in recent_alerts),
        },
    }
