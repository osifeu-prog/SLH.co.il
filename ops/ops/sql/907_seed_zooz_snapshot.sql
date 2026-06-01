BEGIN;

INSERT INTO external_asset_snapshots (
    asset_key,
    price_usd,
    total_supply,
    circulating_supply,
    liquidity_usd,
    holders_count,
    source_url,
    raw_json
) VALUES (
    'coalichain_zooz_bsc',
    0.248330,
    770000000,
    759643000,
    45500,
    NULL,
    'https://zooz.coalichain.io/',
    '{"seed":"manual_from_verified_external_sources","network":"BNB Smart Chain","standard":"BEP-20"}'
);

COMMIT;
