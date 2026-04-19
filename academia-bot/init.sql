-- SLH Academia bot schema + seed.
-- Safe to run repeatedly (CREATE IF NOT EXISTS + ON CONFLICT DO NOTHING).

CREATE TABLE IF NOT EXISTS academy_courses (
    id BIGSERIAL PRIMARY KEY,
    slug TEXT UNIQUE NOT NULL,
    title_he TEXT NOT NULL,
    description_he TEXT,
    price_ils NUMERIC(10,2),
    price_slh NUMERIC(18,4),
    materials_url TEXT,
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS academy_licenses (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    course_id BIGINT REFERENCES academy_courses(id),
    payment_id TEXT,
    status TEXT DEFAULT 'active',
    purchased_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_acad_user ON academy_licenses(user_id);

-- Seed one sample course. [DEMO] tag per project convention.
INSERT INTO academy_courses (slug, title_he, description_he, price_ils, price_slh, materials_url)
VALUES (
    'intro-slh',
    '[DEMO] מבוא ל-SLH — השקעה וקריפטו לישראלים',
    'קורס יסוד שעוזר להבין את השוק, הסיכונים, והפלטפורמה.',
    49.0,
    0.11,
    'https://slh-nft.com/academy/intro-slh'
)
ON CONFLICT (slug) DO NOTHING;
