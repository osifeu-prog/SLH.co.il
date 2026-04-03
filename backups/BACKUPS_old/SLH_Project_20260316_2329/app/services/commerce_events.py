import json


async def log_commerce_event(conn, order_id: int | None, event_type: str, actor_user_id: int | None, payload=None) -> None:
    payload_json = None
    if payload is not None:
        payload_json = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))

    await conn.execute(
        """
        INSERT INTO commerce_events (
            order_id,
            event_type,
            actor_user_id,
            payload_json,
            created_at
        )
        VALUES ($1, $2, $3, $4::jsonb, CURRENT_TIMESTAMP)
        """,
        order_id,
        event_type,
        actor_user_id,
        payload_json,
    )