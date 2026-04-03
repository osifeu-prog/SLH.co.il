ALLOWED_TRANSITIONS = {
    "created": [
        "awaiting_payment",
        "cancelled",
    ],
    "awaiting_payment": [
        "payment_submitted",
        "expired",
        "cancelled",
    ],
    "payment_submitted": [
        "payment_review",
        "awaiting_payment",
        "cancelled",
    ],
    "payment_review": [
        "paid",
        "awaiting_payment",
        "cancelled",
    ],
    "paid": [
        "fulfillment_pending",
        "refunded",
    ],
    "fulfillment_pending": [
        "fulfilled",
    ],
    "fulfilled": [],
    "cancelled": [],
    "expired": [],
    "refunded": [],
}


async def transition_order_state(conn, order_id: int, from_state: str, to_state: str) -> dict:
    if to_state not in ALLOWED_TRANSITIONS.get(from_state, []):
        raise ValueError(f"Illegal state transition {from_state} -> {to_state}")

    row = await conn.fetchrow(
        """
        UPDATE purchase_orders
        SET status = $1,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = $2
          AND status = $3
        RETURNING *
        """,
        to_state,
        int(order_id),
        from_state,
    )

    if not row:
        raise RuntimeError("Order state changed concurrently or order not found")

    return dict(row)