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
    'CASE-ZOOZ-001 Evidence 1',
    'D:\EVIDENCE\CASE-ZOOZ-001\evidence1.pdf',
    NULL,
    NULL,
    'Primary internal evidence - replace with real description',
    224223270,
    'pending'
);

COMMIT;
