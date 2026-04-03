BEGIN;

-- 1) Core tables safety

CREATE TABLE IF NOT EXISTS users (
    user_id BIGINT PRIMARY KEY,
    username TEXT,
    role TEXT DEFAULT 'user',
    balance DOUBLE PRECISION DEFAULT 0,
    last_claim TIMESTAMP DEFAULT TIMESTAMP '1970-01-01 00:00:00',
    invited_count INTEGER DEFAULT 0,
    total_sold NUMERIC DEFAULT 0,
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS user_balances (
    user_id BIGINT PRIMARY KEY REFERENCES users(user_id) ON DELETE CASCADE,
    available NUMERIC(18,8) NOT NULL DEFAULT 0,
    locked NUMERIC(18,8) NOT NULL DEFAULT 0,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS claims (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    amount NUMERIC(18,8) NOT NULL DEFAULT 0,
    claim_type TEXT NOT NULL DEFAULT 'daily',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS invites (
    id BIGSERIAL PRIMARY KEY,
    inviter_user_id BIGINT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    invited_user_id BIGINT NOT NULL UNIQUE REFERENCES users(user_id) ON DELETE CASCADE,
    invite_code TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    reward_granted BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS tasks (
    id SERIAL PRIMARY KEY,
    title TEXT,
    reward NUMERIC,
    type TEXT
);

CREATE TABLE IF NOT EXISTS audit_log (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT,
    event_type TEXT NOT NULL,
    payload_json TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 2) Indexes

CREATE INDEX IF NOT EXISTS idx_claims_user_id_created_at
ON claims(user_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_invites_inviter_user_id
ON invites(inviter_user_id);

CREATE INDEX IF NOT EXISTS idx_audit_log_event_type
ON audit_log(event_type);

CREATE INDEX IF NOT EXISTS idx_audit_log_user_id
ON audit_log(user_id);

CREATE INDEX IF NOT EXISTS idx_audit_log_created_at
ON audit_log(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_audit_log_user_id_created_at
ON audit_log(user_id, created_at DESC);

-- 3) Backfill user_balances from legacy users.balance where needed
INSERT INTO user_balances (user_id, available, locked, updated_at)
SELECT
    u.user_id,
    COALESCE(u.balance, 0)::numeric(18,8),
    0,
    CURRENT_TIMESTAMP
FROM users u
LEFT JOIN user_balances ub ON ub.user_id = u.user_id
WHERE ub.user_id IS NULL;

-- 4) Normalize NULLs
UPDATE users
SET invited_count = 0
WHERE invited_count IS NULL;

UPDATE users
SET total_sold = 0
WHERE total_sold IS NULL;

UPDATE users
SET balance = 0
WHERE balance IS NULL;

-- 5) Mark source of truth in audit
INSERT INTO audit_log (user_id, event_type, payload_json)
VALUES (NULL, 'schema.repair', '{"note":"user_balances is source of truth; users.balance kept for compatibility"}');

COMMIT;