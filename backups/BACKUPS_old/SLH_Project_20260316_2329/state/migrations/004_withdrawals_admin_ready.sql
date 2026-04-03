BEGIN;

ALTER TABLE withdrawals
    ADD COLUMN IF NOT EXISTS created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP;

ALTER TABLE withdrawals
    ADD COLUMN IF NOT EXISTS reviewed_at TIMESTAMP NULL;

ALTER TABLE withdrawals
    ADD COLUMN IF NOT EXISTS reviewed_by BIGINT NULL;

ALTER TABLE withdrawals
    ADD COLUMN IF NOT EXISTS reject_reason TEXT NULL;

ALTER TABLE withdrawals
    ADD COLUMN IF NOT EXISTS approved_at TIMESTAMP NULL;

ALTER TABLE withdrawals
    ADD COLUMN IF NOT EXISTS processed_at TIMESTAMP NULL;

ALTER TABLE withdrawals
    ADD COLUMN IF NOT EXISTS tx_hash TEXT NULL;

ALTER TABLE withdrawals
    ADD COLUMN IF NOT EXISTS error_message TEXT NULL;

CREATE INDEX IF NOT EXISTS idx_withdrawals_status_id
    ON withdrawals(status, id DESC);

CREATE INDEX IF NOT EXISTS idx_withdrawals_user_id_id
    ON withdrawals(user_id, id DESC);

INSERT INTO audit_log (user_id, event_type, payload_json)
VALUES (NULL, 'schema.withdrawals.extended', '{"table":"withdrawals"}');

COMMIT;