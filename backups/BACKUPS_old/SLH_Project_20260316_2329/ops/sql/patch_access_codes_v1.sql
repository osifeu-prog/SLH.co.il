CREATE TABLE IF NOT EXISTS access_codes (
    id BIGSERIAL PRIMARY KEY,
    code TEXT NOT NULL UNIQUE,
    grant_type TEXT NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    max_uses INTEGER,
    used_count INTEGER NOT NULL DEFAULT 0,
    notes TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMP NULL
);

CREATE TABLE IF NOT EXISTS access_code_redemptions (
    id BIGSERIAL PRIMARY KEY,
    code TEXT NOT NULL,
    user_id BIGINT NOT NULL,
    username TEXT,
    result_status TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

INSERT INTO access_codes (code, grant_type, is_active, max_uses, notes)
VALUES
('TEST100', 'full_access', TRUE, NULL, 'grant paid-like access for testers'),
('TESTVIP', 'full_access', TRUE, NULL, 'grant VIP access immediately'),
('TESTPENDING', 'pending_only', TRUE, NULL, 'simulate pending payment request'),
('TESTREJECT', 'reject_only', TRUE, NULL, 'simulate rejected state')
ON CONFLICT (code) DO NOTHING;