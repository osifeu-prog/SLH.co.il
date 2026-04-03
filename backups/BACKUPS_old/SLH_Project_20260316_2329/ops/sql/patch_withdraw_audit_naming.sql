CREATE OR REPLACE FUNCTION public.finance_approve_withdrawal_reserve(
    p_withdrawal_id bigint,
    p_admin_user_id bigint
)
RETURNS bigint
LANGUAGE plpgsql
AS $function$
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
  v_available NUMERIC;
BEGIN
  SELECT user_id, amount, status
    INTO v_user_id, v_amount, v_status
  FROM withdrawals
  WHERE id = p_withdrawal_id
  FOR UPDATE;

  IF NOT FOUND THEN
    RAISE EXCEPTION 'withdrawal % not found', p_withdrawal_id;
  END IF;

  IF v_status <> 'pending' THEN
    RAISE EXCEPTION 'withdrawal % must be pending to approve; current status=%', p_withdrawal_id, v_status;
  END IF;

  INSERT INTO user_balances (user_id, available, locked)
  VALUES (v_user_id, 0, 0)
  ON CONFLICT (user_id) DO NOTHING;

  SELECT available
    INTO v_available
  FROM user_balances
  WHERE user_id = v_user_id
  FOR UPDATE;

  IF COALESCE(v_available, 0) < v_amount THEN
    RAISE EXCEPTION 'insufficient available balance for withdrawal %, user %', p_withdrawal_id, v_user_id;
  END IF;

  v_ref_key := 'withdrawal:reserve:' || p_withdrawal_id::text || ':v1';

  SELECT id INTO v_txn_id
  FROM ledger_txns
  WHERE ref_key = v_ref_key;

  IF v_txn_id IS NULL THEN
    INSERT INTO ledger_txns(ref_key, txn_type, status, description, source_table, source_id, posted_at)
    VALUES (
      v_ref_key,
      'withdrawal_reserve',
      'posted',
      'Reserve approved withdrawal from available to locked',
      'withdrawals',
      p_withdrawal_id,
      NOW()
    )
    RETURNING id INTO v_txn_id;

    SELECT id INTO v_treasury_lock_id  FROM ledger_accounts WHERE code = 'TREASURY_LOCKED';
    SELECT id INTO v_treasury_avail_id FROM ledger_accounts WHERE code = 'TREASURY_AVAILABLE';
    SELECT id INTO v_user_avail_id     FROM ledger_accounts WHERE code = 'USR_AVAIL_' || v_user_id::text;
    SELECT id INTO v_user_lock_id      FROM ledger_accounts WHERE code = 'USR_LOCK_'  || v_user_id::text;

    INSERT INTO ledger_entries(txn_id, line_no, account_id, entry_side, amount, asset_code, user_id, metadata_json)
    VALUES
      (v_txn_id, 1, v_treasury_lock_id,  'debit',  v_amount, 'SLH', v_user_id, '{"kind":"withdrawal_reserve"}'),
      (v_txn_id, 2, v_treasury_avail_id, 'credit', v_amount, 'SLH', v_user_id, '{"kind":"withdrawal_reserve"}'),
      (v_txn_id, 3, v_user_avail_id,     'debit',  v_amount, 'SLH', v_user_id, '{"kind":"withdrawal_reserve"}'),
      (v_txn_id, 4, v_user_lock_id,      'credit', v_amount, 'SLH', v_user_id, '{"kind":"withdrawal_reserve"}');

    UPDATE user_balances
    SET available = available - v_amount,
        locked = locked + v_amount,
        updated_at = NOW()
    WHERE user_id = v_user_id
      AND available >= v_amount;

    INSERT INTO withdrawal_reservations (withdrawal_id, user_id, amount, status, created_at, updated_at)
    VALUES (p_withdrawal_id, v_user_id, v_amount, 'reserved', NOW(), NOW())
    ON CONFLICT (withdrawal_id) DO UPDATE
    SET status = 'reserved',
        updated_at = NOW();
  END IF;

  UPDATE withdrawals
  SET status = 'approved',
      reviewed_at = COALESCE(reviewed_at, NOW()),
      reviewed_by = p_admin_user_id,
      approved_at = COALESCE(approved_at, NOW()),
      reject_reason = NULL,
      error_message = NULL
  WHERE id = p_withdrawal_id;

  INSERT INTO audit_log(user_id, event_type, payload_json, created_at)
  SELECT
    v_user_id,
    'finance.withdraw.approved',
    '{"withdrawal_id":' || p_withdrawal_id::text || ',"admin_user_id":' || p_admin_user_id::text || '}',
    NOW()
  WHERE NOT EXISTS (
    SELECT 1
    FROM audit_log
    WHERE event_type = 'finance.withdraw.approved'
      AND payload_json LIKE '%"withdrawal_id":' || p_withdrawal_id::text || '%'
  );

  RETURN v_txn_id;
END;
$function$;

CREATE OR REPLACE FUNCTION public.finance_mark_withdrawal_sent_consume(
    p_withdrawal_id bigint,
    p_tx_hash text
)
RETURNS bigint
LANGUAGE plpgsql
AS $function$
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
    VALUES (
      v_ref_key,
      'withdrawal_consume',
      'posted',
      'Consume reserved withdrawal and mark sent',
      'withdrawals',
      p_withdrawal_id,
      NOW()
    )
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
    'finance.withdraw.sent',
    '{"withdrawal_id":' || p_withdrawal_id::text || ',"amount":' || v_amount::text || ',"status":"sent","tx_hash":"' || replace(p_tx_hash,'"','\"') || '"}',
    NOW()
  WHERE NOT EXISTS (
    SELECT 1
    FROM audit_log
    WHERE event_type = 'finance.withdraw.sent'
      AND payload_json LIKE '%"withdrawal_id":' || p_withdrawal_id::text || '%'
  );

  RETURN v_txn_id;
END;
$function$;

CREATE OR REPLACE FUNCTION public.finance_reject_withdrawal_release(
    p_withdrawal_id bigint,
    p_reason text DEFAULT NULL
)
RETURNS bigint
LANGUAGE plpgsql
AS $function$
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
    VALUES (
      v_ref_key,
      'withdrawal_release',
      'posted',
      'Release approved withdrawal back to available',
      'withdrawals',
      p_withdrawal_id,
      NOW()
    )
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
    'finance.withdraw.released',
    '{"withdrawal_id":' || p_withdrawal_id::text || ',"amount":' || v_amount::text || ',"status":"released"}',
    NOW()
  WHERE NOT EXISTS (
    SELECT 1
    FROM audit_log
    WHERE event_type = 'finance.withdraw.released'
      AND payload_json LIKE '%"withdrawal_id":' || p_withdrawal_id::text || '%'
  );

  RETURN v_txn_id;
END;
$function$;