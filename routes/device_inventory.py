"""
Device Inventory — catalog of all SLH ESP32 devices (manufacturing → sale → activation).

Distinct from `/api/admin/devices/list` which shows ONLY devices that have
already called `/api/device/register`. This module tracks the full lifecycle:
  in_stock → reserved → sold → shipped → active → returned/dead

Table: device_inventory (created idempotently).
Auth: X-Admin-Key (admin-only, no public access).

Endpoints:
  POST   /api/admin/devices/inventory          — add new device(s) to catalog
  GET    /api/admin/devices/inventory          — list with filters (status, buyer)
  PATCH  /api/admin/devices/inventory/{id}     — update status / buyer / notes
  GET    /api/admin/devices/inventory/stats    — counts by status
"""
from __future__ import annotations

import os
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Header, HTTPException, Query
from pydantic import BaseModel

router = APIRouter(prefix="/api/admin/devices/inventory", tags=["device-inventory"])

_pool = None


def set_pool(pool):
    global _pool
    _pool = pool


# ── auth ────────────────────────────────────────────────────────────
_ADMIN_KEYS = {
    k.strip() for k in os.getenv("ADMIN_API_KEYS", "").split(",") if k.strip()
}


def _require_admin_key(x_admin_key: Optional[str]) -> None:
    if not x_admin_key or x_admin_key not in _ADMIN_KEYS:
        raise HTTPException(403, "Admin key required (X-Admin-Key header)")


VALID_STATUSES = {"in_stock", "reserved", "sold", "shipped", "active", "returned", "dead"}


# ── table init ──────────────────────────────────────────────────────
async def _ensure_table(conn) -> None:
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS device_inventory (
            id              BIGSERIAL PRIMARY KEY,
            mac_address     TEXT      NOT NULL UNIQUE,
            device_id       TEXT,
            status          TEXT      NOT NULL DEFAULT 'in_stock',
            buyer_user_id   BIGINT,
            buyer_name      TEXT,
            buyer_phone     TEXT,
            buyer_email     TEXT,
            sale_price_ils  NUMERIC(10,2),
            ordered_at      TIMESTAMP,
            sold_at          TIMESTAMP,
            shipped_at       TIMESTAMP,
            activated_at     TIMESTAMP,
            fw_version       TEXT,
            hardware_rev     TEXT,
            notes            TEXT,
            created_at       TIMESTAMP NOT NULL DEFAULT NOW(),
            updated_at       TIMESTAMP NOT NULL DEFAULT NOW()
        )
    """)
    await conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_device_inv_status ON device_inventory(status)"
    )
    await conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_device_inv_buyer ON device_inventory(buyer_user_id) WHERE buyer_user_id IS NOT NULL"
    )
    await conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_device_inv_mac ON device_inventory(mac_address)"
    )


def _serialize(row) -> dict:
    return {
        "id":             row["id"],
        "mac_address":    row["mac_address"],
        "device_id":      row["device_id"],
        "status":         row["status"],
        "buyer_user_id":  row["buyer_user_id"],
        "buyer_name":     row["buyer_name"],
        "buyer_phone":    row["buyer_phone"],
        "buyer_email":    row["buyer_email"],
        "sale_price_ils": float(row["sale_price_ils"]) if row["sale_price_ils"] is not None else None,
        "ordered_at":     row["ordered_at"].isoformat() if row["ordered_at"] else None,
        "sold_at":        row["sold_at"].isoformat() if row["sold_at"] else None,
        "shipped_at":     row["shipped_at"].isoformat() if row["shipped_at"] else None,
        "activated_at":   row["activated_at"].isoformat() if row["activated_at"] else None,
        "fw_version":     row["fw_version"],
        "hardware_rev":   row["hardware_rev"],
        "notes":          row["notes"],
        "created_at":     row["created_at"].isoformat(),
        "updated_at":     row["updated_at"].isoformat(),
    }


# ── models ──────────────────────────────────────────────────────────
class InventoryCreate(BaseModel):
    mac_address: str
    device_id: Optional[str] = None
    status: Optional[str] = "in_stock"
    buyer_user_id: Optional[int] = None
    buyer_name: Optional[str] = None
    buyer_phone: Optional[str] = None
    buyer_email: Optional[str] = None
    sale_price_ils: Optional[float] = None
    ordered_at: Optional[datetime] = None
    fw_version: Optional[str] = None
    hardware_rev: Optional[str] = None
    notes: Optional[str] = None


class InventoryUpdate(BaseModel):
    device_id: Optional[str] = None
    status: Optional[str] = None
    buyer_user_id: Optional[int] = None
    buyer_name: Optional[str] = None
    buyer_phone: Optional[str] = None
    buyer_email: Optional[str] = None
    sale_price_ils: Optional[float] = None
    sold_at: Optional[datetime] = None
    shipped_at: Optional[datetime] = None
    activated_at: Optional[datetime] = None
    fw_version: Optional[str] = None
    hardware_rev: Optional[str] = None
    notes: Optional[str] = None


# ── endpoints ───────────────────────────────────────────────────────
@router.post("")
async def create_inventory(
    req: InventoryCreate,
    x_admin_key: Optional[str] = Header(None),
):
    """Add a new ESP32 device to the catalog."""
    _require_admin_key(x_admin_key)
    if req.status and req.status not in VALID_STATUSES:
        raise HTTPException(400, f"status must be one of {sorted(VALID_STATUSES)}")

    mac_clean = req.mac_address.upper().strip()
    if not mac_clean:
        raise HTTPException(400, "mac_address required")

    async with _pool.acquire() as conn:
        await _ensure_table(conn)
        try:
            row = await conn.fetchrow("""
                INSERT INTO device_inventory
                    (mac_address, device_id, status, buyer_user_id, buyer_name, buyer_phone,
                     buyer_email, sale_price_ils, ordered_at, fw_version, hardware_rev, notes)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
                RETURNING *
            """,
                mac_clean, req.device_id, req.status or "in_stock",
                req.buyer_user_id, req.buyer_name, req.buyer_phone, req.buyer_email,
                req.sale_price_ils, req.ordered_at, req.fw_version, req.hardware_rev, req.notes,
            )
        except Exception as e:
            if "duplicate key" in str(e).lower() or "unique" in str(e).lower():
                raise HTTPException(409, f"MAC {mac_clean} already in inventory")
            raise

    return {"ok": True, "device": _serialize(row)}


@router.get("")
async def list_inventory(
    status: Optional[str] = Query(None),
    buyer_user_id: Optional[int] = Query(None),
    search: Optional[str] = Query(None, description="Match against MAC, device_id, buyer name/phone/email"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    x_admin_key: Optional[str] = Header(None),
):
    """List inventory with filters."""
    _require_admin_key(x_admin_key)

    conds: list[str] = []
    params: list = []

    if status:
        params.append(status)
        conds.append(f"status = ${len(params)}")

    if buyer_user_id:
        params.append(buyer_user_id)
        conds.append(f"buyer_user_id = ${len(params)}")

    if search:
        params.append(f"%{search}%")
        like = f"${len(params)}"
        conds.append(
            f"(mac_address ILIKE {like} OR device_id ILIKE {like} OR "
            f"buyer_name ILIKE {like} OR buyer_phone ILIKE {like} OR buyer_email ILIKE {like})"
        )

    where_sql = (" WHERE " + " AND ".join(conds)) if conds else ""
    filter_params = params.copy()
    params.extend([limit, offset])

    async with _pool.acquire() as conn:
        await _ensure_table(conn)
        rows = await conn.fetch(
            f"SELECT * FROM device_inventory{where_sql} "
            f"ORDER BY created_at DESC "
            f"LIMIT ${len(params) - 1} OFFSET ${len(params)}",
            *params,
        )
        total = await conn.fetchval(
            f"SELECT COUNT(*) FROM device_inventory{where_sql}",
            *filter_params,
        )

    return {
        "devices": [_serialize(r) for r in rows],
        "total":   total,
        "limit":   limit,
        "offset":  offset,
    }


@router.patch("/{device_id}")
async def update_inventory(
    device_id: int,
    req: InventoryUpdate,
    x_admin_key: Optional[str] = Header(None),
):
    """Update fields on an inventory row. Only non-null fields are touched."""
    _require_admin_key(x_admin_key)
    if req.status and req.status not in VALID_STATUSES:
        raise HTTPException(400, f"status must be one of {sorted(VALID_STATUSES)}")

    updates = {k: v for k, v in req.model_dump().items() if v is not None}
    if not updates:
        raise HTTPException(400, "no fields to update")

    set_parts = [f"{col} = ${i+1}" for i, col in enumerate(updates.keys())]
    set_parts.append("updated_at = NOW()")
    set_sql = ", ".join(set_parts)
    params = list(updates.values()) + [device_id]

    async with _pool.acquire() as conn:
        await _ensure_table(conn)
        row = await conn.fetchrow(
            f"UPDATE device_inventory SET {set_sql} WHERE id = ${len(params)} RETURNING *",
            *params,
        )
    if not row:
        raise HTTPException(404, "inventory row not found")
    return {"ok": True, "device": _serialize(row)}


@router.get("/stats")
async def inventory_stats(
    x_admin_key: Optional[str] = Header(None),
):
    """Counts by status + revenue summary."""
    _require_admin_key(x_admin_key)

    async with _pool.acquire() as conn:
        await _ensure_table(conn)
        rows = await conn.fetch("""
            SELECT status, COUNT(*) AS cnt,
                   COALESCE(SUM(sale_price_ils) FILTER (WHERE status IN ('sold','shipped','active')), 0) AS revenue
            FROM device_inventory
            GROUP BY status
        """)

    by_status = {r["status"]: {"count": r["cnt"], "revenue_ils": float(r["revenue"])} for r in rows}
    total_devices = sum(v["count"] for v in by_status.values())
    total_revenue = sum(v["revenue_ils"] for v in by_status.values())

    return {
        "by_status": by_status,
        "total_devices": total_devices,
        "total_revenue_ils": total_revenue,
    }
