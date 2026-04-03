BEGIN;

CREATE TABLE IF NOT EXISTS system_settings (
    key TEXT PRIMARY KEY,
    value_text TEXT,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

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

CREATE TABLE IF NOT EXISTS product_groups (
    id BIGSERIAL PRIMARY KEY,
    code TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    description TEXT,
    sort_order INTEGER NOT NULL DEFAULT 100,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

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

CREATE INDEX IF NOT EXISTS idx_products_is_active
ON products(is_active);

CREATE INDEX IF NOT EXISTS idx_product_groups_is_active
ON product_groups(is_active);

CREATE INDEX IF NOT EXISTS idx_purchase_orders_user_id
ON purchase_orders(user_id);

CREATE INDEX IF NOT EXISTS idx_purchase_orders_product_id
ON purchase_orders(product_id);

CREATE INDEX IF NOT EXISTS idx_purchase_orders_status
ON purchase_orders(status);

CREATE INDEX IF NOT EXISTS idx_purchase_orders_created_at
ON purchase_orders(created_at);

COMMIT;