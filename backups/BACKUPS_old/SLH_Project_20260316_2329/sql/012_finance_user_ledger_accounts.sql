BEGIN;

CREATE OR REPLACE FUNCTION finance_ensure_user_ledger_accounts(
  p_user_id BIGINT
)
RETURNS VOID
LANGUAGE plpgsql
AS $$
BEGIN
  INSERT INTO ledger_accounts (code, owner_user_id, account_type, normal_side)
  VALUES
    ('USR_AVAIL_' || p_user_id::text, p_user_id, 'user_liability_available', 'credit')
  ON CONFLICT (code) DO NOTHING;

  INSERT INTO ledger_accounts (code, owner_user_id, account_type, normal_side)
  VALUES
    ('USR_LOCK_' || p_user_id::text, p_user_id, 'user_liability_locked', 'credit')
  ON CONFLICT (code) DO NOTHING;
END;
$$;

CREATE OR REPLACE FUNCTION trg_users_ensure_ledger_accounts()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
  PERFORM finance_ensure_user_ledger_accounts(NEW.user_id);
  RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_users_ensure_ledger_accounts ON users;
CREATE TRIGGER trg_users_ensure_ledger_accounts
AFTER INSERT ON users
FOR EACH ROW
EXECUTE FUNCTION trg_users_ensure_ledger_accounts();

SELECT finance_ensure_user_ledger_accounts(user_id)
FROM users
WHERE user_id = 900000001;

INSERT INTO audit_log(user_id, event_type, payload_json, created_at)
SELECT
  NULL,
  'schema.finance_user_ledger_accounts.v1',
  '{"ok":true,"objects":["finance_ensure_user_ledger_accounts","trg_users_ensure_ledger_accounts"]}',
  NOW()
WHERE NOT EXISTS (
  SELECT 1
  FROM audit_log
  WHERE event_type = 'schema.finance_user_ledger_accounts.v1'
);

COMMIT;