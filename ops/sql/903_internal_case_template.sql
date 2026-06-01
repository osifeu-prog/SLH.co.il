BEGIN;

INSERT INTO risk_reports (
    entity_id,
    reporter_user_id,
    severity,
    summary,
    evidence_ref,
    source_url,
    status
) VALUES (
    'coalichain_zooz',
    224223270,
    'medium',
    'Internal allegation record created for review. This entry is not public and does not assert wrongdoing as fact. Publish only after evidence verification.',
    'CASE-ZOOZ-001',
    NULL,
    'pending_review'
);

COMMIT;
