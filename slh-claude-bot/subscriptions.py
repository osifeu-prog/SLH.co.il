"""
SLH AI Spark — Subscription DB layer.

Sits on the same SQLite file as `session.py` (sessions.db). Why same DB:
- Single file to back up / migrate
- Atomic queries that touch both messages + usage in one transaction
- Zero new infrastructure

Public API (all async):
- init_db()
- get_or_create(user_id) -> SubscriptionRow
- upgrade(user_id, tier, provider, payment_id, period_days=30)
- record_usage(user_id, chat_id, tier, provider, model, ti, to, cost_cents)
- record_payment(...)
- usage_stats(window_days=30) -> dict
- mrr() -> int (monthly recurring revenue in ILS)
"""
from __future__ import annotations

import os
import json
import datetime as dt
from dataclasses import dataclass
from typing import Optional

import aiosqlite

import pricing

DB_PATH = os.getenv("SESSION_DB", "/workspace/slh-claude-bot/sessions.db")
HERE = os.path.dirname(os.path.abspath(__file__))
MIGRATION_FILE = os.path.join(HERE, "migrations", "001_subscriptions.sql")


@dataclass
class SubscriptionRow:
    user_id: int
    tier: str
    current_period_start: str
    current_period_end: str
    messages_used_this_period: int
    payment_provider: Optional[str]
    payment_id: Optional[str]


async def init_db() -> None:
    """Apply schema migrations. Idempotent."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    if not os.path.exists(MIGRATION_FILE):
        # Embedded fallback — keeps the bot bootable even if file is missing
        sql = _EMBEDDED_SCHEMA
    else:
        with open(MIGRATION_FILE, "r", encoding="utf-8") as f:
            sql = f.read()
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executescript(sql)
        await db.commit()


def _now_iso() -> str:
    return dt.datetime.utcnow().isoformat(timespec="seconds")


def _period_end(start_iso: str, days: int = 30) -> str:
    start = dt.datetime.fromisoformat(start_iso)
    return (start + dt.timedelta(days=days)).isoformat(timespec="seconds")


async def get_or_create(user_id: int) -> SubscriptionRow:
    """Lookup user; lazy-create as Free tier if missing. Auto-rolls expired periods."""
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "SELECT user_id, tier, current_period_start, current_period_end, "
            "messages_used_this_period, payment_provider, payment_id "
            "FROM subscriptions WHERE user_id=?",
            (user_id,),
        )
        row = await cur.fetchone()
        if row is None:
            now = _now_iso()
            end = _period_end(now, 30)
            await db.execute(
                "INSERT INTO subscriptions "
                "(user_id, tier, current_period_start, current_period_end) "
                "VALUES (?, 'free', ?, ?)",
                (user_id, now, end),
            )
            await db.commit()
            return SubscriptionRow(user_id, "free", now, end, 0, None, None)
        sub = SubscriptionRow(*row)
        # If the period has rolled over, reset usage but keep the tier (auto-renew
        # behavior is implemented in payment webhook; here we just give a fresh
        # quota window if the prior period genuinely ended).
        if dt.datetime.utcnow().isoformat() > sub.current_period_end:
            now = _now_iso()
            end = _period_end(now, 30)
            new_tier = sub.tier if sub.tier == "free" else "free"  # downgrade on expiry
            await db.execute(
                "UPDATE subscriptions SET tier=?, current_period_start=?, "
                "current_period_end=?, messages_used_this_period=0, updated_at=? "
                "WHERE user_id=?",
                (new_tier, now, end, now, user_id),
            )
            await db.commit()
            return SubscriptionRow(user_id, new_tier, now, end, 0,
                                   sub.payment_provider, sub.payment_id)
        return sub


async def upgrade(user_id: int, tier: str, provider: str, payment_id: str,
                  period_days: int = 30) -> SubscriptionRow:
    """Bump user to a paid tier. Resets quota counter, sets new period."""
    if tier not in pricing.TIERS:
        raise ValueError(f"unknown tier: {tier}")
    now = _now_iso()
    end = _period_end(now, period_days)
    async with aiosqlite.connect(DB_PATH) as db:
        # Ensure row exists
        await db.execute(
            "INSERT OR IGNORE INTO subscriptions "
            "(user_id, tier, current_period_start, current_period_end) "
            "VALUES (?, 'free', ?, ?)",
            (user_id, now, end),
        )
        await db.execute(
            "UPDATE subscriptions SET tier=?, current_period_start=?, "
            "current_period_end=?, messages_used_this_period=0, "
            "payment_provider=?, payment_id=?, updated_at=? WHERE user_id=?",
            (tier, now, end, provider, payment_id, now, user_id),
        )
        await db.commit()
    return await get_or_create(user_id)


async def increment_usage_counter(user_id: int) -> int:
    """Add 1 to messages_used_this_period; return new value."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE subscriptions SET messages_used_this_period = "
            "messages_used_this_period + 1, updated_at=? WHERE user_id=?",
            (_now_iso(), user_id),
        )
        await db.commit()
        cur = await db.execute(
            "SELECT messages_used_this_period FROM subscriptions WHERE user_id=?",
            (user_id,),
        )
        row = await cur.fetchone()
        return row[0] if row else 0


async def record_usage(user_id: int, chat_id: int, tier: str, provider: str,
                       model: Optional[str], tokens_in: int, tokens_out: int,
                       cost_usd_cents: int) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO ai_usage (user_id, chat_id, tier, provider, model, "
            "tokens_input, tokens_output, cost_usd_cents) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (user_id, chat_id, tier, provider, model, tokens_in, tokens_out,
             cost_usd_cents),
        )
        await db.commit()


async def record_payment(user_id: int, provider: str, charge_id: str,
                         amount_stars: int, amount_ils_cents: int,
                         tier_purchased: str, status: str,
                         raw_payload: Optional[dict] = None) -> int:
    payload_str = json.dumps(raw_payload, ensure_ascii=False) if raw_payload else None
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "INSERT INTO payments (user_id, provider, provider_charge_id, "
            "amount_stars, amount_ils_cents, tier_purchased, status, raw_payload) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?) RETURNING id",
            (user_id, provider, charge_id, amount_stars, amount_ils_cents,
             tier_purchased, status, payload_str),
        )
        row = await cur.fetchone()
        await db.commit()
        return row[0] if row else 0


# ===== Reporting =====
async def usage_stats(window_days: int = 30) -> dict:
    """Aggregate stats for /revenue admin command."""
    cutoff = (dt.datetime.utcnow() - dt.timedelta(days=window_days)).isoformat()
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "SELECT tier, COUNT(*) FROM subscriptions GROUP BY tier"
        )
        tier_counts = {row[0]: row[1] for row in await cur.fetchall()}

        cur = await db.execute(
            "SELECT provider, COUNT(*), SUM(cost_usd_cents), "
            "SUM(tokens_input), SUM(tokens_output) "
            "FROM ai_usage WHERE created_at >= ? GROUP BY provider",
            (cutoff,),
        )
        usage_by_provider = {
            row[0]: {
                "messages": row[1],
                "cost_usd_cents": row[2] or 0,
                "tokens_in": row[3] or 0,
                "tokens_out": row[4] or 0,
            }
            for row in await cur.fetchall()
        }

        cur = await db.execute(
            "SELECT SUM(amount_ils_cents) FROM payments "
            "WHERE status='completed' AND created_at >= ?",
            (cutoff,),
        )
        revenue_row = await cur.fetchone()
        revenue_ils_cents = revenue_row[0] if revenue_row and revenue_row[0] else 0

    return {
        "tier_counts": tier_counts,
        "usage_by_provider": usage_by_provider,
        "revenue_ils_cents": revenue_ils_cents,
        "window_days": window_days,
    }


async def mrr_ils() -> float:
    """Monthly recurring revenue: sum of active paid subscriptions × tier price."""
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "SELECT tier, COUNT(*) FROM subscriptions "
            "WHERE current_period_end > ? AND tier != 'free' "
            "GROUP BY tier",
            (_now_iso(),),
        )
        rows = await cur.fetchall()
    return sum(
        count * pricing.TIERS[tier].price_ils for tier, count in rows
        if tier in pricing.TIERS
    )


# Embedded schema fallback (kept in sync with migrations/001_subscriptions.sql)
_EMBEDDED_SCHEMA = """
CREATE TABLE IF NOT EXISTS subscriptions (
    user_id                       INTEGER PRIMARY KEY,
    tier                          TEXT NOT NULL DEFAULT 'free',
    current_period_start          TEXT NOT NULL DEFAULT (datetime('now')),
    current_period_end            TEXT NOT NULL,
    messages_used_this_period     INTEGER NOT NULL DEFAULT 0,
    payment_provider              TEXT,
    payment_id                    TEXT,
    created_at                    TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at                    TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS ai_usage (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id           INTEGER NOT NULL,
    chat_id           INTEGER NOT NULL,
    tier              TEXT NOT NULL,
    provider          TEXT NOT NULL,
    model             TEXT,
    tokens_input      INTEGER NOT NULL DEFAULT 0,
    tokens_output     INTEGER NOT NULL DEFAULT 0,
    cost_usd_cents    INTEGER NOT NULL DEFAULT 0,
    created_at        TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_usage_user_time ON ai_usage(user_id, created_at);
CREATE INDEX IF NOT EXISTS idx_usage_time ON ai_usage(created_at);
CREATE TABLE IF NOT EXISTS payments (
    id                    INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id               INTEGER NOT NULL,
    provider              TEXT NOT NULL,
    provider_charge_id    TEXT,
    amount_stars          INTEGER,
    amount_ils_cents      INTEGER,
    tier_purchased        TEXT NOT NULL,
    status                TEXT NOT NULL,
    raw_payload           TEXT,
    created_at            TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_payments_user ON payments(user_id, created_at);
CREATE INDEX IF NOT EXISTS idx_payments_status ON payments(status);
"""
