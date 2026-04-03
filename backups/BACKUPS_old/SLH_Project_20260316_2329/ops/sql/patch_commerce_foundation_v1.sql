BEGIN;

CREATE TABLE IF NOT EXISTS products (
    id BIGSERIAL PRIMARY KEY,
    code TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    description TEXT,
    price_amount NUMERIC(18,8) NOT NULL,
    price_currency TEXT NOT NULL DEFAULT 'TON',
    product_type TEXT NOT NULL DEFAULT 'digital',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_products_is_active
    ON products(is_active);

CREATE TABLE IF NOT EXISTS purchase_orders (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    product_id BIGINT NOT NULL REFERENCES products(id) ON DELETE RESTRICT,
    product_code TEXT NOT NULL,
    product_title TEXT NOT NULL,
    quantity INTEGER NOT NULL DEFAULT 1,
    unit_price_amount NUMERIC(18,8) NOT NULL,
    total_amount NUMERIC(18,8) NOT NULL,
    currency TEXT NOT NULL DEFAULT 'TON',
    payment_method TEXT NOT NULL DEFAULT 'manual',
    status TEXT NOT NULL DEFAULT 'pending_payment',
    external_payment_ref TEXT,
    admin_note TEXT,
    paid_at TIMESTAMP,
    fulfilled_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_purchase_orders_quantity_positive CHECK (quantity > 0),
    CONSTRAINT chk_purchase_orders_unit_price_nonnegative CHECK (unit_price_amount >= 0),
    CONSTRAINT chk_purchase_orders_total_nonnegative CHECK (total_amount >= 0),
    CONSTRAINT chk_purchase_orders_status CHECK (
        status IN (
            'pending_payment',
            'payment_submitted',
            'paid',
            'fulfilled',
            'cancelled',
            'failed'
        )
    )
);

CREATE INDEX IF NOT EXISTS idx_purchase_orders_user_id_created_at
    ON purchase_orders(user_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_purchase_orders_status_created_at
    ON purchase_orders(status, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_purchase_orders_product_id_created_at
    ON purchase_orders(product_id, created_at DESC);

INSERT INTO system_settings(key, value_text, updated_at)
VALUES
    ('commerce_enabled', '0', CURRENT_TIMESTAMP),
    ('purchase_manual_payment_enabled', '1', CURRENT_TIMESTAMP),
    ('purchase_ton_payment_enabled', '0', CURRENT_TIMESTAMP)
ON CONFLICT (key) DO NOTHING;

INSERT INTO audit_log(user_id, event_type, payload_json, created_at)
VALUES (
    NULL,
    'schema.commerce_foundation.v1',
    '{"source":"ops/sql/patch_commerce_foundation_v1.sql","note":"products + purchase_orders added"}',
    CURRENT_TIMESTAMP
);

COMMIT;