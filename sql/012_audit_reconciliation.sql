-- v0.19: immutable operator reconciliation for orphaned audit processing reservations.
-- Does not execute or retry a calculation and never deletes any financial evidence.
CREATE TABLE lhfm_audit_reconciliation_events (
  event_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  audit_id CHAR(36) NOT NULL,
  tenant_id VARCHAR(128) NOT NULL,
  legal_entity_id VARCHAR(128) NOT NULL,
  operator_id VARCHAR(128) NOT NULL,
  incident_ref VARCHAR(200) NOT NULL,
  prior_state VARCHAR(20) NOT NULL,
  recorded_at DATETIME(6) NOT NULL DEFAULT UTC_TIMESTAMP(6),
  PRIMARY KEY (event_id),
  UNIQUE KEY uq_audit_reconciliation_run (audit_id),
  CONSTRAINT fk_audit_reconciliation_run FOREIGN KEY (audit_id)
    REFERENCES lhfm_api_runs (audit_id),
  CONSTRAINT chk_audit_reconciliation_prior CHECK (prior_state = 'PROCESSING')
) ENGINE=InnoDB;
