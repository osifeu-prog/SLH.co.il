BEGIN;

ALTER TABLE users
  ADD COLUMN IF NOT EXISTS xp_total INTEGER NOT NULL DEFAULT 0,
  ADD COLUMN IF NOT EXISTS level INTEGER NOT NULL DEFAULT 1,
  ADD COLUMN IF NOT EXISTS last_active_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP;

CREATE TABLE IF NOT EXISTS xp_events (
  id BIGSERIAL PRIMARY KEY,
  user_id BIGINT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
  event_type TEXT NOT NULL,
  xp_delta INTEGER NOT NULL,
  payload_json TEXT,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_xp_events_user_id
ON xp_events(user_id);

CREATE INDEX IF NOT EXISTS idx_xp_events_event_type
ON xp_events(event_type);

CREATE INDEX IF NOT EXISTS idx_xp_events_user_id_created_at
ON xp_events(user_id, created_at DESC);

CREATE TABLE IF NOT EXISTS daily_claims (
  user_id BIGINT PRIMARY KEY REFERENCES users(user_id) ON DELETE CASCADE,
  streak INTEGER NOT NULL DEFAULT 0,
  last_claim_at TIMESTAMP,
  last_reward NUMERIC(18,8) NOT NULL DEFAULT 0,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO audit_log (user_id, event_type, payload_json)
VALUES (
  NULL,
  'schema.migration.005_xp_daily_foundation',
  '{"ok":true,"adds":["users.xp_total","users.level","users.last_active_at","xp_events","daily_claims"]}'
);

COMMIT;