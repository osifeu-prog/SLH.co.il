BEGIN;

CREATE TABLE IF NOT EXISTS ledger_accounts (
  id BIGSERIAL PRIMARY KEY,
  code TEXT NOT NULL UNIQUE,
  owner_user_id BIGINT NULL,
  asset_code TEXT NOT NULL DEFAULT 'SLH',
  account_type TEXT NOT NULL,
  normal_side TEXT NOT NULL CHECK (normal_side IN ('debit','credit')),
  status TEXT NOT NULL DEFAULT 'active',
  created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS ledger_txns (
  id BIGSERIAL PRIMARY KEY,
  ref_key TEXT NOT NULL UNIQUE,
  txn_type TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'posted',
  description TEXT NOT NULL DEFAULT '',
  source_table TEXT NULL,
  source_id BIGINT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT NOW(),
  posted_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS ledger_entries (
  id BIGSERIAL PRIMARY KEY,
  txn_id BIGINT NOT NULL REFERENCES ledger_txns(id) ON DELETE CASCADE,
  line_no INTEGER NOT NULL,
  account_id BIGINT NOT NULL REFERENCES ledger_accounts(id),
  entry_side TEXT NOT NULL CHECK (entry_side IN ('debit','credit')),
  amount NUMERIC(20,8) NOT NULL CHECK (amount > 0),
  asset_code TEXT NOT NULL DEFAULT 'SLH',
  user_id BIGINT NULL,
  metadata_json TEXT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT NOW(),
  CONSTRAINT uq_ledger_entries_txn_line UNIQUE (txn_id, line_no)
);

CREATE TABLE IF NOT EXISTS finance_idempotency_keys (
  id BIGSERIAL PRIMARY KEY,
  idem_key TEXT NOT NULL UNIQUE,
  operation TEXT NOT NULL,
  resource_type TEXT NULL,
  resource_id BIGINT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS withdrawal_reservations (
  withdrawal_id INTEGER PRIMARY KEY REFERENCES withdrawals(id) ON DELETE CASCADE,
  user_id BIGINT NOT NULL,
  amount NUMERIC(20,8) NOT NULL CHECK (amount > 0),
  status TEXT NOT NULL CHECK (status IN ('reserved','released','consumed')),
  created_at TIMESTAMP NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_ledger_accounts_owner_user_id ON ledger_accounts(owner_user_id);
CREATE INDEX IF NOT EXISTS idx_ledger_txns_txn_type ON ledger_txns(txn_type);
CREATE INDEX IF NOT EXISTS idx_ledger_entries_txn_id ON ledger_entries(txn_id);
CREATE INDEX IF NOT EXISTS idx_ledger_entries_account_id ON ledger_entries(account_id);
CREATE INDEX IF NOT EXISTS idx_ledger_entries_user_id ON ledger_entries(user_id);
CREATE INDEX IF NOT EXISTS idx_finance_idempotency_keys_operation ON finance_idempotency_keys(operation);

INSERT INTO ledger_accounts (code, owner_user_id, account_type, normal_side)
VALUES
  ('TREASURY_AVAILABLE', NULL, 'treasury_asset', 'debit'),
  ('TREASURY_LOCKED', NULL, 'treasury_asset_locked', 'debit'),
  ('WITHDRAWAL_CLEARING', NULL, 'clearing', 'debit')
ON CONFLICT (code) DO NOTHING;

INSERT INTO ledger_accounts (code, owner_user_id, account_type, normal_side)
SELECT
  'USR_AVAIL_' || user_id::text,
  user_id,
  'user_liability_available',
  'credit'
FROM users
ON CONFLICT (code) DO NOTHING;

INSERT INTO ledger_accounts (code, owner_user_id, account_type, normal_side)
SELECT
  'USR_LOCK_' || user_id::text,
  user_id,
  'user_liability_locked',
  'credit'
FROM users
ON CONFLICT (code) DO NOTHING;

INSERT INTO audit_log(user_id, event_type, payload_json, created_at)
SELECT
  NULL,
  'schema.economic_core.v1',
  '{"ok":true,"tables":["ledger_accounts","ledger_txns","ledger_entries","finance_idempotency_keys","withdrawal_reservations"]}',
  NOW()
WHERE NOT EXISTS (
  SELECT 1
  FROM audit_log
  WHERE event_type = 'schema.economic_core.v1'
);

COMMIT;