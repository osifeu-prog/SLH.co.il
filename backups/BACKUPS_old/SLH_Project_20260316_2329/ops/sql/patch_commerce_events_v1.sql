CREATE TABLE IF NOT EXISTS commerce_events (
    id BIGSERIAL PRIMARY KEY,
    order_id BIGINT,
    event_type TEXT NOT NULL,
    actor_user_id BIGINT,
    payload_json JSONB,
    created_at TIMESTAMP NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_commerce_events_order
ON commerce_events(order_id);