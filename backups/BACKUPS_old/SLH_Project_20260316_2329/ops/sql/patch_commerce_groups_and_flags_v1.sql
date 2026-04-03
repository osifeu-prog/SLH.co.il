BEGIN;

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

CREATE INDEX IF NOT EXISTS idx_product_groups_is_active_sort
    ON product_groups(is_active, sort_order, id);

ALTER TABLE products
    ADD COLUMN IF NOT EXISTS group_id BIGINT REFERENCES product_groups(id) ON DELETE SET NULL;

ALTER TABLE products
    ADD COLUMN IF NOT EXISTS sort_order INTEGER NOT NULL DEFAULT 100;

ALTER TABLE products
    ADD COLUMN IF NOT EXISTS is_visible BOOLEAN NOT NULL DEFAULT TRUE;

CREATE INDEX IF NOT EXISTS idx_products_group_id
    ON products(group_id);

CREATE INDEX IF NOT EXISTS idx_products_visible_active_sort
    ON products(is_visible, is_active, sort_order, id);

INSERT INTO product_groups (
    code,
    title,
    description,
    sort_order,
    is_active,
    created_at,
    updated_at
)
VALUES
    ('SERVICES', 'Services', 'General services and operator-delivered flows', 10, TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
    ('SUBSCRIPTIONS', 'Subscriptions', 'Recurring or membership-style access products', 20, TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
    ('DIGITAL_GOODS', 'Digital Goods', 'Digital-only products and downloadable assets', 30, TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
    ('AUDITS', 'Audits', 'Audit and review packages', 40, TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
    ('VIP', 'VIP', 'Priority and premium access products', 50, TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
ON CONFLICT (code) DO UPDATE
SET
    title = EXCLUDED.title,
    description = EXCLUDED.description,
    sort_order = EXCLUDED.sort_order,
    is_active = EXCLUDED.is_active,
    updated_at = CURRENT_TIMESTAMP;

UPDATE products p
SET group_id = g.id
FROM product_groups g
WHERE p.code = 'VIP_MONTH'
  AND g.code = 'VIP'
  AND (p.group_id IS NULL OR p.group_id <> g.id);

UPDATE products p
SET group_id = g.id
FROM product_groups g
WHERE p.code = 'AUDIT_BASIC'
  AND g.code = 'AUDITS'
  AND (p.group_id IS NULL OR p.group_id <> g.id);

UPDATE products
SET sort_order = 10
WHERE code = 'VIP_MONTH';

UPDATE products
SET sort_order = 20
WHERE code = 'AUDIT_BASIC';

UPDATE products
SET is_visible = TRUE
WHERE code IN ('VIP_MONTH', 'AUDIT_BASIC');

INSERT INTO system_settings(key, value_text, updated_at)
VALUES
    ('store_visible_to_users', '1', CURRENT_TIMESTAMP),
    ('purchase_admin_approval_required', '1', CURRENT_TIMESTAMP),
    ('purchase_user_cancel_enabled', '1', CURRENT_TIMESTAMP),
    ('purchase_auto_fulfill_enabled', '0', CURRENT_TIMESTAMP)
ON CONFLICT (key) DO NOTHING;

INSERT INTO audit_log(user_id, event_type, payload_json, created_at)
VALUES (
    NULL,
    'schema.commerce_groups_and_flags.v1',
    '{"source":"ops/sql/patch_commerce_groups_and_flags_v1.sql","note":"product_groups + products visibility/order + commerce flags"}',
    CURRENT_TIMESTAMP
);

COMMIT;