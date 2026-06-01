BEGIN;

INSERT INTO risk_entities (
    entity_id, canonical_name, entity_type, homepage_url, primary_chain, contract_address,
    source_status, public_summary, is_public
) VALUES (
    'coalichain_zooz',
    'ZooZ / Coalichain',
    'project',
    'https://zooz.coali.app/',
    'BSC',
    '0x132306a39d6fC1E49C3Cb6D8FE8d07d4D44B462a',
    'externally_claimed',
    'Externally claimed governance / community token project. Internal review only.',
    FALSE
)
ON CONFLICT (entity_id) DO UPDATE SET
    canonical_name = EXCLUDED.canonical_name,
    homepage_url = EXCLUDED.homepage_url,
    primary_chain = EXCLUDED.primary_chain,
    contract_address = EXCLUDED.contract_address,
    source_status = EXCLUDED.source_status,
    public_summary = EXCLUDED.public_summary,
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO risk_aliases (entity_id, alias_text, alias_type)
VALUES
('coalichain_zooz','ZooZ','token'),
('coalichain_zooz','Coalichain','project'),
('coalichain_zooz','Coali','app')
ON CONFLICT DO NOTHING;

INSERT INTO risk_claims (entity_id, claim_type, claim_text, source_url, source_title, verification_status, visibility)
VALUES
(
  'coalichain_zooz',
  'public_claim',
  'Public site states ZooZ is the governance token of the Coalichain ecosystem and references Proof of Influence.',
  'https://zooz.coali.app/',
  'ZooZ / Coalichain website',
  'unverified',
  'internal'
),
(
  'coalichain_zooz',
  'public_claim',
  'Public site lists total supply as 770,000,000 ZooZ and circulating supply as 400,000 ZooZ.',
  'https://zooz.coali.app/',
  'ZooZ token data',
  'unverified',
  'internal'
),
(
  'coalichain_zooz',
  'public_claim',
  'Public site lists BSC contract address 0x132306a39d6fC1E49C3Cb6D8FE8d07d4D44B462a.',
  'https://zooz.coali.app/',
  'ZooZ token data',
  'unverified',
  'internal'
),
(
  'coalichain_zooz',
  'public_claim',
  'App store listings describe Coali as a governance app and say the ZooZ token may validate participation or reward engagement.',
  'https://play.google.com/store/apps/details?id=com.coalichain',
  'Coali app listing',
  'unverified',
  'internal'
)
ON CONFLICT DO NOTHING;

COMMIT;
