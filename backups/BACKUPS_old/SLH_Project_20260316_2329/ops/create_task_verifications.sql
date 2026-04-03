BEGIN;

CREATE TABLE IF NOT EXISTS task_verifications (
  user_id      BIGINT    NOT NULL,
  task_id      INTEGER   NOT NULL,
  status       TEXT      NOT NULL DEFAULT 'pending',
  requested_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  reviewed_at  TIMESTAMP NULL,
  reviewed_by  BIGINT    NULL,
  review_note  TEXT      NULL,
  PRIMARY KEY (user_id, task_id),
  CHECK (status IN ('pending', 'approved', 'rejected'))
);

CREATE INDEX IF NOT EXISTS idx_task_verifications_status_requested_at
  ON task_verifications (status, requested_at);

CREATE INDEX IF NOT EXISTS idx_task_verifications_reviewed_by
  ON task_verifications (reviewed_by);

COMMIT;