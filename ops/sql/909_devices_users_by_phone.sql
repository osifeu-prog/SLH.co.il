-- 909 — device-onboarding schema (phone → user_id → device_id → signing_token)
-- Supports: PC (windows/mac/linux), ESP32, SIM-only GSM devices, smartphones.

BEGIN;

-- Users identified primarily by phone (can link to telegram_id later)
CREATE TABLE IF NOT EXISTS users_by_phone (
    user_id BIGSERIAL PRIMARY KEY,
    phone TEXT UNIQUE NOT NULL,
    telegram_id BIGINT,
    display_name TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    last_seen TIMESTAMP DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_users_by_phone_tg ON users_by_phone(telegram_id)
    WHERE telegram_id IS NOT NULL;

-- Devices registered under a user
CREATE TABLE IF NOT EXISTS devices (
    device_id TEXT PRIMARY KEY,
    user_id BIGINT REFERENCES users_by_phone(user_id) ON DELETE SET NULL,
    device_type TEXT NOT NULL CHECK (device_type IN ('pc_windows','pc_mac','pc_linux','esp32','sim_gsm','smartphone','other')),
    device_name TEXT,
    signing_token TEXT,
    last_ip TEXT,
    last_user_agent TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    last_seen TIMESTAMP DEFAULT NOW(),
    registered_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_devices_user ON devices(user_id);
CREATE INDEX IF NOT EXISTS idx_devices_last_seen ON devices(last_seen DESC);

-- One-time verification codes (phone + device_id → 6-digit code, 5-min TTL)
CREATE TABLE IF NOT EXISTS device_verify_codes (
    id BIGSERIAL PRIMARY KEY,
    phone TEXT NOT NULL,
    device_id TEXT NOT NULL,
    code TEXT NOT NULL,
    attempts INTEGER DEFAULT 0,
    used BOOLEAN DEFAULT FALSE,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_verify_phone_device ON device_verify_codes(phone, device_id, used)
    WHERE used = FALSE;
CREATE INDEX IF NOT EXISTS idx_verify_expires ON device_verify_codes(expires_at);

-- Log of device actions (optional audit trail)
CREATE TABLE IF NOT EXISTS device_events (
    id BIGSERIAL PRIMARY KEY,
    device_id TEXT REFERENCES devices(device_id) ON DELETE CASCADE,
    event_type TEXT NOT NULL,   -- 'register', 'verify', 'sign', 'heartbeat'
    payload JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_device_events_dev ON device_events(device_id, created_at DESC);

COMMIT;
