BEGIN;

CREATE TABLE IF NOT EXISTS audit_log (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NULL,
    event_type TEXT NOT NULL,
    payload_json JSONB,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_audit_log_event_type_created_at
ON audit_log(event_type, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_audit_log_user_id_created_at
ON audit_log(user_id, created_at DESC);

COMMIT;