BEGIN;

UPDATE invites
SET reward_granted = FALSE
WHERE invited_user_id = 7757102350;

UPDATE user_balances
SET available = available - 3.0,
    updated_at = CURRENT_TIMESTAMP
WHERE user_id = 224223270;

UPDATE users
SET balance = COALESCE(balance, 0) - 3.0
WHERE user_id = 224223270;

DELETE FROM audit_log
WHERE event_type = 'invite.reward_granted'
  AND user_id = 224223270
  AND payload_json LIKE '%"invited_user_id":7757102350%';

DELETE FROM xp_events
WHERE event_type = 'xp.referral_reward'
  AND user_id = 224223270
  AND payload_json LIKE '%"invited_user_id":7757102350%';

WITH last_daily AS (
  SELECT COALESCE(last_reward, 0)::numeric(18,8) AS reward
  FROM daily_claims
  WHERE user_id = 7757102350
)
UPDATE user_balances
SET available = available - COALESCE((SELECT reward FROM last_daily), 0),
    updated_at = CURRENT_TIMESTAMP
WHERE user_id = 7757102350;

WITH last_daily AS (
  SELECT COALESCE(last_reward, 0)::double precision AS reward
  FROM daily_claims
  WHERE user_id = 7757102350
)
UPDATE users
SET balance = COALESCE(balance, 0) - COALESCE((SELECT reward FROM last_daily), 0),
    last_claim = TIMESTAMP '1970-01-01 00:00:00'
WHERE user_id = 7757102350;

DELETE FROM claims
WHERE user_id = 7757102350
  AND claim_type = 'daily';

DELETE FROM xp_events
WHERE user_id = 7757102350
  AND event_type = 'xp.daily_claim';

DELETE FROM daily_claims
WHERE user_id = 7757102350;

COMMIT;