CREATE TABLE IF NOT EXISTS feature_flags (
  id BIGSERIAL PRIMARY KEY,
  key TEXT UNIQUE NOT NULL,
  enabled BOOLEAN NOT NULL DEFAULT false,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

INSERT INTO feature_flags(key, enabled)
VALUES ('AIRDROP_ENABLED', true)
ON CONFLICT (key) DO UPDATE
SET enabled = EXCLUDED.enabled, updated_at = NOW();

SELECT key, enabled, updated_at
FROM feature_flags
WHERE key='AIRDROP_ENABLED';
