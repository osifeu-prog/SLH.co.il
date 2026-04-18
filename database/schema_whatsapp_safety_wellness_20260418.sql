-- ============================================================
-- SLH Spark Integration Systems — Database Schema
-- Date: 2026-04-18
-- Components: WhatsApp, Safety Network, Wellness Admin
-- ============================================================

-- ============================================================
-- WHATSAPP INTEGRATION TABLES
-- ============================================================

CREATE TABLE IF NOT EXISTS whatsapp_contacts (
    id SERIAL PRIMARY KEY,
    phone_number VARCHAR(15) UNIQUE NOT NULL,
    user_id INT REFERENCES users(id),
    name VARCHAR(100),
    invited_at TIMESTAMP,
    last_contacted TIMESTAMP,
    contact_source VARCHAR(50),
    invitation_status VARCHAR(20) DEFAULT 'pending', -- pending, sent, opened, joined, blocked
    contact_metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS fraud_flags_whatsapp (
    id SERIAL PRIMARY KEY,
    phone_number VARCHAR(15),
    user_id INT REFERENCES users(id),
    fraud_type VARCHAR(50), -- 'spam', 'scam', 'identity_theft', 'other'
    severity INT CHECK (severity >= 1 AND severity <= 10),
    reported_by INT REFERENCES users(id),
    proof_url TEXT,
    proof_description TEXT,
    zuz_penalty INT DEFAULT 5,
    is_active BOOLEAN DEFAULT TRUE,
    appeals_count INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    INDEX idx_phone (phone_number),
    INDEX idx_user_id (user_id)
);

CREATE TABLE IF NOT EXISTS whatsapp_invites (
    id SERIAL PRIMARY KEY,
    phone_number VARCHAR(15) NOT NULL,
    invite_type VARCHAR(50), -- 'website', 'bot', 'course', 'event'
    invite_category VARCHAR(50),
    message_template TEXT,
    custom_message TEXT,
    sent_at TIMESTAMP,
    delivered BOOLEAN DEFAULT FALSE,
    read BOOLEAN DEFAULT FALSE,
    clicked BOOLEAN DEFAULT FALSE,
    clicked_url VARCHAR(500),
    clicked_at TIMESTAMP,
    response_text TEXT,
    created_by INT REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS whatsapp_broadcast (
    id SERIAL PRIMARY KEY,
    broadcast_title VARCHAR(200),
    broadcast_message TEXT,
    target_segment VARCHAR(100), -- 'all', 'interested', 'fraud_flagged', 'custom'
    phone_filter JSONB,
    scheduled_for TIMESTAMP,
    sent_at TIMESTAMP,
    total_recipients INT,
    delivered_count INT DEFAULT 0,
    read_count INT DEFAULT 0,
    click_count INT DEFAULT 0,
    created_by INT REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- SAFETY NETWORK TABLES
-- ============================================================

CREATE TABLE IF NOT EXISTS safety_alerts (
    id SERIAL PRIMARY KEY,
    source_group VARCHAR(100), -- 't.me/F7Bp00MKc3' or custom group ID
    source_user VARCHAR(100),
    source_user_id INT REFERENCES users(id),
    alert_title VARCHAR(200) NOT NULL,
    alert_description TEXT,
    threat_level INT CHECK (threat_level >= 1 AND threat_level <= 10),
    alert_category VARCHAR(50), -- 'fraud', 'scam', 'violence', 'theft', 'other'
    associated_phones TEXT[], -- Array of phone numbers
    associated_users INT[],
    location_info VARCHAR(200),
    evidence_url TEXT,
    evidence_type VARCHAR(50),
    zuz_mark_triggered BOOLEAN DEFAULT FALSE,
    zuz_penalties_issued INT DEFAULT 0,
    penalty_user_ids INT[],
    is_verified BOOLEAN DEFAULT FALSE,
    verified_by INT REFERENCES users(id),
    alert_status VARCHAR(20) DEFAULT 'open', -- 'open', 'investigating', 'resolved', 'false_alarm'
    reported_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    INDEX idx_threat_level (threat_level),
    INDEX idx_source_group (source_group)
);

CREATE TABLE IF NOT EXISTS threat_intel (
    id SERIAL PRIMARY KEY,
    phone_number VARCHAR(15),
    user_id INT REFERENCES users(id),
    threat_score FLOAT CHECK (threat_score >= 0 AND threat_score <= 100),
    threat_category VARCHAR(50),
    last_flagged TIMESTAMP,
    flagged_count INT DEFAULT 0,
    alert_ids INT[],
    auto_banned BOOLEAN DEFAULT FALSE,
    ban_reason VARCHAR(200),
    ban_expire_date TIMESTAMP,
    confidence_level FLOAT DEFAULT 0.5,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    INDEX idx_phone (phone_number),
    INDEX idx_threat_score (threat_score)
);

CREATE TABLE IF NOT EXISTS community_groups (
    id SERIAL PRIMARY KEY,
    group_name VARCHAR(100) NOT NULL,
    telegram_id VARCHAR(100) UNIQUE,
    group_type VARCHAR(50), -- 'public_safety', 'crime_alert', 'community_watch', 'custom'
    group_url VARCHAR(500),
    group_description TEXT,
    is_monitored BOOLEAN DEFAULT TRUE,
    members_count INT DEFAULT 0,
    last_sync TIMESTAMP,
    sync_frequency VARCHAR(20) DEFAULT '5min', -- '1min', '5min', '15min', '30min'
    moderator_ids INT[],
    alert_count INT DEFAULT 0,
    created_by INT REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS security_org_links (
    id SERIAL PRIMARY KEY,
    org_name VARCHAR(100) NOT NULL,
    org_type VARCHAR(50), -- 'police', 'security_company', 'nonprofit', 'community_org'
    contact_email VARCHAR(100),
    contact_phone VARCHAR(15),
    api_endpoint VARCHAR(500),
    api_key_encrypted VARCHAR(500),
    is_active BOOLEAN DEFAULT TRUE,
    alert_threshold INT DEFAULT 5, -- Auto-alert if threat level >= X
    created_by INT REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- WELLNESS SYSTEM TABLES
-- ============================================================

CREATE TABLE IF NOT EXISTS wellness_courses (
    id SERIAL PRIMARY KEY,
    course_title VARCHAR(200) NOT NULL,
    course_slug VARCHAR(100) UNIQUE,
    course_description TEXT,
    course_content LONGTEXT,
    instructor_id INT REFERENCES users(id),
    category VARCHAR(50), -- 'meditation', 'fitness', 'nutrition', 'wellness'
    difficulty VARCHAR(20) DEFAULT 'beginner', -- 'beginner', 'intermediate', 'advanced'
    duration_minutes INT,
    price_slh FLOAT DEFAULT 0.1,
    price_zvk INT DEFAULT 2,
    price_mnה FLOAT DEFAULT 0,
    video_url VARCHAR(500),
    thumbnail_url VARCHAR(500),
    tags JSONB,
    published BOOLEAN DEFAULT FALSE,
    published_at TIMESTAMP,
    student_count INT DEFAULT 0,
    rating FLOAT DEFAULT 0,
    review_count INT DEFAULT 0,
    created_by INT REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    INDEX idx_published (published),
    INDEX idx_category (category)
);

CREATE TABLE IF NOT EXISTS wellness_tasks (
    id SERIAL PRIMARY KEY,
    task_title VARCHAR(100) NOT NULL,
    task_description TEXT,
    task_type VARCHAR(50), -- 'meditation', 'exercise', 'nutrition', 'affirmation'
    task_duration_minutes INT,
    task_instructions TEXT,
    reward_slh FLOAT DEFAULT 0.1,
    reward_zvk INT DEFAULT 1,
    reward_mnה FLOAT DEFAULT 0,
    reward_rep INT DEFAULT 1,
    difficulty VARCHAR(20) DEFAULT 'beginner',
    is_daily BOOLEAN DEFAULT TRUE,
    is_seasonal BOOLEAN DEFAULT FALSE,
    created_by INT REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS wellness_schedules (
    id SERIAL PRIMARY KEY,
    schedule_name VARCHAR(100) NOT NULL,
    schedule_description TEXT,
    schedule_type VARCHAR(50) DEFAULT 'daily', -- 'daily', 'weekly', 'custom', 'seasonal'
    cron_expression VARCHAR(100),
    task_ids INT[],
    broadcast_time TIME,
    broadcast_timezone VARCHAR(50) DEFAULT 'Asia/Jerusalem',
    is_active BOOLEAN DEFAULT TRUE,
    created_by INT REFERENCES users(id),
    last_broadcast TIMESTAMP,
    broadcast_count INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS wellness_completions (
    id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(id) NOT NULL,
    task_id INT REFERENCES wellness_tasks(id),
    course_id INT REFERENCES wellness_courses(id),
    completion_status VARCHAR(20) DEFAULT 'completed', -- 'completed', 'abandoned', 'verified'
    time_spent_minutes INT,
    feedback_text TEXT,
    rating INT CHECK (rating IS NULL OR (rating >= 1 AND rating <= 5)),
    tokens_awarded JSONB,
    streak_count INT DEFAULT 1,
    is_bonus_streak BOOLEAN DEFAULT FALSE,
    bonus_multiplier FLOAT DEFAULT 1.0,
    completed_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    INDEX idx_user_id (user_id),
    INDEX idx_completed_at (completed_at)
);

CREATE TABLE IF NOT EXISTS wellness_user_progress (
    id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(id) NOT NULL,
    total_tasks_completed INT DEFAULT 0,
    total_courses_completed INT DEFAULT 0,
    current_streak INT DEFAULT 0,
    longest_streak INT DEFAULT 0,
    last_activity_date DATE,
    total_time_spent_minutes INT DEFAULT 0,
    total_rewards JSONB,
    favorite_task_type VARCHAR(50),
    preferred_time_of_day VARCHAR(20), -- 'morning', 'afternoon', 'evening', 'night'
    notification_preference VARCHAR(20) DEFAULT 'daily', -- 'daily', 'weekly', 'none'
    updated_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- AUDIT & LOGGING TABLES
-- ============================================================

CREATE TABLE IF NOT EXISTS integration_audit_log (
    id SERIAL PRIMARY KEY,
    system VARCHAR(50), -- 'whatsapp', 'safety_network', 'wellness'
    action VARCHAR(100),
    action_type VARCHAR(50), -- 'create', 'update', 'delete', 'flag', 'alert', 'broadcast'
    target_id INT,
    target_type VARCHAR(50),
    user_id INT REFERENCES users(id),
    details JSONB,
    status VARCHAR(20), -- 'success', 'failed', 'pending'
    error_message TEXT,
    ip_address VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW(),
    INDEX idx_system (system),
    INDEX idx_action_type (action_type),
    INDEX idx_created_at (created_at)
);

-- ============================================================
-- INDEXES FOR PERFORMANCE
-- ============================================================

CREATE INDEX idx_whatsapp_contacts_phone ON whatsapp_contacts(phone_number);
CREATE INDEX idx_whatsapp_contacts_user ON whatsapp_contacts(user_id);
CREATE INDEX idx_fraud_flags_phone ON fraud_flags_whatsapp(phone_number);
CREATE INDEX idx_fraud_flags_user ON fraud_flags_whatsapp(user_id);
CREATE INDEX idx_fraud_flags_severity ON fraud_flags_whatsapp(severity);

CREATE INDEX idx_safety_alerts_threat ON safety_alerts(threat_level);
CREATE INDEX idx_safety_alerts_group ON safety_alerts(source_group);
CREATE INDEX idx_safety_alerts_status ON safety_alerts(alert_status);
CREATE INDEX idx_threat_intel_phone ON threat_intel(phone_number);
CREATE INDEX idx_threat_intel_score ON threat_intel(threat_score);
CREATE INDEX idx_threat_intel_banned ON threat_intel(auto_banned);

CREATE INDEX idx_wellness_courses_published ON wellness_courses(published);
CREATE INDEX idx_wellness_courses_category ON wellness_courses(category);
CREATE INDEX idx_wellness_completions_user ON wellness_completions(user_id);
CREATE INDEX idx_wellness_completions_date ON wellness_completions(completed_at);
CREATE INDEX idx_wellness_progress_user ON wellness_user_progress(user_id);

-- ============================================================
-- SEED DATA (Optional - remove if using migrations)
-- ============================================================

-- Example initial tasks
INSERT INTO wellness_tasks (task_title, task_type, task_duration_minutes, reward_zvk) VALUES
('יומי: מדיטציה בוקר', 'meditation', 10, 2),
('יומי: אימון קל', 'exercise', 15, 3),
('יומי: טיפ תזונה', 'nutrition', 5, 1),
('יומי: אימרה חיזוקית', 'affirmation', 2, 1);

-- Example initial schedule
INSERT INTO wellness_schedules (schedule_name, schedule_type, schedule_description, cron_expression, task_ids, broadcast_time) VALUES
('תוכנית יומית SLH', 'daily', 'שיגור יומי של משימות wellness', '0 8 * * *', '{1,2,3,4}', '08:00');

-- ============================================================
-- END OF SCHEMA
-- ============================================================
