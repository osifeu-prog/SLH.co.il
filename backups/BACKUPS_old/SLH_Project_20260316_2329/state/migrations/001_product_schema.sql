BEGIN;

CREATE TABLE IF NOT EXISTS invites (
    id BIGSERIAL PRIMARY KEY,
    inviter_user_id BIGINT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    invited_user_id BIGINT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    invite_code TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(invited_user_id)
);

CREATE INDEX IF NOT EXISTS idx_invites_inviter_user_id
    ON invites(inviter_user_id);

CREATE TABLE IF NOT EXISTS claims (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    amount NUMERIC(18,8) NOT NULL DEFAULT 0,
    claim_type TEXT NOT NULL DEFAULT 'daily',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_claims_user_id_created_at
    ON claims(user_id, created_at DESC);

CREATE TABLE IF NOT EXISTS audit_log (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT,
    event_type TEXT NOT NULL,
    payload_json TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_audit_log_user_id
    ON audit_log(user_id);

CREATE INDEX IF NOT EXISTS idx_audit_log_event_type
    ON audit_log(event_type);

CREATE TABLE IF NOT EXISTS user_balances (
    user_id BIGINT PRIMARY KEY REFERENCES users(user_id) ON DELETE CASCADE,
    available NUMERIC(18,8) NOT NULL DEFAULT 0,
    locked NUMERIC(18,8) NOT NULL DEFAULT 0,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO user_balances (user_id, available, locked)
SELECT u.user_id, COALESCE(u.balance, 0), 0
FROM users u
ON CONFLICT (user_id) DO NOTHING;

COMMIT;