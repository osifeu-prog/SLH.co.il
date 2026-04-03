BEGIN;

CREATE OR REPLACE FUNCTION trg_sync_users_balance_from_user_balances()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
  UPDATE users
  SET balance = NEW.available
  WHERE user_id = NEW.user_id;
  RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_user_balances_sync_users_balance ON user_balances;
CREATE TRIGGER trg_user_balances_sync_users_balance
AFTER INSERT OR UPDATE OF available ON user_balances
FOR EACH ROW
EXECUTE FUNCTION trg_sync_users_balance_from_user_balances();

INSERT INTO finance_idempotency_keys (idem_key, operation, resource_type, resource_id)
VALUES
  ('backfill:withdrawal_reservation:1:v1', 'withdrawal_reservation_backfill', 'withdrawals', 1)
ON CONFLICT (idem_key) DO NOTHING;

INSERT INTO withdrawal_reservations (withdrawal_id, user_id, amount, status, created_at, updated_at)
SELECT
  w.id,
  w.user_id,
  w.amount,
  'reserved',
  NOW(),
  NOW()
FROM withdrawals w
WHERE w.id = 1
  AND w.status = 'approved'
  AND NOT EXISTS (
    SELECT 1 FROM withdrawal_reservations r WHERE r.withdrawal_id = w.id
  );

INSERT INTO ledger_txns (ref_key, txn_type, status, description, source_table, source_id, posted_at)
SELECT
  'withdrawal:reserve:' || w.id::text || ':v1',
  'withdrawal_reserve',
  'posted',
  'Reserve approved withdrawal from available to locked',
  'withdrawals',
  w.id,
  NOW()
FROM withdrawals w
WHERE w.id = 1
  AND w.status = 'approved'
ON CONFLICT (ref_key) DO NOTHING;

INSERT INTO ledger_entries (txn_id, line_no, account_id, entry_side, amount, asset_code, user_id, metadata_json)
SELECT
  tx.id,
  1,
  a.id,
  'debit',
  w.amount,
  'SLH',
  w.user_id,
  '{"kind":"withdrawal_reserve","bucket":"treasury_locked"}'
FROM ledger_txns tx
JOIN withdrawals w ON tx.ref_key = 'withdrawal:reserve:' || w.id::text || ':v1'
JOIN ledger_accounts a ON a.code = 'TREASURY_LOCKED'
ON CONFLICT (txn_id, line_no) DO NOTHING;

INSERT INTO ledger_entries (txn_id, line_no, account_id, entry_side, amount, asset_code, user_id, metadata_json)
SELECT
  tx.id,
  2,
  a.id,
  'credit',
  w.amount,
  'SLH',
  w.user_id,
  '{"kind":"withdrawal_reserve","bucket":"treasury_available"}'
FROM ledger_txns tx
JOIN withdrawals w ON tx.ref_key = 'withdrawal:reserve:' || w.id::text || ':v1'
JOIN ledger_accounts a ON a.code = 'TREASURY_AVAILABLE'
ON CONFLICT (txn_id, line_no) DO NOTHING;

INSERT INTO ledger_entries (txn_id, line_no, account_id, entry_side, amount, asset_code, user_id, metadata_json)
SELECT
  tx.id,
  3,
  a.id,
  'debit',
  w.amount,
  'SLH',
  w.user_id,
  '{"kind":"withdrawal_reserve","bucket":"user_available"}'
FROM ledger_txns tx
JOIN withdrawals w ON tx.ref_key = 'withdrawal:reserve:' || w.id::text || ':v1'
JOIN ledger_accounts a ON a.code = 'USR_AVAIL_' || w.user_id::text
ON CONFLICT (txn_id, line_no) DO NOTHING;

INSERT INTO ledger_entries (txn_id, line_no, account_id, entry_side, amount, asset_code, user_id, metadata_json)
SELECT
  tx.id,
  4,
  a.id,
  'credit',
  w.amount,
  'SLH',
  w.user_id,
  '{"kind":"withdrawal_reserve","bucket":"user_locked"}'
FROM ledger_txns tx
JOIN withdrawals w ON tx.ref_key = 'withdrawal:reserve:' || w.id::text || ':v1'
JOIN ledger_accounts a ON a.code = 'USR_LOCK_' || w.user_id::text
ON CONFLICT (txn_id, line_no) DO NOTHING;

UPDATE user_balances ub
SET
  available = ub.available - w.amount,
  locked = ub.locked + w.amount,
  updated_at = NOW()
FROM withdrawals w
WHERE w.id = 1
  AND w.status = 'approved'
  AND ub.user_id = w.user_id
  AND EXISTS (
    SELECT 1 FROM withdrawal_reservations r
    WHERE r.withdrawal_id = w.id
      AND r.status = 'reserved'
  )
  AND ub.available >= w.amount
  AND ub.locked = 0;

INSERT INTO audit_log(user_id, event_type, payload_json, created_at)
SELECT
  w.user_id,
  'finance.withdrawal_reservation_backfilled',
  '{"withdrawal_id":1,"amount":1.0,"status":"reserved"}',
  NOW()
FROM withdrawals w
WHERE w.id = 1
  AND NOT EXISTS (
    SELECT 1
    FROM audit_log a
    WHERE a.event_type = 'finance.withdrawal_reservation_backfilled'
      AND a.payload_json LIKE '%"withdrawal_id":1%'
  );

COMMIT;