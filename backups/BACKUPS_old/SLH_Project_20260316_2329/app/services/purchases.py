import json
import re

from app.db.database import db


PAYMENT_REF_RE = re.compile(r"^[A-Za-z0-9._\-\/# ]{3,140}$")


async def _get_setting_bool(conn, key: str, default: bool = False) -> bool:
    row = await conn.fetchrow(
        """
        SELECT value_text
        FROM system_settings
        WHERE key = $1
        LIMIT 1
        """,
        key,
    )
    if not row:
        return default

    raw = str(row["value_text"] or "").strip().lower()
    return raw in ("1", "true", "yes", "on")


async def _get_setting_text(conn, key: str, default: str = "") -> str:
    row = await conn.fetchrow(
        """
        SELECT value_text
        FROM system_settings
        WHERE key = $1
        LIMIT 1
        """,
        key,
    )
    if not row:
        return default
    return str(row["value_text"] or "").strip()


def _normalize_product_code(raw: str) -> str:
    value = str(raw or "").strip().upper()
    if not value:
        raise ValueError("Product code is required.")
    return value


def _normalize_payment_ref(raw: str) -> str:
    value = str(raw or "").strip()

    if not value:
        raise ValueError("Payment reference is required.")
    if "\n" in value or "\r" in value:
        raise ValueError("Payment reference must be a single line.")
    if "|" in value:
        raise ValueError("Payment reference contains unsupported characters.")
    if not PAYMENT_REF_RE.fullmatch(value):
        raise ValueError("Payment reference must be 3-140 valid characters.")

    return value


async def get_commerce_flags() -> dict:
    async with db.pool.acquire() as conn:
        commerce_enabled = await _get_setting_bool(conn, "commerce_enabled", False)
        purchase_manual_payment_enabled = await _get_setting_bool(conn, "purchase_manual_payment_enabled", True)
        purchase_ton_payment_enabled = await _get_setting_bool(conn, "purchase_ton_payment_enabled", False)
        store_visible_to_users = await _get_setting_bool(conn, "store_visible_to_users", True)
        purchase_user_cancel_enabled = await _get_setting_bool(conn, "purchase_user_cancel_enabled", True)
        store_featured_enabled = await _get_setting_bool(conn, "store_featured_enabled", True)
        store_inventory_enforced = await _get_setting_bool(conn, "store_inventory_enforced", True)
        store_purchase_limits_enforced = await _get_setting_bool(conn, "store_purchase_limits_enforced", True)

    return {
        "commerce_enabled": commerce_enabled,
        "purchase_manual_payment_enabled": purchase_manual_payment_enabled,
        "purchase_ton_payment_enabled": purchase_ton_payment_enabled,
        "store_visible_to_users": store_visible_to_users,
        "purchase_user_cancel_enabled": purchase_user_cancel_enabled,
        "store_featured_enabled": store_featured_enabled,
        "store_inventory_enforced": store_inventory_enforced,
        "store_purchase_limits_enforced": store_purchase_limits_enforced,
    }


async def get_manual_payment_config() -> dict:
    async with db.pool.acquire() as conn:
        title = await _get_setting_text(conn, "purchase_manual_payment_title", "ط£â€”أ¢â‚¬â€Œط£â€”ط¢آ¢ط£â€”أ¢â‚¬ع©ط£â€”ط¢آ¨ط£â€”أ¢â‚¬â€Œ ط£â€”أ¢â€‍آ¢ط£â€”أ¢â‚¬إ“ط£â€”ط¢آ ط£â€”أ¢â€‍آ¢ط£â€”ط¹آ¾")
        body = await _get_setting_text(
            conn,
            "purchase_manual_payment_body",
            "ط£â€”أ¢â€‍آ¢ط£â€”ط¢آ© ط£â€”ط¥â€œط£â€”أ¢â‚¬ع©ط£â€”ط¢آ¦ط£â€”ط¢آ¢ ط£â€”ط¹آ¯ط£â€”ط¹آ¾ ط£â€”أ¢â‚¬â€Œط£â€”ط¹آ¾ط£â€”ط¢آ©ط£â€”ط¥â€œط£â€”أ¢â‚¬آ¢ط£â€”أ¢â‚¬إ’ ط£â€”أ¢â‚¬ع©ط£â€”أ¢â‚¬â€Œط£â€”ط¹آ¾ط£â€”ط¹آ¯ط£â€”أ¢â‚¬إ’ ط£â€”ط¥â€œط£â€”ط¢آ¤ط£â€”ط¢آ¨ط£â€”ط¹آ©ط£â€”أ¢â€‍آ¢ ط£â€”أ¢â‚¬â€Œط£â€”ط¹آ¾ط£â€”ط¢آ©ط£â€”ط¥â€œط£â€”أ¢â‚¬آ¢ط£â€”أ¢â‚¬إ’ ط£â€”ط¢آ©ط£â€”ط·إ’ط£â€”أ¢â‚¬آ¢ط£â€”ط¢آ¤ط£â€”ط¢آ§ط£â€”أ¢â‚¬آ¢ ط£â€”أ¢â‚¬ع†ط£â€”أ¢â‚¬آ¢ط£â€”ط¥â€œ ط£â€”أ¢â‚¬â€Œط£â€”أ¢â‚¬ع†ط£â€”ط¢آ ط£â€”أ¢â‚¬â€Œط£â€”ط¥â€œ.",
        )
        receipt_footer = await _get_setting_text(conn, "purchase_receipt_footer", "ط£â€”ط¹آ¾ط£â€”أ¢â‚¬آ¢ط£â€”أ¢â‚¬إ“ط£â€”أ¢â‚¬â€Œ ط£â€”ط¢آ©ط£â€”ط¢آ¨ط£â€”أ¢â‚¬ط›ط£â€”ط¢آ©ط£â€”ط¹آ¾ ط£â€”أ¢â‚¬إ“ط£â€”ط¢آ¨ط£â€”ط¹â€ک ط£â€”أ¢â‚¬ع†ط£â€”ط¢آ¢ط£â€”ط¢آ¨ط£â€”أ¢â‚¬ط›ط£â€”ط¹آ¾ SLH.")
        friends_link = await _get_setting_text(conn, "friends_support_invite_link", "")

    return {
        "title": title,
        "body": body,
        "contact": contact,
        "receipt_footer": receipt_footer,
        "friends_support_invite_link": friends_link,
    }


async def list_active_products(limit: int = 50) -> dict:
    safe_limit = max(1, min(int(limit), 200))

    async with db.pool.acquire() as conn:
        commerce_enabled = await _get_setting_bool(conn, "commerce_enabled", False)
        if not commerce_enabled:
            return {"ok": False, "error": "Store is currently unavailable."}

        store_visible_to_users = await _get_setting_bool(conn, "store_visible_to_users", True)
        if not store_visible_to_users:
            return {"ok": False, "error": "Store is currently hidden."}

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
                pg.description AS group_description,
                pg.sort_order AS group_sort_order
            FROM products p
            LEFT JOIN product_groups pg ON pg.id = p.group_id
            WHERE p.is_active = TRUE
              AND p.is_visible = TRUE
            ORDER BY
                COALESCE(pg.sort_order, 999999) ASC,
                COALESCE(pg.title, 'ZZZ') ASC,
                p.sort_order ASC,
                p.id ASC
            LIMIT $1
            """,
            safe_limit,
        )

    return {"ok": True, "rows": [dict(r) for r in rows]}


async def create_purchase_order(user_id: int, product_code: str, quantity: int = 1) -> dict:
    try:
        code = _normalize_product_code(product_code)
    except ValueError as e:
        return {"ok": False, "error": str(e)}

    try:
        qty = int(quantity)
    except Exception:
        return {"ok": False, "error": "Quantity must be an integer."}

    if qty <= 0:
        return {"ok": False, "error": "Quantity must be positive."}

    async with db.pool.acquire() as conn:
        async with conn.transaction():
            commerce_enabled = await _get_setting_bool(conn, "commerce_enabled", False)
            if not commerce_enabled:
                return {"ok": False, "error": "Store is currently unavailable."}

            store_visible_to_users = await _get_setting_bool(conn, "store_visible_to_users", True)
            if not store_visible_to_users:
                return {"ok": False, "error": "Store is currently hidden."}

            purchase_manual_payment_enabled = await _get_setting_bool(conn, "purchase_manual_payment_enabled", True)
            if not purchase_manual_payment_enabled:
                return {"ok": False, "error": "Manual purchase flow is currently disabled."}

            store_inventory_enforced = await _get_setting_bool(conn, "store_inventory_enforced", True)
            store_purchase_limits_enforced = await _get_setting_bool(conn, "store_purchase_limits_enforced", True)

            product = await conn.fetchrow(
                """
                SELECT
                    id,
                    code,
                    title,
                    description,
                    price_amount,
                    price_currency,
                    product_type,
                    is_active,
                    is_visible,
                    is_featured,
                    inventory_mode,
                    inventory_count,
                    purchase_limit_per_user,
                    requires_admin_delivery,
                    image_url,
                    success_message_template
                FROM products
                WHERE UPPER(code) = UPPER($1)
                FOR UPDATE
                """,
                code,
            )

            if not product:
                return {"ok": False, "error": f"Product '{code}' was not found."}
            if not bool(product["is_active"]):
                return {"ok": False, "error": f"Product '{code}' is not active."}
            if not bool(product["is_visible"]):
                return {"ok": False, "error": f"Product '{code}' is currently hidden."}

            if store_inventory_enforced and str(product["inventory_mode"] or "unlimited") == "limited":
                current_inventory = int(product["inventory_count"] or 0)
                if current_inventory < qty:
                    return {"ok": False, "error": f"Insufficient inventory for '{code}'."}

            if store_purchase_limits_enforced and product["purchase_limit_per_user"] is not None:
                current_count = await conn.fetchval(
                    """
                    SELECT COUNT(*)
                    FROM purchase_orders
                    WHERE user_id = $1
                      AND UPPER(product_code) = UPPER($2)
                      AND status <> 'cancelled'
                    """,
                    int(user_id),
                    str(product["code"]),
                )
                if int(current_count or 0) >= int(product["purchase_limit_per_user"]):
                    return {"ok": False, "error": f"Purchase limit reached for '{code}'."}

            unit_price = float(product["price_amount"] or 0)
            total_amount = unit_price * qty

            if store_inventory_enforced and str(product["inventory_mode"] or "unlimited") == "limited":
                await conn.execute(
                    """
                    UPDATE products
                    SET inventory_count = inventory_count - $2,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = $1
                    """,
                    int(product["id"]),
                    qty,
                )

            row = await conn.fetchrow(
                """
                INSERT INTO purchase_orders (
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
                    created_at,
                    updated_at
                )
                VALUES (
                    $1, $2, $3, $4, $5, $6, $7, $8,
                    'manual',
                    'pending_payment',
                    CURRENT_TIMESTAMP,
                    CURRENT_TIMESTAMP
                )
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
                int(user_id),
                int(product["id"]),
                str(product["code"]),
                str(product["title"]),
                int(qty),
                unit_price,
                total_amount,
                str(product["price_currency"] or "TON"),
            )

            payload = json.dumps(
                {
                    "purchase_order_id": int(row["id"]),
                    "product_id": int(product["id"]),
                    "product_code": str(row["product_code"]),
                    "product_title": str(row["product_title"]),
                    "quantity": int(row["quantity"]),
                    "unit_price_amount": float(row["unit_price_amount"]),
                    "total_amount": float(row["total_amount"]),
                    "currency": str(row["currency"]),
                    "payment_method": str(row["payment_method"]),
                    "status": str(row["status"]),
                },
                ensure_ascii=False,
                separators=(",", ":"),
            )
            await conn.execute(
                """
                INSERT INTO audit_log (user_id, event_type, payload_json, created_at)
                VALUES ($1, $2, $3, CURRENT_TIMESTAMP)
                """,
                int(user_id),
                "purchase.order_created",
                payload,
            )

    payment_cfg = await get_manual_payment_config()
    return {
        "ok": True,
        "order": dict(row),
        "payment_config": payment_cfg,
    }


async def list_user_purchase_orders(user_id: int, limit: int = 10) -> list[dict]:
    safe_limit = max(1, min(int(limit), 100))

    async with db.pool.acquire() as conn:
        rows = await conn.fetch(
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
            WHERE user_id = $1
            ORDER BY id DESC
            LIMIT $2
            """,
            int(user_id),
            safe_limit,
        )

    return [dict(r) for r in rows]


async def submit_purchase_payment(order_id: int, user_id: int, payment_ref: str) -> dict:
    try:
        clean_ref = _normalize_payment_ref(payment_ref)
    except ValueError as e:
        return {"ok": False, "error": str(e)}

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
                  AND user_id = $2
                FOR UPDATE
                """,
                int(order_id),
                int(user_id),
            )
            if not row:
                return {"ok": False, "error": "Purchase order not found."}

            status = str(row["status"] or "")
            if status != "pending_payment":
                return {"ok": False, "error": f"Order status is {status}, cannot submit payment."}

            dup = await conn.fetchrow(
                """
                SELECT id
                FROM purchase_orders
                WHERE external_payment_ref = $1
                  AND id <> $2
                LIMIT 1
                """,
                clean_ref,
                int(order_id),
            )
            if dup:
                return {"ok": False, "error": "Payment reference already used."}

            updated = await conn.fetchrow(
                """
                UPDATE purchase_orders
                SET status = 'payment_submitted',
                    external_payment_ref = $3,
                    admin_note = 'awaiting_manual_review',
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = $1
                  AND user_id = $2
                  AND status = 'pending_payment'
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
                int(user_id),
                clean_ref,
            )
            if not updated:
                return {"ok": False, "error": "Purchase order was not updated."}

            await conn.execute(
                """
                INSERT INTO purchase_payment_submissions (
                    order_id,
                    submitted_by_user_id,
                    submitted_ref,
                    submitted_amount,
                    submitted_currency,
                    evidence_text,
                    review_status,
                    created_at
                )
                VALUES (
                    $1, $2, $3, $4, $5, $6, 'pending', CURRENT_TIMESTAMP
                )
                """,
                int(updated["id"]),
                int(user_id),
                clean_ref,
                float(updated["total_amount"] or 0),
                str(updated["currency"] or ""),
                clean_ref,
            )

            payload = json.dumps(
                {
                    "purchase_order_id": int(updated["id"]),
                    "product_code": str(updated["product_code"]),
                    "product_title": str(updated["product_title"]),
                    "payment_ref": str(updated["external_payment_ref"] or ""),
                    "status": "payment_submitted",
                },
                ensure_ascii=False,
                separators=(",", ":"),
            )

            await conn.execute(
                """
                INSERT INTO audit_log (user_id, event_type, payload_json, created_at)
                VALUES ($1, $2, $3, CURRENT_TIMESTAMP)
                """,
                int(user_id),
                "purchase.payment_submitted",
                payload,
            )

    return {"ok": True, "row": dict(updated)}


async def cancel_purchase_order(order_id: int, user_id: int) -> dict:
    async with db.pool.acquire() as conn:
        async with conn.transaction():
            purchase_user_cancel_enabled = await _get_setting_bool(conn, "purchase_user_cancel_enabled", True)
            if not purchase_user_cancel_enabled:
                return {"ok": False, "error": "Order cancellation is currently disabled."}

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
                  AND user_id = $2
                FOR UPDATE
                """,
                int(order_id),
                int(user_id),
            )
            if not row:
                return {"ok": False, "error": "Purchase order not found."}

            status = str(row["status"] or "")
            if status != "pending_payment":
                return {"ok": False, "error": f"Order status is {status}, cannot cancel."}

            product = await conn.fetchrow(
                """
                SELECT id, inventory_mode
                FROM products
                WHERE id = $1
                """,
                int(row["product_id"]),
            )
            if product and str(product["inventory_mode"] or "unlimited") == "limited":
                await conn.execute(
                    """
                    UPDATE products
                    SET inventory_count = COALESCE(inventory_count, 0) + $2,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = $1
                    """,
                    int(row["product_id"]),
                    int(row["quantity"]),
                )

            updated = await conn.fetchrow(
                """
                UPDATE purchase_orders
                SET status = 'cancelled',
                    admin_note = 'cancelled_by_user',
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = $1
                  AND user_id = $2
                  AND status = 'pending_payment'
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
                int(user_id),
            )
            if not updated:
                return {"ok": False, "error": "Purchase order was not updated."}

            payload = json.dumps(
                {
                    "purchase_order_id": int(updated["id"]),
                    "user_id": int(updated["user_id"]),
                    "status": "cancelled",
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
                int(user_id),
                "purchase.order_cancelled",
                payload,
            )

    return {"ok": True, "row": dict(updated)}