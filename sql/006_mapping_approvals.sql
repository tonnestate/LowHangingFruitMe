-- LowHangingFruitMe v0.13 – signed source mapping approvals (MariaDB/InnoDB).
-- Run only on dedicated application DB via controlled migrations.
CREATE TABLE IF NOT EXISTS lhfm_mapping_approvals (
  bundle_id CHAR(36) NOT NULL,
  dataset VARCHAR(16) NOT NULL,
  tenant_id VARCHAR(128) NOT NULL,
  legal_entity_id VARCHAR(128) NOT NULL,
  reviewer_id VARCHAR(128) NOT NULL,
  approval_id VARCHAR(128) NOT NULL,
  source_sha256 CHAR(64) NOT NULL,
  mapping_sha256 CHAR(64) NOT NULL,
  receipt_sha256 CHAR(64) NOT NULL,
  state VARCHAR(12) NOT NULL,
  created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  revoked_at DATETIME(6) NULL,
  PRIMARY KEY (bundle_id, dataset),
  KEY idx_mapping_scope (tenant_id, legal_entity_id, state),
  CONSTRAINT chk_mapping_dataset CHECK (dataset IN ('transactions', 'settlements')),
  CONSTRAINT chk_mapping_state CHECK (state IN ('ACTIVE', 'REVOKED')),
  CONSTRAINT fk_mapping_reviewer FOREIGN KEY (tenant_id, legal_entity_id, reviewer_id)
    REFERENCES lhfm_reviewer_grants (tenant_id, legal_entity_id, reviewer_id),
  CONSTRAINT fk_mapping_contract_approval FOREIGN KEY (approval_id)
    REFERENCES lhfm_approval_records (approval_id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS lhfm_mapping_approval_events (
  event_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  bundle_id CHAR(36) NOT NULL,
  dataset VARCHAR(16) NOT NULL,
  tenant_id VARCHAR(128) NOT NULL,
  legal_entity_id VARCHAR(128) NOT NULL,
  actor_id VARCHAR(128) NOT NULL,
  event_type VARCHAR(16) NOT NULL,
  recorded_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (event_id),
  KEY idx_mapping_events (bundle_id, dataset, event_id),
  CONSTRAINT chk_mapping_event CHECK (event_type IN ('ISSUED','REVOKED')),
  CONSTRAINT fk_mapping_event FOREIGN KEY (bundle_id,dataset)
    REFERENCES lhfm_mapping_approvals (bundle_id,dataset)
) ENGINE=InnoDB;
