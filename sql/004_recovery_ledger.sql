-- LowHangingFruitMe v0.11 Recovery Ledger – dedicated application MariaDB only.
-- Finance verification role is provisioned OUT OF BAND by a trusted operator.
CREATE TABLE IF NOT EXISTS lhfm_finance_grants (
  tenant_id VARCHAR(128) NOT NULL,
  legal_entity_id VARCHAR(128) NOT NULL,
  finance_actor_id VARCHAR(128) NOT NULL,
  active BOOLEAN NOT NULL DEFAULT FALSE,
  PRIMARY KEY (tenant_id, legal_entity_id, finance_actor_id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS lhfm_recovery_cases (
  case_id CHAR(36) NOT NULL,
  audit_id CHAR(36) NOT NULL,
  tenant_id VARCHAR(128) NOT NULL,
  legal_entity_id VARCHAR(128) NOT NULL,
  reviewer_id VARCHAR(128) NOT NULL,
  claim_sha256 CHAR(64) NOT NULL,
  difference_cents BIGINT NOT NULL,
  created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (case_id),
  UNIQUE KEY uq_case_audit (audit_id),
  UNIQUE KEY uq_claim (tenant_id, legal_entity_id, claim_sha256),
  CONSTRAINT fk_case_audit FOREIGN KEY (audit_id) REFERENCES lhfm_api_runs(audit_id),
  CONSTRAINT chk_difference_positive CHECK (difference_cents > 0)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS lhfm_recovery_events (
  event_id CHAR(36) NOT NULL,
  case_id CHAR(36) NOT NULL,
  tenant_id VARCHAR(128) NOT NULL,
  legal_entity_id VARCHAR(128) NOT NULL,
  reporter_id VARCHAR(128) NOT NULL,
  kind VARCHAR(16) NOT NULL,
  amount_cents BIGINT NOT NULL,
  evidence_upload_id CHAR(36) NOT NULL,
  reverses_event_id CHAR(36) NULL,
  request_sha256 CHAR(64) NOT NULL,
  idempotency_key CHAR(36) NOT NULL,
  state VARCHAR(16) NOT NULL,
  verified_by VARCHAR(128) NULL,
  verified_at DATETIME(6) NULL,
  created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (event_id),
  UNIQUE KEY uq_event_idempotency (case_id, idempotency_key),
  UNIQUE KEY uq_evidence_once (tenant_id, legal_entity_id, evidence_upload_id),
  KEY idx_case_events (case_id, state, kind),
  CONSTRAINT fk_event_case FOREIGN KEY (case_id) REFERENCES lhfm_recovery_cases(case_id),
  CONSTRAINT fk_reversed_event FOREIGN KEY (reverses_event_id) REFERENCES lhfm_recovery_events(event_id),
  CONSTRAINT chk_event_kind CHECK (kind IN ('REALIZATION','REVERSAL')),
  CONSTRAINT chk_event_state CHECK (state IN ('REPORTED','CONFIRMED','REJECTED')),
  CONSTRAINT chk_event_amount CHECK (amount_cents > 0)
) ENGINE=InnoDB;
