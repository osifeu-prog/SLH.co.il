SELECT entity_id, canonical_name, homepage_url, contract_address, is_public
FROM risk_entities
ORDER BY canonical_name;

SELECT entity_id, claim_type, verification_status, LEFT(claim_text, 110) AS claim_preview
FROM risk_claims
ORDER BY claim_id;

SELECT *
FROM v_risk_entity_score
ORDER BY score_zuz DESC, canonical_name;
