"""
Admin Key Rotation — DB-backed admin secrets + in-memory cache.

Allows the admin to rotate their X-Admin-Key at runtime without editing
Railway env vars or redeploying. Env keys (`ADMIN_API_KEYS`) continue to
work as a backward-compat fallback — DB keys are additive.

Flow:
  1. Admin logs in with current key (env or DB — both accepted).
  2. POST /api/admin/rotate-key with current + new key.
  3. New key hashed (SHA-256 + salt) and stored in `admin_secrets`.
  4. All previous DB keys marked inactive.
  5. In-memory cache reloaded — new key valid immediately.

Schema:
  admin_secrets (id, key_hash, salt, label, active, created_at, rotated_at, created_by)

Endpoints (all admin-gated via X-Admin-Key):
  POST  /api/admin/rotate-key      — rotate to new key
  GET   /api/admin/key-status      — last rotation info (no keys exposed)
  POST  /api/admin/reload-keys     — force in-memory reload (debug)
"""
from __future__ import annotations

import hashlib
import logging
import secrets
from datetime import datetime
from typing import Optional, List, Tuple

from pydantic import BaseModel, Field, validator
from fastapi import APIRouter, HTTPException, Header

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin", tags=["admin-rotate"])

# ═══════════════════ Module state ═══════════════════

_pool = None

# In-memory cache of active DB admin keys: list of (salt, key_hash) tuples.
# Loaded at startup (via reload_db_admin_keys) and after every rotation.
_DB_ADMIN_KEYS: List[Tuple[str, str]] = []


def set_pool(pool):
    global _pool
    _pool = pool


# ═══════════════════ Helpers ═══════════════════

def _hash_key(salt: str, key: str) -> str:
    return hashlib.sha256((salt + key).encode("utf-8")).hexdigest()


def check_db_admin_key(candidate: str) -> bool:
    """In-memory check. Safe to call from sync _require_admin. Returns True if match."""
    if not candidate:
        return False
    for salt, expected_hash in _DB_ADMIN_KEYS:
        h = _hash_key(salt, candidate)
        if secrets.compare_digest(h, expected_hash):
            return True
    return False


async def reload_db_admin_keys() -> int:
    """Refresh _DB_ADMIN_KEYS from DB. Returns count loaded."""
    global _DB_ADMIN_KEYS
    if _pool is None:
        logger.warning("[admin-rotate] reload skipped — pool not set")
        return 0
    try:
        async with _pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT salt, key_hash FROM admin_secrets WHERE active = TRUE"
            )
            _DB_ADMIN_KEYS = [(r["salt"], r["key_hash"]) for r in rows]
            logger.info(f"[admin-rotate] loaded {len(_DB_ADMIN_KEYS)} active DB admin keys")
            return len(_DB_ADMIN_KEYS)
    except Exception as e:  # noqa: BLE001
        logger.error(f"[admin-rotate] reload failed: {e!r}")
        return 0


async def init_admin_secrets_table():
    """Create admin_secrets table. Safe to call repeatedly."""
    if _pool is None:
        logger.warning("[admin-rotate] init skipped — pool not set")
        return
    try:
        async with _pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS admin_secrets (
                    id SERIAL PRIMARY KEY,
                    key_hash TEXT NOT NULL,
                    salt TEXT NOT NULL,
                    label TEXT DEFAULT 'admin',
                    active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT NOW(),
                    rotated_at TIMESTAMP,
                    created_by TEXT
                )
            """)
            await conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_admin_secrets_active ON admin_secrets(active) WHERE active = TRUE"
            )
        logger.info("[admin-rotate] table ready")
        await reload_db_admin_keys()
    except Exception as e:  # noqa: BLE001
        logger.error(f"[admin-rotate] init failed: {e!r}")


# ═══════════════════ Models ═══════════════════

class RotateKeyRequest(BaseModel):
    new_key: str = Field(..., min_length=12, max_length=128)
    label: Optional[str] = Field(None, max_length=80)

    @validator("new_key")
    def _validate_strength(cls, v):
        v = v.strip()
        if len(v) < 12:
            raise ValueError("new_key must be at least 12 chars")
        # Require minimum variety — at least 2 of: lower, upper, digit, symbol
        has_lower = any(c.islower() for c in v)
        has_upper = any(c.isupper() for c in v)
        has_digit = any(c.isdigit() for c in v)
        has_symbol = any(not c.isalnum() for c in v)
        variety = sum([has_lower, has_upper, has_digit, has_symbol])
        if variety < 2:
            raise ValueError("new_key must mix at least 2 character classes (lower/upper/digit/symbol)")
        # Reject common weak patterns
        lowered = v.lower()
        banned = ("password", "123456", "qwerty", "admin1234", "slh2026admin")
        if any(b in lowered for b in banned):
            raise ValueError("new_key contains a banned substring")
        return v


# ═══════════════════ Endpoints ═══════════════════
# Note: _require_admin is imported lazily from main.py to avoid circular import.

def _lazy_require_admin():
    from main import _require_admin  # type: ignore
    return _require_admin


@router.post("/rotate-key")
async def rotate_admin_key(
    payload: RotateKeyRequest,
    authorization: Optional[str] = Header(None),
    x_admin_key: Optional[str] = Header(None),
):
    """Rotate the admin key. Current key authenticates, new key replaces it.

    Env keys continue to work — this only rotates DB keys. To fully retire
    env keys, remove from Railway `ADMIN_API_KEYS` after rotation.
    """
    _lazy_require_admin()(authorization, x_admin_key)

    if _pool is None:
        raise HTTPException(503, "database pool not ready")

    # Reject rotating to the same key that authenticated
    if x_admin_key and secrets.compare_digest(x_admin_key, payload.new_key):
        raise HTTPException(400, "new_key must differ from current key")

    salt = secrets.token_hex(16)
    new_hash = _hash_key(salt, payload.new_key)
    label = (payload.label or "rotated").strip()[:80]

    async with _pool.acquire() as conn:
        async with conn.transaction():
            # Deactivate all previous DB keys
            await conn.execute(
                "UPDATE admin_secrets SET active = FALSE, rotated_at = NOW() WHERE active = TRUE"
            )
            # Insert new
            row = await conn.fetchrow(
                """
                INSERT INTO admin_secrets (key_hash, salt, label, active, created_by)
                VALUES ($1, $2, $3, TRUE, $4)
                RETURNING id, created_at
                """,
                new_hash, salt, label, "admin_ui",
            )

    # Refresh in-memory cache — new key works on very next request
    loaded = await reload_db_admin_keys()

    return {
        "ok": True,
        "id": row["id"],
        "label": label,
        "created_at": row["created_at"].isoformat() if row["created_at"] else None,
        "active_db_keys": loaded,
        "message": "סיסמת אדמין עודכנה. השתמש בסיסמה החדשה בבקשות הבאות.",
    }


@router.get("/key-status")
async def admin_key_status(
    authorization: Optional[str] = Header(None),
    x_admin_key: Optional[str] = Header(None),
):
    """Return rotation metadata (NO actual keys exposed)."""
    _lazy_require_admin()(authorization, x_admin_key)

    if _pool is None:
        raise HTTPException(503, "database pool not ready")

    async with _pool.acquire() as conn:
        active = await conn.fetchrow(
            """
            SELECT id, label, created_at, created_by
            FROM admin_secrets
            WHERE active = TRUE
            ORDER BY created_at DESC
            LIMIT 1
            """
        )
        total_ever = await conn.fetchval(
            "SELECT COUNT(*) FROM admin_secrets"
        ) or 0
        last_rotated_at = await conn.fetchval(
            "SELECT MAX(rotated_at) FROM admin_secrets WHERE rotated_at IS NOT NULL"
        )

    return {
        "has_active_db_key": active is not None,
        "active_key": {
            "id": active["id"],
            "label": active["label"],
            "created_at": active["created_at"].isoformat() if active["created_at"] else None,
            "created_by": active["created_by"],
        } if active else None,
        "total_keys_ever": int(total_ever),
        "last_rotation_at": last_rotated_at.isoformat() if last_rotated_at else None,
        "env_keys_available": True,  # Env fallback always on
        "cached_in_memory": len(_DB_ADMIN_KEYS),
    }


@router.post("/reload-keys")
async def admin_reload_keys(
    authorization: Optional[str] = Header(None),
    x_admin_key: Optional[str] = Header(None),
):
    """Force in-memory reload of DB admin keys. Useful after manual DB edits."""
    _lazy_require_admin()(authorization, x_admin_key)
    loaded = await reload_db_admin_keys()
    return {"ok": True, "active_db_keys": loaded}
