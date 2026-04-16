BEGIN;

INSERT INTO risk_evidence (
    entity_id,
    evidence_type,
    title,
    storage_path,
    source_url,
    sha256,
    notes,
    collected_by_user_id,
    verification_status
) VALUES (
    'coalichain_zooz',
    'document',
    'PLACEHOLDER - replace with actual evidence title',
    'D:\EVIDENCE\CASE-ZOOZ-001\replace_me.pdf',
    NULL,
    NULL,
    'Internal evidence placeholder. Replace before apply.',
    224223270,
    'pending'
);

COMMIT;
