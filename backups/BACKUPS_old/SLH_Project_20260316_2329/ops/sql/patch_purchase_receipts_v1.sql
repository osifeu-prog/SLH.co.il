CREATE TABLE IF NOT EXISTS purchase_receipts (
    id BIGSERIAL PRIMARY KEY,
    order_id BIGINT NOT NULL,
    receipt_no TEXT,
    payload_json JSONB,
    sent_to_user_at TIMESTAMP,
    message_id BIGINT,
    created_at TIMESTAMP NOT NULL DEFAULT now()
);