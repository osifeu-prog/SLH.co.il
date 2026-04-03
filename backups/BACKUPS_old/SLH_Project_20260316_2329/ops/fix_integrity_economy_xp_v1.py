from pathlib import Path
from textwrap import dedent

root = Path(".")

economy_path = root / "app" / "services" / "economy.py"
xp_path = root / "app" / "services" / "xp.py"

economy_text = dedent("""\
from app.db.database import db


async def ensure_user_balance(user_id: int) -> None:
    async with db.pool.acquire() as conn:
        await conn.execute(
            \"""
            INSERT INTO user_balances (user_id, available, locked)
            VALUES ($1, 0, 0)
            ON CONFLICT (user_id) DO NOTHING
            \""",
            user_id,
        )


async def add_balance(user_id: int, amount):
    amount = float(amount)
    async with db.pool.acquire() as conn:
        async with conn.transaction():
            await conn.execute(
                \"""
                INSERT INTO user_balances (user_id, available, locked)
                VALUES ($1, 0, 0)
                ON CONFLICT (user_id) DO NOTHING
                \""",
                user_id,
            )

            await conn.execute(
                \"""
                UPDATE user_balances
                SET available = available + $1,
                    updated_at = CURRENT_TIMESTAMP
                WHERE user_id = $2
                \""",
                amount,
                user_id,
            )

            await conn.execute(
                \"""
                UPDATE users
                SET balance = COALESCE(balance, 0) + $1
                WHERE user_id = $2
                \""",
                amount,
                user_id,
            )


async def subtract_balance(user_id: int, amount):
    amount = float(amount)
    async with db.pool.acquire() as conn:
        async with conn.transaction():
            await conn.execute(
                \"""
                INSERT INTO user_balances (user_id, available, locked)
                VALUES ($1, 0, 0)
                ON CONFLICT (user_id) DO NOTHING
                \""",
                user_id,
            )

            await conn.execute(
                \"""
                UPDATE user_balances
                SET available = available - $1,
                    updated_at = CURRENT_TIMESTAMP
                WHERE user_id = $2
                \""",
                amount,
                user_id,
            )

            await conn.execute(
                \"""
                UPDATE users
                SET balance = COALESCE(balance, 0) - $1
                WHERE user_id = $2
                \""",
                amount,
                user_id,
            )


async def get_balance(user_id: int):
    async with db.pool.acquire() as conn:
        await conn.execute(
            \"""
            INSERT INTO user_balances (user_id, available, locked)
            VALUES ($1, 0, 0)
            ON CONFLICT (user_id) DO NOTHING
            \""",
            user_id,
        )

        row = await conn.fetchrow(
            \"""
            SELECT available, locked
            FROM user_balances
            WHERE user_id = $1
            \""",
            user_id,
        )

        if not row:
            return {"available": 0, "locked": 0}

        return {
            "available": float(row["available"]),
            "locked": float(row["locked"]),
        }
""")

xp_text = dedent("""\
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
                \"""
                SELECT COALESCE(xp_total, 0) AS xp_total
                FROM users
                WHERE user_id = $1
                FOR UPDATE
                \""",
                user_id,
            )

            current_xp = int(row["xp_total"] or 0) if row else 0
            new_xp = max(0, current_xp + int(xp_delta))
            new_level = level_from_xp(new_xp)

            await conn.execute(
                \"""
                UPDATE users
                SET xp_total = $1,
                    level = $2,
                    last_active_at = CURRENT_TIMESTAMP
                WHERE user_id = $3
                \""",
                new_xp,
                new_level,
                user_id,
            )

            await conn.execute(
                \"""
                INSERT INTO xp_events (user_id, event_type, xp_delta, payload_json)
                VALUES ($1, $2, $3, $4)
                \""",
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
""")

economy_path.write_text(economy_text, encoding="utf-8", newline="\n")
xp_path.write_text(xp_text, encoding="utf-8", newline="\n")

print("economy.py and xp.py rewritten cleanly")