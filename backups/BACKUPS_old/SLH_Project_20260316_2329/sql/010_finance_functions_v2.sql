BEGIN;

CREATE OR REPLACE FUNCTION finance_post_user_reward(
  p_ref_key TEXT,
  p_user_id BIGINT,
  p_amount NUMERIC,
  p_txn_type TEXT,
  p_description TEXT,
  p_source_table TEXT DEFAULT NULL,
  p_source_id BIGINT DEFAULT NULL,
  p_metadata_json TEXT DEFAULT NULL
)
RETURNS BIGINT
LANGUAGE plpgsql
AS $$
DECLARE
  v_txn_id BIGINT;
  v_avail_account_id BIGINT;
  v_treasury_account_id BIGINT;
BEGIN
  IF p_amount IS NULL OR p_amount <= 0 THEN
    RAISE EXCEPTION 'finance_post_user_reward amount must be > 0';
  END IF;

  SELECT id INTO v_txn_id
  FROM ledger_txns
  WHERE ref_key = p_ref_key;

  IF v_txn_id IS NOT NULL THEN
    RETURN v_txn_id;
  END IF;

  INSERT INTO ledger_txns(ref_key, txn_type, status, description, source_table, source_id, posted_at)
  VALUES (p_ref_key, p_txn_type, 'posted', p_description, p_source_table, p_source_id, NOW())
  RETURNING id INTO v_txn_id;

  SELECT id INTO v_treasury_account_id
  FROM ledger_accounts
  WHERE code = 'TREASURY_AVAILABLE';

  SELECT id INTO v_avail_account_id
  FROM ledger_accounts
  WHERE code = 'USR_AVAIL_' || p_user_id::text;

  IF v_treasury_account_id IS NULL OR v_avail_account_id IS NULL THEN
    RAISE EXCEPTION 'finance_post_user_reward missing ledger account(s) for user %', p_user_id;
  END IF;

  INSERT INTO ledger_entries(txn_id, line_no, account_id, entry_side, amount, asset_code, user_id, metadata_json)
  VALUES
    (v_txn_id, 1, v_treasury_account_id, 'debit',  p_amount, 'SLH', p_user_id, p_metadata_json),
    (v_txn_id, 2, v_avail_account_id,    'credit', p_amount, 'SLH', p_user_id, p_metadata_json);

  UPDATE user_balances
  SET available = available + p_amount,
      updated_at = NOW()
  WHERE user_id = p_user_id;

  RETURN v_txn_id;
END;
$$;

CREATE OR REPLACE FUNCTION finance_reject_withdrawal_release(
  p_withdrawal_id BIGINT,
  p_reason TEXT DEFAULT NULL
)
RETURNS BIGINT
LANGUAGE plpgsql
AS $$
DECLARE
  v_user_id BIGINT;
  v_amount NUMERIC;
  v_status TEXT;
  v_txn_id BIGINT;
  v_ref_key TEXT;
  v_user_avail_id BIGINT;
  v_user_lock_id BIGINT;
  v_treasury_avail_id BIGINT;
  v_treasury_lock_id BIGINT;
BEGIN
  SELECT user_id, amount, status
    INTO v_user_id, v_amount, v_status
  FROM withdrawals
  WHERE id = p_withdrawal_id;

  IF NOT FOUND THEN
    RAISE EXCEPTION 'withdrawal % not found', p_withdrawal_id;
  END IF;

  IF v_status <> 'approved' THEN
    RAISE EXCEPTION 'withdrawal % must be approved to release; current status=%', p_withdrawal_id, v_status;
  END IF;

  v_ref_key := 'withdrawal:release:' || p_withdrawal_id::text || ':v1';

  SELECT id INTO v_txn_id
  FROM ledger_txns
  WHERE ref_key = v_ref_key;

  IF v_txn_id IS NULL THEN
    INSERT INTO ledger_txns(ref_key, txn_type, status, description, source_table, source_id, posted_at)
    VALUES (v_ref_key, 'withdrawal_release', 'posted', 'Release approved withdrawal back to available', 'withdrawals', p_withdrawal_id, NOW())
    RETURNING id INTO v_txn_id;

    SELECT id INTO v_treasury_avail_id FROM ledger_accounts WHERE code = 'TREASURY_AVAILABLE';
    SELECT id INTO v_treasury_lock_id  FROM ledger_accounts WHERE code = 'TREASURY_LOCKED';
    SELECT id INTO v_user_avail_id     FROM ledger_accounts WHERE code = 'USR_AVAIL_' || v_user_id::text;
    SELECT id INTO v_user_lock_id      FROM ledger_accounts WHERE code = 'USR_LOCK_'  || v_user_id::text;

    INSERT INTO ledger_entries(txn_id, line_no, account_id, entry_side, amount, asset_code, user_id, metadata_json)
    VALUES
      (v_txn_id, 1, v_treasury_avail_id, 'debit',  v_amount, 'SLH', v_user_id, '{"kind":"withdrawal_release"}'),
      (v_txn_id, 2, v_treasury_lock_id,  'credit', v_amount, 'SLH', v_user_id, '{"kind":"withdrawal_release"}'),
      (v_txn_id, 3, v_user_avail_id,     'credit', v_amount, 'SLH', v_user_id, '{"kind":"withdrawal_release"}'),
      (v_txn_id, 4, v_user_lock_id,      'debit',  v_amount, 'SLH', v_user_id, '{"kind":"withdrawal_release"}');

    UPDATE user_balances
    SET available = available + v_amount,
        locked = locked - v_amount,
        updated_at = NOW()
    WHERE user_id = v_user_id
      AND locked >= v_amount;

    UPDATE withdrawal_reservations
    SET status = 'released',
        updated_at = NOW()
    WHERE withdrawal_id = p_withdrawal_id
      AND status = 'reserved';
  END IF;

  UPDATE withdrawals
  SET status = 'rejected',
      reviewed_at = COALESCE(reviewed_at, NOW()),
      reject_reason = COALESCE(p_reason, reject_reason)
  WHERE id = p_withdrawal_id;

  INSERT INTO audit_log(user_id, event_type, payload_json, created_at)
  SELECT
    v_user_id,
    'finance.withdrawal_released',
    '{"withdrawal_id":' || p_withdrawal_id::text || ',"amount":' || v_amount::text || ',"status":"released"}',
    NOW()
  WHERE NOT EXISTS (
    SELECT 1
    FROM audit_log
    WHERE event_type = 'finance.withdrawal_released'
      AND payload_json LIKE '%"withdrawal_id":' || p_withdrawal_id::text || '%'
  );

  RETURN v_txn_id;
END;
$$;

CREATE OR REPLACE FUNCTION finance_mark_withdrawal_sent_consume(
  p_withdrawal_id BIGINT,
  p_tx_hash TEXT
)
RETURNS BIGINT
LANGUAGE plpgsql
AS $$
DECLARE
  v_user_id BIGINT;
  v_amount NUMERIC;
  v_status TEXT;
  v_txn_id BIGINT;
  v_ref_key TEXT;
  v_user_lock_id BIGINT;
  v_clearing_id BIGINT;
  v_treasury_lock_id BIGINT;
BEGIN
  SELECT user_id, amount, status
    INTO v_user_id, v_amount, v_status
  FROM withdrawals
  WHERE id = p_withdrawal_id;

  IF NOT FOUND THEN
    RAISE EXCEPTION 'withdrawal % not found', p_withdrawal_id;
  END IF;

  IF v_status <> 'approved' THEN
    RAISE EXCEPTION 'withdrawal % must be approved to send; current status=%', p_withdrawal_id, v_status;
  END IF;

  IF p_tx_hash IS NULL OR btrim(p_tx_hash) = '' THEN
    RAISE EXCEPTION 'tx hash required';
  END IF;

  v_ref_key := 'withdrawal:consume:' || p_withdrawal_id::text || ':v1';

  SELECT id INTO v_txn_id
  FROM ledger_txns
  WHERE ref_key = v_ref_key;

  IF v_txn_id IS NULL THEN
    INSERT INTO ledger_txns(ref_key, txn_type, status, description, source_table, source_id, posted_at)
    VALUES (v_ref_key, 'withdrawal_consume', 'posted', 'Consume reserved withdrawal and mark sent', 'withdrawals', p_withdrawal_id, NOW())
    RETURNING id INTO v_txn_id;

    SELECT id INTO v_treasury_lock_id FROM ledger_accounts WHERE code = 'TREASURY_LOCKED';
    SELECT id INTO v_clearing_id      FROM ledger_accounts WHERE code = 'WITHDRAWAL_CLEARING';
    SELECT id INTO v_user_lock_id     FROM ledger_accounts WHERE code = 'USR_LOCK_' || v_user_id::text;

    INSERT INTO ledger_entries(txn_id, line_no, account_id, entry_side, amount, asset_code, user_id, metadata_json)
    VALUES
      (v_txn_id, 1, v_clearing_id,      'debit',  v_amount, 'SLH', v_user_id, '{"kind":"withdrawal_consume"}'),
      (v_txn_id, 2, v_treasury_lock_id, 'credit', v_amount, 'SLH', v_user_id, '{"kind":"withdrawal_consume"}'),
      (v_txn_id, 3, v_user_lock_id,     'debit',  v_amount, 'SLH', v_user_id, '{"kind":"withdrawal_consume"}');

    UPDATE user_balances
    SET locked = locked - v_amount,
        updated_at = NOW()
    WHERE user_id = v_user_id
      AND locked >= v_amount;

    UPDATE withdrawal_reservations
    SET status = 'consumed',
        updated_at = NOW()
    WHERE withdrawal_id = p_withdrawal_id
      AND status = 'reserved';
  END IF;

  UPDATE withdrawals
  SET status = 'sent',
      processed_at = COALESCE(processed_at, NOW()),
      reviewed_at = COALESCE(reviewed_at, NOW()),
      tx_hash = COALESCE(NULLIF(p_tx_hash,''), tx_hash)
  WHERE id = p_withdrawal_id;

  INSERT INTO audit_log(user_id, event_type, payload_json, created_at)
  SELECT
    v_user_id,
    'finance.withdrawal_consumed',
    '{"withdrawal_id":' || p_withdrawal_id::text || ',"amount":' || v_amount::text || ',"status":"consumed","tx_hash":"' || replace(p_tx_hash,'"','\"') || '"}',
    NOW()
  WHERE NOT EXISTS (
    SELECT 1
    FROM audit_log
    WHERE event_type = 'finance.withdrawal_consumed'
      AND payload_json LIKE '%"withdrawal_id":' || p_withdrawal_id::text || '%'
  );

  RETURN v_txn_id;
END;
$$;

CREATE OR REPLACE FUNCTION trg_withdrawals_wallet_sanitize()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
  IF NEW.wallet IS NOT NULL THEN
    NEW.wallet := regexp_replace(NEW.wallet, E'[\\r\\n\\t]+', ' ', 'g');
    NEW.wallet := btrim(NEW.wallet);
  END IF;

  IF NEW.wallet IS NULL OR NEW.wallet = '' THEN
    RAISE EXCEPTION 'wallet is required';
  END IF;

  IF NEW.wallet ~ '[[:space:]]' THEN
    RAISE EXCEPTION 'wallet must not contain whitespace';
  END IF;

  IF NEW.wallet ~ '/' THEN
    RAISE EXCEPTION 'wallet contains illegal character "/"';
  END IF;

  IF length(NEW.wallet) < 5 OR length(NEW.wallet) > 128 THEN
    RAISE EXCEPTION 'wallet length out of range';
  END IF;

  RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_withdrawals_wallet_sanitize ON withdrawals;
CREATE TRIGGER trg_withdrawals_wallet_sanitize
BEFORE INSERT OR UPDATE OF wallet ON withdrawals
FOR EACH ROW
EXECUTE FUNCTION trg_withdrawals_wallet_sanitize();

CREATE OR REPLACE VIEW v_ledger_balance_by_account AS
SELECT
  la.code,
  la.owner_user_id,
  la.account_type,
  la.normal_side,
  COALESCE(SUM(
    CASE
      WHEN la.normal_side = 'debit'  AND le.entry_side = 'debit'  THEN le.amount
      WHEN la.normal_side = 'debit'  AND le.entry_side = 'credit' THEN -le.amount
      WHEN la.normal_side = 'credit' AND le.entry_side = 'credit' THEN le.amount
      WHEN la.normal_side = 'credit' AND le.entry_side = 'debit'  THEN -le.amount
      ELSE 0
    END
  ),0) AS balance
FROM ledger_accounts la
LEFT JOIN ledger_entries le ON le.account_id = la.id
GROUP BY la.code, la.owner_user_id, la.account_type, la.normal_side;

CREATE OR REPLACE VIEW v_user_finance_snapshot AS
SELECT
  u.user_id,
  u.username,
  COALESCE(ub.available,0) AS available,
  COALESCE(ub.locked,0) AS locked,
  COALESCE(va.balance,0) AS ledger_available,
  COALESCE(vl.balance,0) AS ledger_locked,
  COALESCE(ub.available,0) - COALESCE(va.balance,0) AS delta_available,
  COALESCE(ub.locked,0) - COALESCE(vl.balance,0) AS delta_locked
FROM users u
LEFT JOIN user_balances ub ON ub.user_id = u.user_id
LEFT JOIN v_ledger_balance_by_account va ON va.code = 'USR_AVAIL_' || u.user_id::text
LEFT JOIN v_ledger_balance_by_account vl ON vl.code = 'USR_LOCK_'  || u.user_id::text;

INSERT INTO audit_log(user_id, event_type, payload_json, created_at)
SELECT
  NULL,
  'schema.finance_functions.v2',
  '{"ok":true,"objects":["finance_post_user_reward","finance_reject_withdrawal_release","finance_mark_withdrawal_sent_consume","trg_withdrawals_wallet_sanitize","v_ledger_balance_by_account","v_user_finance_snapshot"]}',
  NOW()
WHERE NOT EXISTS (
  SELECT 1 FROM audit_log WHERE event_type='schema.finance_functions.v2'
);

COMMIT;