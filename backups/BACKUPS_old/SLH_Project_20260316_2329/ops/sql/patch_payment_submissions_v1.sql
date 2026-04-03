CREATE TABLE IF NOT EXISTS purchase_payment_submissions (
    id BIGSERIAL PRIMARY KEY,
    order_id BIGINT NOT NULL,
    submitted_by_user_id BIGINT NOT NULL,
    submitted_ref TEXT,
    submitted_amount NUMERIC,
    submitted_currency TEXT,
    evidence_text TEXT,
    evidence_file_id TEXT,
    review_status TEXT NOT NULL DEFAULT 'pending',
    reviewed_by_user_id BIGINT,
    reviewed_at TIMESTAMP,
    review_notes TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_payment_submissions_order
ON purchase_payment_submissions(order_id);

CREATE INDEX IF NOT EXISTS idx_payment_submissions_status
ON purchase_payment_submissions(review_status);