-- SLH AI Spark — Subscription tables for sessions.db (SQLite)
-- Run via subscriptions.init_db() at bot startup.
-- All timestamps are SQLite TEXT (ISO-8601 UTC) for portability.

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
    provider          TEXT NOT NULL,            -- 'anthropic' | 'groq' | 'gemini'
    model             TEXT,
    tokens_input      INTEGER NOT NULL DEFAULT 0,
    tokens_output     INTEGER NOT NULL DEFAULT 0,
    cost_usd_cents    INTEGER NOT NULL DEFAULT 0,    -- precision via cents
    created_at        TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_usage_user_time ON ai_usage(user_id, created_at);
CREATE INDEX IF NOT EXISTS idx_usage_time ON ai_usage(created_at);

CREATE TABLE IF NOT EXISTS payments (
    id                    INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id               INTEGER NOT NULL,
    provider              TEXT NOT NULL,        -- 'telegram_stars' | 'manual'
    provider_charge_id    TEXT,
    amount_stars          INTEGER,
    amount_ils_cents      INTEGER,
    tier_purchased        TEXT NOT NULL,
    status                TEXT NOT NULL,        -- 'pending' | 'completed' | 'refunded' | 'failed'
    raw_payload           TEXT,                 -- JSON
    created_at            TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_payments_user ON payments(user_id, created_at);
CREATE INDEX IF NOT EXISTS idx_payments_status ON payments(status);
