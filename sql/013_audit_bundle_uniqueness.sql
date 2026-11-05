-- SQL-013: prevent duplicate financial audits for the same reviewed bundle.
-- A new audit requires a newly signed/reviewed source bundle.
-- An existing installation with duplicate bundle runs MUST be reconciled
-- under an approved migration window; do not silently delete any audit.
ALTER TABLE lhfm_api_runs
  ADD UNIQUE KEY uq_audit_bundle_once (
    tenant_id, legal_entity_id, reviewer_id, bundle_id
  );
