-- SQL-013: enforce one in-flight and one finalized financial audit per signed bundle.
-- NEEDS_REVIEW is intentionally not unique: the old bundle must be recheckable
-- after approval revocation or supersession without overwriting evidence.
-- Historical concurrent/finalized duplicates require manual reconciliation.
ALTER TABLE lhfm_api_runs
  ADD COLUMN processing_bundle_id CHAR(36) AS
    (CASE WHEN status='PROCESSING' THEN bundle_id ELSE NULL END) PERSISTENT,
  ADD COLUMN completed_bundle_id CHAR(36) AS
    (CASE WHEN status='COMPLETED' THEN bundle_id ELSE NULL END) PERSISTENT,
  ADD UNIQUE KEY uq_audit_processing_once
    (tenant_id, legal_entity_id, reviewer_id, processing_bundle_id),
  ADD UNIQUE KEY uq_audit_completed_once
    (tenant_id, legal_entity_id, reviewer_id, completed_bundle_id);
