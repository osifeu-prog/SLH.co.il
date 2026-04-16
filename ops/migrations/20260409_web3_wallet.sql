-- ============================================================
-- Migration: Web3 Wallet Linking
-- Date:      2026-04-09
-- Purpose:   Add on-chain wallet linking to web_users
-- Safe:     Idempotent — can be re-run
-- ============================================================

-- BSC / ETH address (ERC-20 style): 0x + 40 hex chars
ALTER TABLE web_users
  ADD COLUMN IF NOT EXISTS eth_wallet VARCHAR(42);

ALTER TABLE web_users
  ADD COLUMN IF NOT EXISTS eth_wallet_linked_at TIMESTAMP;

-- TON address (UQ / EQ format, 66–68 chars)
ALTER TABLE web_users
  ADD COLUMN IF NOT EXISTS ton_wallet VARCHAR(68);

ALTER TABLE web_users
  ADD COLUMN IF NOT EXISTS ton_wallet_linked_at TIMESTAMP;

-- Fast lookup + uniqueness guard (partial so NULL doesn't collide)
CREATE INDEX IF NOT EXISTS idx_web_users_eth_wallet
  ON web_users(eth_wallet)
  WHERE eth_wallet IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_web_users_ton_wallet
  ON web_users(ton_wallet)
  WHERE ton_wallet IS NOT NULL;

-- ============================================================
-- Sanity check
-- ============================================================
-- SELECT telegram_id, username, eth_wallet, eth_wallet_linked_at
--   FROM web_users
--  WHERE eth_wallet IS NOT NULL
--  ORDER BY eth_wallet_linked_at DESC
--  LIMIT 20;
