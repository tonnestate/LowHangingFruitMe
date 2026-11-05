-- SQL-013: prevent duplicate financial executions per reviewed bundle and run state.
-- Preserve one separate NEEDS_REVIEW result after a rule becomes non-current.
-- Historical duplicates require operator reconciliation, never automatic deletion.
ALTER TABLE lhfm_api_runs
  ADD UNIQUE KEY uq_audit_bundle_state
    (tenant_id, legal_entity_id, reviewer_id, bundle_id, status);
