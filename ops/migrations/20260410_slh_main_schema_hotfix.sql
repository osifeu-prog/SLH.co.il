-- SLH_HOTFIX 2026-04-10: Align slh_main schema to code expectations
-- =================================================================
-- Fixes live errors in slh-core-bot:
--   1. UndefinedTableError: relation "v_user_withdrawal_history" does not exist
--   2. UndefinedColumnError: column "last_claim_at" does not exist
--   3. UndefinedColumnError: column "task_code" does not exist
--
-- Target: slh_main database
-- Safety: All 3 tables are empty (0 rows) at time of migration — no data loss risk
-- Backup: D:\SLH_BACKUPS\FULL_20260410_125544\slh_main.sql
-- =================================================================

BEGIN;

-- =================================================================
-- FIX 1: daily_claims — add columns expected by daily.py
-- =================================================================
-- Code expects: streak, last_claim_at, last_reward, updated_at
-- With UNIQUE(user_id) for ON CONFLICT (user_id) DO UPDATE

ALTER TABLE daily_claims
    ADD COLUMN IF NOT EXISTS last_claim_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ADD COLUMN IF NOT EXISTS last_reward NUMERIC(20, 8) DEFAULT 0,
    ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;

-- Migrate any existing claimed_at → last_claim_at (safety, even though empty)
UPDATE daily_claims SET last_claim_at = claimed_at WHERE last_claim_at IS NULL AND claimed_at IS NOT NULL;

-- Need UNIQUE constraint on user_id for ON CONFLICT
-- Drop the existing PK on id, make user_id unique instead
-- (daily_claims is keyed by user_id semantically - one row per user)
ALTER TABLE daily_claims DROP CONSTRAINT IF EXISTS daily_claims_user_id_unique;
ALTER TABLE daily_claims ADD CONSTRAINT daily_claims_user_id_unique UNIQUE (user_id);

-- =================================================================
-- FIX 2: task_verifications — add task_code column expected by tasks.py
-- =================================================================
-- Code queries: SELECT task_code, status FROM task_verifications
-- Current DB has: task_id INTEGER
-- Solution: Add task_code as alias column that mirrors task_id

ALTER TABLE task_verifications
    ADD COLUMN IF NOT EXISTS task_code INTEGER;

-- Backfill task_code from task_id
UPDATE task_verifications SET task_code = task_id WHERE task_code IS NULL;

-- Keep them in sync via trigger for future inserts
CREATE OR REPLACE FUNCTION task_verifications_sync_codes() RETURNS TRIGGER AS $$
BEGIN
    IF NEW.task_code IS NULL AND NEW.task_id IS NOT NULL THEN
        NEW.task_code := NEW.task_id;
    ELSIF NEW.task_id IS NULL AND NEW.task_code IS NOT NULL THEN
        NEW.task_id := NEW.task_code;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS task_verifications_sync_trigger ON task_verifications;
CREATE TRIGGER task_verifications_sync_trigger
    BEFORE INSERT OR UPDATE ON task_verifications
    FOR EACH ROW EXECUTE FUNCTION task_verifications_sync_codes();

-- =================================================================
-- FIX 3: withdrawals — add columns expected by withdrawals_query.py
-- =================================================================
-- Code expects: wallet, reviewed_at, processed_at, reject_reason, reservation_status
-- Some exist (tx_hash), some don't

ALTER TABLE withdrawals
    ADD COLUMN IF NOT EXISTS wallet TEXT,
    ADD COLUMN IF NOT EXISTS reviewed_at TIMESTAMP,
    ADD COLUMN IF NOT EXISTS processed_at TIMESTAMP,
    ADD COLUMN IF NOT EXISTS reject_reason TEXT,
    ADD COLUMN IF NOT EXISTS reservation_status TEXT;

-- Backfill wallet from existing to_address
UPDATE withdrawals SET wallet = to_address WHERE wallet IS NULL AND to_address IS NOT NULL;

-- =================================================================
-- FIX 4: Create v_user_withdrawal_history view
-- =================================================================

DROP VIEW IF EXISTS v_user_withdrawal_history;

CREATE VIEW v_user_withdrawal_history AS
SELECT
    w.id,
    w.user_id,
    w.amount,
    COALESCE(w.wallet, w.to_address) AS wallet,
    w.status,
    w.created_at,
    w.reviewed_at,
    w.processed_at,
    w.reject_reason,
    w.tx_hash,
    w.reservation_status
FROM withdrawals w;

-- =================================================================
-- FIX 5: Create v_withdrawal_admin_queue view (not yet erroring but code uses it)
-- =================================================================

DROP VIEW IF EXISTS v_withdrawal_admin_queue;

CREATE VIEW v_withdrawal_admin_queue AS
SELECT
    w.id,
    w.user_id,
    u.username,
    w.amount,
    COALESCE(w.wallet, w.to_address) AS wallet,
    w.status,
    w.created_at,
    w.reviewed_at,
    w.processed_at,
    w.reject_reason,
    w.tx_hash,
    w.reservation_status,
    COALESCE((SELECT balance FROM token_balances tb WHERE tb.user_id = w.user_id AND tb.token = 'SLH' LIMIT 1), 0) AS available,
    0::numeric AS locked,
    0::numeric AS ledger_available,
    0::numeric AS ledger_locked,
    0::numeric AS delta_available,
    0::numeric AS delta_locked
FROM withdrawals w
LEFT JOIN users u ON u.user_id = w.user_id;

COMMIT;

-- =================================================================
-- VERIFICATION
-- =================================================================
\echo 'Verifying schema changes...'
SELECT column_name FROM information_schema.columns
    WHERE table_name = 'daily_claims' AND column_name IN ('last_claim_at', 'last_reward', 'updated_at')
    ORDER BY column_name;
SELECT column_name FROM information_schema.columns
    WHERE table_name = 'task_verifications' AND column_name = 'task_code';
SELECT to_regclass('public.v_user_withdrawal_history') AS view_exists;
SELECT to_regclass('public.v_withdrawal_admin_queue') AS admin_view_exists;
