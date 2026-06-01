BEGIN;

CREATE TABLE IF NOT EXISTS risk_entities (
    entity_id TEXT PRIMARY KEY,
    canonical_name TEXT NOT NULL,
    entity_type TEXT NOT NULL DEFAULT 'project',
    homepage_url TEXT,
    primary_chain TEXT,
    contract_address TEXT,
    source_status TEXT NOT NULL DEFAULT 'externally_claimed',
    public_summary TEXT,
    is_public BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS risk_aliases (
    alias_id BIGSERIAL PRIMARY KEY,
    entity_id TEXT NOT NULL REFERENCES risk_entities(entity_id) ON DELETE CASCADE,
    alias_text TEXT NOT NULL,
    alias_type TEXT NOT NULL DEFAULT 'name',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS risk_claims (
    claim_id BIGSERIAL PRIMARY KEY,
    entity_id TEXT NOT NULL REFERENCES risk_entities(entity_id) ON DELETE CASCADE,
    claim_type TEXT NOT NULL,
    claim_text TEXT NOT NULL,
    source_url TEXT,
    source_title TEXT,
    observed_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    verification_status TEXT NOT NULL DEFAULT 'unverified',
    visibility TEXT NOT NULL DEFAULT 'internal'
);

CREATE TABLE IF NOT EXISTS risk_evidence (
    evidence_id BIGSERIAL PRIMARY KEY,
    entity_id TEXT NOT NULL REFERENCES risk_entities(entity_id) ON DELETE CASCADE,
    evidence_type TEXT NOT NULL,
    title TEXT NOT NULL,
    storage_path TEXT,
    source_url TEXT,
    sha256 TEXT,
    notes TEXT,
    collected_by_user_id BIGINT,
    collected_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    verification_status TEXT NOT NULL DEFAULT 'pending'
);

CREATE TABLE IF NOT EXISTS risk_reports (
    report_id BIGSERIAL PRIMARY KEY,
    entity_id TEXT NOT NULL REFERENCES risk_entities(entity_id) ON DELETE CASCADE,
    reporter_user_id BIGINT,
    subject_user_id BIGINT,
    severity TEXT NOT NULL CHECK (severity IN ('low','medium','high','critical')),
    summary TEXT NOT NULL,
    evidence_ref TEXT,
    source_url TEXT,
    status TEXT NOT NULL DEFAULT 'pending_review',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_risk_aliases_entity ON risk_aliases(entity_id);
CREATE INDEX IF NOT EXISTS idx_risk_claims_entity ON risk_claims(entity_id);
CREATE INDEX IF NOT EXISTS idx_risk_evidence_entity ON risk_evidence(entity_id);
CREATE INDEX IF NOT EXISTS idx_risk_reports_entity ON risk_reports(entity_id);
CREATE INDEX IF NOT EXISTS idx_risk_reports_status ON risk_reports(status);
CREATE INDEX IF NOT EXISTS idx_risk_reports_severity ON risk_reports(severity);

CREATE OR REPLACE VIEW v_risk_entity_score AS
SELECT
    e.entity_id,
    e.canonical_name,
    e.entity_type,
    e.homepage_url,
    e.is_public,
    COALESCE((
        SELECT SUM(
            CASE r.severity
                WHEN 'low' THEN 5
                WHEN 'medium' THEN 10
                WHEN 'high' THEN 25
                WHEN 'critical' THEN 50
                ELSE 0
            END
        )
        FROM risk_reports r
        WHERE r.entity_id = e.entity_id
          AND r.status = 'approved'
    ), 0)::NUMERIC(18,2) AS score_zuz,
    (
        SELECT COUNT(*)
        FROM risk_reports r
        WHERE r.entity_id = e.entity_id
          AND r.status = 'approved'
    ) AS approved_reports,
    (
        SELECT COUNT(*)
        FROM risk_evidence ev
        WHERE ev.entity_id = e.entity_id
          AND ev.verification_status = 'verified'
    ) AS verified_evidence,
    CASE
        WHEN (
            SELECT COUNT(*)
            FROM risk_reports r
            WHERE r.entity_id = e.entity_id
              AND r.status = 'approved'
        ) >= 2
        AND (
            SELECT COUNT(*)
            FROM risk_evidence ev
            WHERE ev.entity_id = e.entity_id
              AND ev.verification_status = 'verified'
        ) >= 1
        THEN TRUE
        ELSE FALSE
    END AS eligible_for_publication
FROM risk_entities e;

CREATE OR REPLACE VIEW v_risk_public_cards AS
SELECT
    s.entity_id,
    s.canonical_name,
    s.entity_type,
    s.homepage_url,
    s.score_zuz,
    s.approved_reports,
    s.verified_evidence,
    CASE
        WHEN s.score_zuz >= 100 THEN 'critical'
        WHEN s.score_zuz >= 50 THEN 'high'
        WHEN s.score_zuz >= 20 THEN 'medium'
        WHEN s.score_zuz > 0 THEN 'low'
        ELSE 'none'
    END AS risk_level
FROM v_risk_entity_score s
WHERE s.eligible_for_publication = TRUE
  AND s.is_public = TRUE;

COMMIT;
