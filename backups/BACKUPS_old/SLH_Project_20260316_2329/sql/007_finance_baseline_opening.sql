BEGIN;

INSERT INTO ledger_txns (ref_key, txn_type, status, description, source_table, source_id, posted_at)
SELECT
  'baseline:user:' || ub.user_id::text || ':available:v1',
  'baseline_opening',
  'posted',
  'Opening available balance baseline from user_balances',
  'user_balances',
  ub.user_id,
  NOW()
FROM user_balances ub
WHERE ub.available > 0
ON CONFLICT (ref_key) DO NOTHING;

INSERT INTO ledger_entries (txn_id, line_no, account_id, entry_side, amount, asset_code, user_id, metadata_json)
SELECT
  tx.id,
  1,
  a.id,
  'debit',
  ub.available,
  'SLH',
  ub.user_id,
  '{"kind":"baseline_opening","bucket":"available","side":"debit_treasury"}'
FROM ledger_txns tx
JOIN user_balances ub
  ON tx.ref_key = 'baseline:user:' || ub.user_id::text || ':available:v1'
JOIN ledger_accounts a
  ON a.code = 'TREASURY_AVAILABLE'
ON CONFLICT (txn_id, line_no) DO NOTHING;

INSERT INTO ledger_entries (txn_id, line_no, account_id, entry_side, amount, asset_code, user_id, metadata_json)
SELECT
  tx.id,
  2,
  a.id,
  'credit',
  ub.available,
  'SLH',
  ub.user_id,
  '{"kind":"baseline_opening","bucket":"available","side":"credit_user_liability"}'
FROM ledger_txns tx
JOIN user_balances ub
  ON tx.ref_key = 'baseline:user:' || ub.user_id::text || ':available:v1'
JOIN ledger_accounts a
  ON a.code = 'USR_AVAIL_' || ub.user_id::text
ON CONFLICT (txn_id, line_no) DO NOTHING;

INSERT INTO ledger_txns (ref_key, txn_type, status, description, source_table, source_id, posted_at)
SELECT
  'baseline:user:' || ub.user_id::text || ':locked:v1',
  'baseline_opening_locked',
  'posted',
  'Opening locked balance baseline from user_balances',
  'user_balances',
  ub.user_id,
  NOW()
FROM user_balances ub
WHERE ub.locked > 0
ON CONFLICT (ref_key) DO NOTHING;

INSERT INTO ledger_entries (txn_id, line_no, account_id, entry_side, amount, asset_code, user_id, metadata_json)
SELECT
  tx.id,
  1,
  a.id,
  'debit',
  ub.locked,
  'SLH',
  ub.user_id,
  '{"kind":"baseline_opening","bucket":"locked","side":"debit_treasury_locked"}'
FROM ledger_txns tx
JOIN user_balances ub
  ON tx.ref_key = 'baseline:user:' || ub.user_id::text || ':locked:v1'
JOIN ledger_accounts a
  ON a.code = 'TREASURY_LOCKED'
ON CONFLICT (txn_id, line_no) DO NOTHING;

INSERT INTO ledger_entries (txn_id, line_no, account_id, entry_side, amount, asset_code, user_id, metadata_json)
SELECT
  tx.id,
  2,
  a.id,
  'credit',
  ub.locked,
  'SLH',
  ub.user_id,
  '{"kind":"baseline_opening","bucket":"locked","side":"credit_user_locked_liability"}'
FROM ledger_txns tx
JOIN user_balances ub
  ON tx.ref_key = 'baseline:user:' || ub.user_id::text || ':locked:v1'
JOIN ledger_accounts a
  ON a.code = 'USR_LOCK_' || ub.user_id::text
ON CONFLICT (txn_id, line_no) DO NOTHING;

INSERT INTO audit_log(user_id, event_type, payload_json, created_at)
SELECT
  NULL,
  'finance.baseline_opening.v1',
  '{"ok":true,"source":"user_balances","version":"v1"}',
  NOW()
WHERE NOT EXISTS (
  SELECT 1
  FROM audit_log
  WHERE event_type = 'finance.baseline_opening.v1'
);

COMMIT;