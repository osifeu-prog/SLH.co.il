BEGIN;

ALTER TABLE users
    ADD COLUMN IF NOT EXISTS role TEXT DEFAULT 'user';

ALTER TABLE users
    ADD COLUMN IF NOT EXISTS balance DOUBLE PRECISION DEFAULT 0;

ALTER TABLE users
    ADD COLUMN IF NOT EXISTS last_claim TIMESTAMP DEFAULT TIMESTAMP '1970-01-01 00:00:00';

ALTER TABLE users
    ADD COLUMN IF NOT EXISTS invited_count INTEGER DEFAULT 0;

ALTER TABLE users
    ADD COLUMN IF NOT EXISTS total_sold NUMERIC DEFAULT 0;

ALTER TABLE users
    ADD COLUMN IF NOT EXISTS joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;

CREATE TABLE IF NOT EXISTS tasks (
    id SERIAL PRIMARY KEY,
    title TEXT,
    reward NUMERIC,
    type TEXT
);

CREATE TABLE IF NOT EXISTS sell_orders (
    id SERIAL PRIMARY KEY,
    user_id BIGINT,
    amount NUMERIC,
    status TEXT DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT now()
);

CREATE TABLE IF NOT EXISTS withdrawals (
    id SERIAL PRIMARY KEY,
    user_id BIGINT,
    amount NUMERIC,
    wallet TEXT,
    status TEXT DEFAULT 'pending'
);

CREATE TABLE IF NOT EXISTS blacklist (
    id SERIAL PRIMARY KEY,
    pattern TEXT UNIQUE,
    type TEXT,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_audit_log_created_at
    ON audit_log(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_audit_log_user_id_created_at
    ON audit_log(user_id, created_at DESC);

UPDATE users SET invited_count = 0 WHERE invited_count IS NULL;
UPDATE users SET total_sold = 0 WHERE total_sold IS NULL;
UPDATE users SET balance = 0 WHERE balance IS NULL;
UPDATE users SET joined_at = CURRENT_TIMESTAMP WHERE joined_at IS NULL;
UPDATE users SET last_claim = TIMESTAMP '1970-01-01 00:00:00' WHERE last_claim IS NULL;

INSERT INTO user_balances (user_id, available, locked, updated_at)
SELECT u.user_id, COALESCE(u.balance, 0)::numeric(18,8), 0, CURRENT_TIMESTAMP
FROM users u
LEFT JOIN user_balances ub ON ub.user_id = u.user_id
WHERE ub.user_id IS NULL;

INSERT INTO audit_log (user_id, event_type, payload_json)
VALUES (NULL, 'schema.v2.finalized', '{"source":"003_schema_v2_finalize.sql"}');

COMMIT;