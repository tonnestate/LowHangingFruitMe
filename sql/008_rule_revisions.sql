-- LowHangingFruitMe v0.14 – atomically signed contract rule revisions.
-- Apply once after 001..007 to the dedicated application database.
-- Legacy active approvals receive NULL lineage metadata and MUST be reapproved:
-- the dispatch guard rejects them rather than assuming they remain current.
ALTER TABLE lhfm_approval_records
  ADD COLUMN agreement_id VARCHAR(128) NULL,
  ADD COLUMN rule_id VARCHAR(128) NULL,
  ADD COLUMN rule_revision VARCHAR(128) NULL,
  ADD COLUMN source_revision_id VARCHAR(128) NULL,
  ADD COLUMN superseded_by VARCHAR(128) NULL;

CREATE TABLE IF NOT EXISTS lhfm_rule_heads (
  tenant_id VARCHAR(128) NOT NULL,
  legal_entity_id VARCHAR(128) NOT NULL,
  agreement_id VARCHAR(128) NOT NULL,
  rule_id VARCHAR(128) NOT NULL,
  current_approval_id VARCHAR(128) NULL,
  PRIMARY KEY (tenant_id, legal_entity_id, agreement_id, rule_id),
  KEY idx_current_approval (current_approval_id),
  CONSTRAINT fk_rule_current_approval
    FOREIGN KEY (current_approval_id) REFERENCES lhfm_approval_records(approval_id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS lhfm_rule_revision_events (
  event_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  approval_id VARCHAR(128) NOT NULL,
  tenant_id VARCHAR(128) NOT NULL,
  legal_entity_id VARCHAR(128) NOT NULL,
  actor_id VARCHAR(128) NOT NULL,
  event_type VARCHAR(20) NOT NULL,
  replaced_by VARCHAR(128) NULL,
  recorded_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (event_id),
  KEY idx_rule_events (approval_id, event_id),
  CONSTRAINT chk_rule_revision_event
    CHECK (event_type IN ('APPROVED','SUPERSEDED','REVOKED')),
  CONSTRAINT fk_rule_event_approval
    FOREIGN KEY (approval_id) REFERENCES lhfm_approval_records(approval_id)
) ENGINE=InnoDB;
