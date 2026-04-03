BEGIN;

INSERT INTO products (
    code,
    title,
    description,
    price_amount,
    price_currency,
    product_type,
    is_active,
    created_at,
    updated_at
)
VALUES
    (
        'VIP_MONTH',
        'VIP Monthly Access',
        'Manual-first monthly VIP access product for commerce flow validation.',
        10.00000000,
        'TON',
        'digital',
        TRUE,
        CURRENT_TIMESTAMP,
        CURRENT_TIMESTAMP
    ),
    (
        'AUDIT_BASIC',
        'Basic Audit Package',
        'Manual-first audit package for commerce flow validation.',
        25.00000000,
        'TON',
        'service',
        TRUE,
        CURRENT_TIMESTAMP,
        CURRENT_TIMESTAMP
    )
ON CONFLICT (code) DO UPDATE
SET
    title = EXCLUDED.title,
    description = EXCLUDED.description,
    price_amount = EXCLUDED.price_amount,
    price_currency = EXCLUDED.price_currency,
    product_type = EXCLUDED.product_type,
    is_active = EXCLUDED.is_active,
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO audit_log(user_id, event_type, payload_json, created_at)
VALUES (
    NULL,
    'commerce.products_seeded.v1',
    '{"source":"ops/sql/seed_products_v1.sql","codes":["VIP_MONTH","AUDIT_BASIC"]}',
    CURRENT_TIMESTAMP
);

COMMIT;