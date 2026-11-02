-- LowHangingFruitMe 0.5 approval registry, MariaDB/InnoDB.
-- Dedicated DB/schema ONLY; do not create these tables in TonnEstate's schemas.
-- Run via controlled migration tooling; no automatic schema mutation on API requests.
CREATE TABLE IF NOT EXISTS lhfm_reviewer_grants (
  tenant_id VARCHAR(128) NOT NULL,
  legal_entity_id VARCHAR(128) NOT NULL,
  reviewer_id VARCHAR(128) NOT NULL,
  role VARCHAR(40) NOT NULL,
  active BOOLEAN NOT NULL DEFAULT FALSE,
  PRIMARY KEY (tenant_id, legal_entity_id, reviewer_id),
  CONSTRAINT chk_reviewer_role CHECK (role IN ('contract_reviewer'))
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS lhfm_approval_records (
  approval_id VARCHAR(128) NOT NULL,
  tenant_id VARCHAR(128) NOT NULL,
  legal_entity_id VARCHAR(128) NOT NULL,
  reviewer_id VARCHAR(128) NOT NULL,
  rule_sha256 CHAR(64) NOT NULL,
  document_sha256 CHAR(64) NOT NULL,
  receipt_sha256 CHAR(64) NOT NULL,
  state VARCHAR(16) NOT NULL,
  revoked_by VARCHAR(128) NULL,
  revoked_at DATETIME(6) NULL,
  created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (approval_id),
  KEY idx_scope (tenant_id, legal_entity_id, state),
  CONSTRAINT chk_approval_state CHECK (state IN ('ACTIVE','REVOKED')),
  CONSTRAINT fk_approval_reviewer FOREIGN KEY
    (tenant_id, legal_entity_id, reviewer_id)
    REFERENCES lhfm_reviewer_grants(tenant_id, legal_entity_id, reviewer_id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS lhfm_approval_events (
  event_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  approval_id VARCHAR(128) NOT NULL,
  tenant_id VARCHAR(128) NOT NULL,
  legal_entity_id VARCHAR(128) NOT NULL,
  actor_id VARCHAR(128) NOT NULL,
  event_type VARCHAR(16) NOT NULL,
  recorded_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY(event_id),
  KEY idx_approval_events(approval_id, event_id),
  CONSTRAINT chk_approval_event CHECK (event_type IN ('ISSUED','REVOKED')),
  CONSTRAINT fk_event_approval FOREIGN KEY (approval_id)
    REFERENCES lhfm_approval_records(approval_id)
) ENGINE=InnoDB;
