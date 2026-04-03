import json

from app.services.commerce_events import log_commerce_event
from app.db.database import db


async def list_product_groups(limit: int = 50) -> list[dict]:
    safe_limit = max(1, min(int(limit), 200))

    async with db.pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT
                id,
                code,
                title,
                description,
                sort_order,
                is_active,
                created_at,
                updated_at
            FROM product_groups
            ORDER BY sort_order ASC, id ASC
            LIMIT $1
            """,
            safe_limit,
        )

    return [dict(r) for r in rows]


async def list_products_admin(limit: int = 100) -> list[dict]:
    safe_limit = max(1, min(int(limit), 500))

    async with db.pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT
                p.id,
                p.code,
                p.title,
                p.description,
                p.price_amount,
                p.price_currency,
                p.product_type,
                p.is_active,
                p.is_visible,
                p.sort_order,
                p.is_featured,
                p.inventory_mode,
                p.inventory_count,
                p.purchase_limit_per_user,
                p.requires_admin_delivery,
                p.image_url,
                p.success_message_template,
                p.created_at,
                p.updated_at,
                pg.id AS group_id,
                pg.code AS group_code,
                pg.title AS group_title,
                pg.sort_order AS group_sort_order
            FROM products p
            LEFT JOIN product_groups pg ON pg.id = p.group_id
            ORDER BY
                COALESCE(pg.sort_order, 999999) ASC,
                p.sort_order ASC,
                p.id ASC
            LIMIT $1
            """,
            safe_limit,
        )

    return [dict(r) for r in rows]


async def hide_product(product_code: str, admin_user_id: int) -> dict:
    code = (product_code or "").strip().upper()
    if not code:
        return {"ok": False, "error": "Product code is required."}

    async with db.pool.acquire() as conn:
        async with conn.transaction():
            row = await conn.fetchrow(
                """
                UPDATE products
                SET is_visible = FALSE,
                    updated_at = CURRENT_TIMESTAMP
                WHERE UPPER(code) = UPPER($1)
                RETURNING id, code, title, is_visible, is_active, sort_order, group_id
                """,
                code,
            )
            if not row:
                return {"ok": False, "error": "Product not found."}

            payload = json.dumps(
                {
                    "product_id": int(row["id"]),
                    "product_code": str(row["code"]),
                    "admin_user_id": int(admin_user_id),
                    "is_visible": False,
                },
                ensure_ascii=False,
                separators=(",", ":"),
            )
            await conn.execute(
                """
                INSERT INTO audit_log (user_id, event_type, payload_json, created_at)
                VALUES (NULL, $1, $2, CURRENT_TIMESTAMP)
                """,
                "product.hidden",
                payload,
            )

    return {"ok": True, "row": dict(row)}


async def show_product(product_code: str, admin_user_id: int) -> dict:
    code = (product_code or "").strip().upper()
    if not code:
        return {"ok": False, "error": "Product code is required."}

    async with db.pool.acquire() as conn:
        async with conn.transaction():
            row = await conn.fetchrow(
                """
                UPDATE products
                SET is_visible = TRUE,
                    updated_at = CURRENT_TIMESTAMP
                WHERE UPPER(code) = UPPER($1)
                RETURNING id, code, title, is_visible, is_active, sort_order, group_id
                """,
                code,
            )
            if not row:
                return {"ok": False, "error": "Product not found."}

            payload = json.dumps(
                {
                    "product_id": int(row["id"]),
                    "product_code": str(row["code"]),
                    "admin_user_id": int(admin_user_id),
                    "is_visible": True,
                },
                ensure_ascii=False,
                separators=(",", ":"),
            )
            await conn.execute(
                """
                INSERT INTO audit_log (user_id, event_type, payload_json, created_at)
                VALUES (NULL, $1, $2, CURRENT_TIMESTAMP)
                """,
                "product.shown",
                payload,
            )

    return {"ok": True, "row": dict(row)}


async def set_product_group(product_code: str, group_code: str, admin_user_id: int) -> dict:
    pcode = (product_code or "").strip().upper()
    gcode = (group_code or "").strip().upper()

    if not pcode or not gcode:
        return {"ok": False, "error": "Product code and group code are required."}

    async with db.pool.acquire() as conn:
        async with conn.transaction():
            group_row = await conn.fetchrow(
                """
                SELECT id, code, title
                FROM product_groups
                WHERE UPPER(code) = UPPER($1)
                LIMIT 1
                """,
                gcode,
            )
            if not group_row:
                return {"ok": False, "error": "Group not found."}

            row = await conn.fetchrow(
                """
                UPDATE products
                SET group_id = $2,
                    updated_at = CURRENT_TIMESTAMP
                WHERE UPPER(code) = UPPER($1)
                RETURNING id, code, title, group_id, sort_order, is_visible, is_active
                """,
                pcode,
                int(group_row["id"]),
            )
            if not row:
                return {"ok": False, "error": "Product not found."}

            payload = json.dumps(
                {
                    "product_id": int(row["id"]),
                    "product_code": str(row["code"]),
                    "group_id": int(group_row["id"]),
                    "group_code": str(group_row["code"]),
                    "group_title": str(group_row["title"]),
                    "admin_user_id": int(admin_user_id),
                },
                ensure_ascii=False,
                separators=(",", ":"),
            )
            await conn.execute(
                """
                INSERT INTO audit_log (user_id, event_type, payload_json, created_at)
                VALUES (NULL, $1, $2, CURRENT_TIMESTAMP)
                """,
                "product.group_changed",
                payload,
            )

    return {
        "ok": True,
        "row": {
            **dict(row),
            "group_code": str(group_row["code"]),
            "group_title": str(group_row["title"]),
        },
    }


async def list_purchase_orders_admin(limit: int = 50, statuses: tuple[str, ...] | None = None) -> list[dict]:
    safe_limit = max(1, min(int(limit), 200))
    effective_statuses = statuses or ("payment_submitted", "pending_payment", "paid")

    async with db.pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT
                po.id,
                po.user_id,
                po.product_id,
                po.product_code,
                po.product_title,
                po.quantity,
                po.unit_price_amount,
                po.total_amount,
                po.currency,
                po.payment_method,
                po.status,
                po.external_payment_ref,
                po.admin_note,
                po.paid_at,
                po.fulfilled_at,
                po.created_at,
                po.updated_at
            FROM purchase_orders po
            WHERE po.status = ANY($1::text[])
            ORDER BY
                CASE po.status
                    WHEN 'payment_submitted' THEN 1
                    WHEN 'pending_payment' THEN 2
                    WHEN 'paid' THEN 3
                    ELSE 99
                END ASC,
                po.id DESC
            LIMIT $2
            """,
            list(effective_statuses),
            safe_limit,
        )

    return [dict(r) for r in rows]


async def get_purchase_order_admin(order_id: int) -> dict | None:
    async with db.pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT
                po.id,
                po.user_id,
                po.product_id,
                po.product_code,
                po.product_title,
                po.quantity,
                po.unit_price_amount,
                po.total_amount,
                po.currency,
                po.payment_method,
                po.status,
                po.external_payment_ref,
                po.admin_note,
                po.paid_at,
                po.fulfilled_at,
                po.created_at,
                po.updated_at
            FROM purchase_orders po
            WHERE po.id = $1
            LIMIT 1
            """,
            int(order_id),
        )

    return dict(row) if row else None


async def _review_latest_purchase_submission(
    conn,
    order_id: int,
    review_status: str,
    admin_user_id: int,
    review_notes: str,
) -> dict | None:
    row = await conn.fetchrow(
        """
        UPDATE purchase_payment_submissions
        SET review_status = $2,
            reviewed_by_user_id = $3,
            reviewed_at = CURRENT_TIMESTAMP,
            review_notes = $4
        WHERE id = (
            SELECT id
            FROM purchase_payment_submissions
            WHERE order_id = $1
              AND review_status = 'pending'
            ORDER BY id DESC
            LIMIT 1
        )
        RETURNING *
        """,
        int(order_id),
        str(review_status),
        int(admin_user_id),
        str(review_notes or ""),
    )
    return dict(row) if row else None


async def _grant_purchase_points(conn, user_id: int, amount: float) -> float:
    granted = float(amount or 0)
    if granted <= 0:
        return 0.0

    await conn.execute(
        """
        UPDATE users
        SET balance = COALESCE(balance, 0) + $2,
            last_active_at = CURRENT_TIMESTAMP
        WHERE user_id = $1
        """,
        int(user_id),
        granted,
    )
    return granted


async def mark_purchase_order_paid_admin(
    order_id: int,
    admin_user_id: int,
    payment_ref: str | None = None,
    admin_note: str | None = None,
) -> dict:
    ref = (payment_ref or "").strip()
    note = (admin_note or "").strip() or "approved_by_admin"

    async with db.pool.acquire() as conn:
        async with conn.transaction():
            row = await conn.fetchrow(
                """
                SELECT
                    id,
                    user_id,
                    product_id,
                    product_code,
                    product_title,
                    quantity,
                    unit_price_amount,
                    total_amount,
                    currency,
                    payment_method,
                    status,
                    external_payment_ref,
                    admin_note,
                    paid_at,
                    fulfilled_at,
                    created_at,
                    updated_at
                FROM purchase_orders
                WHERE id = $1
                FOR UPDATE
                """,
                int(order_id),
            )
            if not row:
                return {"ok": False, "error": f"Purchase order #{int(order_id)} not found."}

            status = str(row["status"] or "")
            if status not in ("pending_payment", "payment_submitted"):
                return {"ok": False, "error": f"Order status is {status}, cannot approve payment."}

            final_ref = ref or str(row["external_payment_ref"] or "").strip()
            if not final_ref:
                return {"ok": False, "error": "Payment reference is required."}

            fraud_check = await fraud_guard_payment_ref(conn, final_ref, int(order_id))
            if not fraud_check.get("ok"):
                return fraud_check

            updated = await conn.fetchrow(
                """
                UPDATE purchase_orders
                SET status = 'paid',
                    external_payment_ref = NULLIF($2::text, ''),
                    admin_note = $3::text,
                    paid_at = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = $1
                  AND status IN ('pending_payment', 'payment_submitted')
                RETURNING
                    id,
                    user_id,
                    product_id,
                    product_code,
                    product_title,
                    quantity,
                    unit_price_amount,
                    total_amount,
                    currency,
                    payment_method,
                    status,
                    external_payment_ref,
                    admin_note,
                    paid_at,
                    fulfilled_at,
                    created_at,
                    updated_at
                """,
                int(order_id),
                final_ref,
                note,
            )

            if not updated:
                return {"ok": False, "error": f"Purchase order #{int(order_id)} was not updated."}

            await _review_latest_purchase_submission(
                conn,
                int(updated["id"]),
                "approved",
                int(admin_user_id),
                note,
            )

            points_granted = await _grant_purchase_points(
                conn,
                int(updated["user_id"]),
                float(updated["total_amount"] or 0),
            )

            payload = json.dumps(
                {
                    "purchase_order_id": int(updated["id"]),
                    "admin_user_id": int(admin_user_id),
                    "status": "paid",
                    "external_payment_ref": str(updated["external_payment_ref"] or ""),
                    "admin_note": str(updated["admin_note"] or ""),
                    "points_granted": points_granted,
                },
                ensure_ascii=False,
                separators=(",", ":"),
            )
            await conn.execute(
                """
                INSERT INTO audit_log (user_id, event_type, payload_json, created_at)
                VALUES ($1, $2, $3, CURRENT_TIMESTAMP)
                """,
                int(admin_user_id),
                "purchase.order_paid",
                payload,
            )

            await log_commerce_event(
                conn,
                int(updated["id"]),
                "purchase.order_paid",
                int(admin_user_id),
                {
                    "purchase_order_id": int(updated["id"]),
                    "admin_user_id": int(admin_user_id),
                    "status": "paid",
                    "external_payment_ref": str(updated["external_payment_ref"] or ""),
                    "admin_note": str(updated["admin_note"] or ""),
                    "points_granted": points_granted,
                },
            )

    result_row = dict(updated)
    result_row["points_granted"] = points_granted
    return {"ok": True, "row": result_row}


async def reject_purchase_order_payment_admin(
    order_id: int,
    admin_user_id: int,
    admin_note: str | None = None,
) -> dict:
    note = (admin_note or "").strip() or "rejected_by_admin"

    async with db.pool.acquire() as conn:
        async with conn.transaction():
            row = await conn.fetchrow(
                """
                SELECT
                    id,
                    user_id,
                    product_id,
                    product_code,
                    product_title,
                    quantity,
                    unit_price_amount,
                    total_amount,
                    currency,
                    payment_method,
                    status,
                    external_payment_ref,
                    admin_note,
                    paid_at,
                    fulfilled_at,
                    created_at,
                    updated_at
                FROM purchase_orders
                WHERE id = $1
                FOR UPDATE
                """,
                int(order_id),
            )
            if not row:
                return {"ok": False, "error": f"Purchase order #{int(order_id)} not found."}

            status = str(row["status"] or "")
            if status not in ("pending_payment", "payment_submitted"):
                return {"ok": False, "error": f"Order status is {status}, cannot reject payment."}

            updated = await conn.fetchrow(
                """
                UPDATE purchase_orders
                SET status = 'pending_payment',
                    external_payment_ref = NULL,
                    admin_note = $2::text,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = $1
                  AND status IN ('pending_payment', 'payment_submitted')
                RETURNING
                    id,
                    user_id,
                    product_id,
                    product_code,
                    product_title,
                    quantity,
                    unit_price_amount,
                    total_amount,
                    currency,
                    payment_method,
                    status,
                    external_payment_ref,
                    admin_note,
                    paid_at,
                    fulfilled_at,
                    created_at,
                    updated_at
                """,
                int(order_id),
                note,
            )
            if not updated:
                return {"ok": False, "error": f"Purchase order #{int(order_id)} was not updated."}

            await _review_latest_purchase_submission(
                conn,
                int(updated["id"]),
                "rejected",
                int(admin_user_id),
                note,
            )

            payload = json.dumps(
                {
                    "purchase_order_id": int(updated["id"]),
                    "admin_user_id": int(admin_user_id),
                    "status": "pending_payment",
                    "admin_note": str(updated["admin_note"] or ""),
                },
                ensure_ascii=False,
                separators=(",", ":"),
            )
            await conn.execute(
                """
                INSERT INTO audit_log (user_id, event_type, payload_json, created_at)
                VALUES ($1, $2, $3, CURRENT_TIMESTAMP)
                """,
                int(admin_user_id),
                "purchase.payment_rejected",
                payload,
            )

            await log_commerce_event(
                conn,
                int(updated["id"]),
                "purchase.payment_rejected",
                int(admin_user_id),
                {
                    "purchase_order_id": int(updated["id"]),
                    "admin_user_id": int(admin_user_id),
                    "status": "pending_payment",
                    "admin_note": str(updated["admin_note"] or ""),
                },
            )

    return {"ok": True, "row": dict(updated)}


async def fulfill_purchase_order_admin(order_id: int, admin_user_id: int, admin_note: str | None = None) -> dict:
    note = (admin_note or "").strip() or "fulfilled_by_admin"

    async with db.pool.acquire() as conn:
        async with conn.transaction():
            row = await conn.fetchrow(
                """
                SELECT
                    id,
                    user_id,
                    product_id,
                    product_code,
                    product_title,
                    quantity,
                    unit_price_amount,
                    total_amount,
                    currency,
                    payment_method,
                    status,
                    external_payment_ref,
                    admin_note,
                    paid_at,
                    fulfilled_at,
                    created_at,
                    updated_at
                FROM purchase_orders
                WHERE id = $1
                FOR UPDATE
                """,
                int(order_id),
            )
            if not row:
                return {"ok": False, "error": f"Purchase order #{int(order_id)} not found."}

            if row["fulfilled_at"]:
                return {"ok": True, "row": dict(row), "message": "Already fulfilled"}

            status = str(row["status"] or "")
            if status != "paid":
                return {"ok": False, "error": f"Order status is {status}, cannot fulfill."}

            updated = await conn.fetchrow(
                """
                UPDATE purchase_orders
                SET status = 'fulfilled',
                    admin_note = $2::text,
                    fulfilled_at = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = $1
                  AND status = 'paid'
                RETURNING
                    id,
                    user_id,
                    product_id,
                    product_code,
                    product_title,
                    quantity,
                    unit_price_amount,
                    total_amount,
                    currency,
                    payment_method,
                    status,
                    external_payment_ref,
                    admin_note,
                    paid_at,
                    fulfilled_at,
                    created_at,
                    updated_at
                """,
                int(order_id),
                note,
            )

            if not updated:
                return {"ok": False, "error": f"Purchase order #{int(order_id)} was not updated."}

            payload = json.dumps(
                {
                    "purchase_order_id": int(updated["id"]),
                    "admin_user_id": int(admin_user_id),
                    "status": "fulfilled",
                    "admin_note": str(updated["admin_note"] or ""),
                },
                ensure_ascii=False,
                separators=(",", ":"),
            )
            await conn.execute(
                """
                INSERT INTO audit_log (user_id, event_type, payload_json, created_at)
                VALUES ($1, $2, $3, CURRENT_TIMESTAMP)
                """,
                int(admin_user_id),
                "purchase.order_fulfilled",
                payload,
            )

            await log_commerce_event(
                conn,
                int(updated["id"]),
                "purchase.order_fulfilled",
                int(admin_user_id),
                {
                    "purchase_order_id": int(updated["id"]),
                    "admin_user_id": int(admin_user_id),
                    "status": "fulfilled",
                    "admin_note": str(updated["admin_note"] or ""),
                },
            )

    return {"ok": True, "row": dict(updated)}

async def update_product_price_admin(product_code: str, amount: float, admin_user_id: int) -> dict:
    code = (product_code or "").strip().upper()
    if not code:
        return {"ok": False, "error": "Product code is required."}

    if amount < 0:
        return {"ok": False, "error": "Amount must be non-negative."}

    async with db.pool.acquire() as conn:
        async with conn.transaction():
            row = await conn.fetchrow(
                """
                UPDATE products
                SET price_amount = $2,
                    updated_at = CURRENT_TIMESTAMP
                WHERE UPPER(code) = UPPER($1)
                RETURNING id, code, title, price_amount, price_currency
                """,
                code,
                float(amount),
            )
            if not row:
                return {"ok": False, "error": "Product not found."}

            payload = json.dumps(
                {
                    "product_id": int(row["id"]),
                    "product_code": str(row["code"]),
                    "price_amount": float(row["price_amount"]),
                    "admin_user_id": int(admin_user_id),
                },
                ensure_ascii=False,
                separators=(",", ":"),
            )
            await conn.execute(
                """
                INSERT INTO audit_log (user_id, event_type, payload_json, created_at)
                VALUES ($1, $2, $3, CURRENT_TIMESTAMP)
                """,
                int(admin_user_id),
                "product.price_updated",
                payload,
            )

    return {"ok": True, "row": dict(row)}


async def list_system_settings_admin(limit: int = 50) -> list[dict]:
    safe_limit = max(1, min(int(limit), 200))

    async with db.pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT key, value_text, updated_at
            FROM system_settings
            ORDER BY key ASC
            LIMIT $1
            """,
            safe_limit,
        )

    return [dict(r) for r in rows]


async def set_system_setting_text_admin(key: str, value_text: str, admin_user_id: int) -> dict:
    clean_key = (key or "").strip()
    clean_value = str(value_text or "").strip()

    if not clean_key:
        return {"ok": False, "error": "Setting key is required."}

    async with db.pool.acquire() as conn:
        async with conn.transaction():
            row = await conn.fetchrow(
                """
                INSERT INTO system_settings (key, value_text, updated_at)
                VALUES ($1, $2, CURRENT_TIMESTAMP)
                ON CONFLICT (key)
                DO UPDATE SET
                    value_text = EXCLUDED.value_text,
                    updated_at = CURRENT_TIMESTAMP
                RETURNING key, value_text, updated_at
                """,
                clean_key,
                clean_value,
            )

            payload = json.dumps(
                {
                    "key": str(row["key"]),
                    "value_text": str(row["value_text"] or ""),
                    "admin_user_id": int(admin_user_id),
                },
                ensure_ascii=False,
                separators=(",", ":"),
            )
            await conn.execute(
                """
                INSERT INTO audit_log (user_id, event_type, payload_json, created_at)
                VALUES ($1, $2, $3, CURRENT_TIMESTAMP)
                """,
                int(admin_user_id),
                "system_setting.updated",
                payload,
            )

    return {"ok": True, "row": dict(row)}


async def fraud_guard_payment_ref(conn, payment_ref: str, exclude_order_id: int | None = None):
    clean_ref = str(payment_ref or "").strip()
    if not clean_ref or len(clean_ref) < 5:
        return {"ok": False, "error": "Invalid payment reference"}

    if exclude_order_id is None:
        row = await conn.fetchrow(
            """
            SELECT id FROM purchase_orders
            WHERE external_payment_ref = $1
            LIMIT 1
            """,
            clean_ref
        )
    else:
        row = await conn.fetchrow(
            """
            SELECT id FROM purchase_orders
            WHERE external_payment_ref = $1
              AND id <> $2
            LIMIT 1
            """,
            clean_ref,
            int(exclude_order_id),
        )

    if row:
        return {"ok": False, "error": "Payment reference already used"}

    return {"ok": True}
