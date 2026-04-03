import json

from app.db.database import db


LEVEL_THRESHOLDS = [
    (1, 0),
    (2, 100),
    (3, 250),
    (4, 500),
    (5, 900),
    (6, 1400),
    (7, 2000),
    (8, 2800),
    (9, 3800),
    (10, 5000),
]


def level_from_xp(xp_total: int) -> int:
    lvl = 1
    for level, min_xp in LEVEL_THRESHOLDS:
        if xp_total >= min_xp:
            lvl = level
        else:
            break
    return lvl


async def grant_xp(user_id: int, event_type: str, xp_delta: int, payload: dict | None = None) -> dict:
    payload_json = json.dumps(payload or {}, ensure_ascii=False, separators=(",", ":"))

    async with db.pool.acquire() as conn:
        async with conn.transaction():
            row = await conn.fetchrow(
                """
                SELECT COALESCE(xp_total, 0) AS xp_total
                FROM users
                WHERE user_id = $1
                FOR UPDATE
                """,
                user_id,
            )

            current_xp = int(row["xp_total"] or 0) if row else 0
            new_xp = max(0, current_xp + int(xp_delta))
            new_level = level_from_xp(new_xp)

            await conn.execute(
                """
                UPDATE users
                SET xp_total = $1,
                    level = $2,
                    last_active_at = CURRENT_TIMESTAMP
                WHERE user_id = $3
                """,
                new_xp,
                new_level,
                user_id,
            )

            await conn.execute(
                """
                INSERT INTO xp_events (user_id, event_type, xp_delta, payload_json)
                VALUES ($1, $2, $3, $4)
                """,
                user_id,
                event_type,
                int(xp_delta),
                payload_json,
            )

    return {
        "ok": True,
        "xp_total": new_xp,
        "level": new_level,
        "xp_delta": int(xp_delta),
    }