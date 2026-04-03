BEGIN;

ALTER TABLE products
    ADD COLUMN IF NOT EXISTS is_featured BOOLEAN NOT NULL DEFAULT FALSE;

ALTER TABLE products
    ADD COLUMN IF NOT EXISTS inventory_mode TEXT NOT NULL DEFAULT 'unlimited';

ALTER TABLE products
    ADD COLUMN IF NOT EXISTS inventory_count INTEGER;

ALTER TABLE products
    ADD COLUMN IF NOT EXISTS purchase_limit_per_user INTEGER;

ALTER TABLE products
    ADD COLUMN IF NOT EXISTS requires_admin_delivery BOOLEAN NOT NULL DEFAULT TRUE;

ALTER TABLE products
    ADD COLUMN IF NOT EXISTS image_url TEXT;

ALTER TABLE products
    ADD COLUMN IF NOT EXISTS success_message_template TEXT;

CREATE INDEX IF NOT EXISTS idx_products_featured_visible
    ON products(is_featured, is_visible, is_active, sort_order, id);

UPDATE products
SET
    is_featured = TRUE,
    inventory_mode = 'unlimited',
    inventory_count = NULL,
    purchase_limit_per_user = 1,
    requires_admin_delivery = TRUE,
    success_message_template = 'Your VIP order was created successfully. Please submit payment reference to continue.'
WHERE code = 'VIP_MONTH';

UPDATE products
SET
    is_featured = TRUE,
    inventory_mode = 'unlimited',
    inventory_count = NULL,
    purchase_limit_per_user = 3,
    requires_admin_delivery = TRUE,
    success_message_template = 'Your audit package order was created successfully. Admin review will continue after payment submission.'
WHERE code = 'AUDIT_BASIC';

INSERT INTO system_settings(key, value_text, updated_at)
VALUES
    ('store_featured_enabled', '1', CURRENT_TIMESTAMP),
    ('store_inventory_enforced', '1', CURRENT_TIMESTAMP),
    ('store_purchase_limits_enforced', '1', CURRENT_TIMESTAMP)
ON CONFLICT (key) DO NOTHING;

INSERT INTO audit_log(user_id, event_type, payload_json, created_at)
VALUES (
    NULL,
    'schema.commerce_product_controls.v1',
    '{"source":"ops/sql/patch_commerce_product_controls_v1.sql","note":"featured + inventory + purchase limits + delivery fields"}',
    CURRENT_TIMESTAMP
);

COMMIT;