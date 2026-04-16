BEGIN;

CREATE TABLE IF NOT EXISTS external_asset_watch (
    watch_id BIGSERIAL PRIMARY KEY,
    asset_key TEXT UNIQUE NOT NULL,
    asset_name TEXT NOT NULL,
    chain TEXT NOT NULL,
    contract_address TEXT NOT NULL,
    homepage_url TEXT,
    source_url TEXT,
    status TEXT NOT NULL DEFAULT 'active',
    notes TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS external_asset_snapshots (
    snapshot_id BIGSERIAL PRIMARY KEY,
    asset_key TEXT NOT NULL REFERENCES external_asset_watch(asset_key) ON DELETE CASCADE,
    observed_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    price_usd NUMERIC(18,8),
    total_supply NUMERIC(38,8),
    circulating_supply NUMERIC(38,8),
    liquidity_usd NUMERIC(18,2),
    holders_count INTEGER,
    source_url TEXT,
    raw_json TEXT
);

INSERT INTO external_asset_watch (
    asset_key, asset_name, chain, contract_address, homepage_url, source_url, notes
) VALUES (
    'coalichain_zooz_bsc',
    'Coalichain Token (ZOOZ)',
    'BNB Smart Chain',
    '0x132306a39d6fC1E49C3Cb6D8FE8d07d4D44B462a',
    'https://zooz.coali.app/',
    'https://zooz.coalichain.io/',
    'Externally monitored asset. No economic linkage to internal ZUZ token.'
)
ON CONFLICT (asset_key) DO UPDATE SET
    asset_name = EXCLUDED.asset_name,
    chain = EXCLUDED.chain,
    contract_address = EXCLUDED.contract_address,
    homepage_url = EXCLUDED.homepage_url,
    source_url = EXCLUDED.source_url,
    notes = EXCLUDED.notes,
    updated_at = CURRENT_TIMESTAMP;

COMMIT;
