-- v0.14 candidate review queue. Only verified Docling provenance is accepted.
-- Business rules are NEVER auto-approved by a parser or an LLM.
CREATE TABLE lhfm_contract_candidates (
  candidate_id CHAR(36) NOT NULL,
  tenant_id VARCHAR(128) NOT NULL,
  legal_entity_id VARCHAR(128) NOT NULL,
  reviewer_id VARCHAR(128) NOT NULL,
  contract_upload_id CHAR(36) NOT NULL,
  agreement_id VARCHAR(128) NOT NULL,
  rule_id VARCHAR(128) NOT NULL,
  rule_revision VARCHAR(128) NOT NULL,
  source_revision_id VARCHAR(128) NOT NULL,
  document_sha256 CHAR(64) NOT NULL,
  evidence_json LONGTEXT NOT NULL,
  reviewed_rule_json LONGTEXT NULL,
  reviewed_rule_sha256 CHAR(64) NULL,
  state VARCHAR(24) NOT NULL,
  approval_id VARCHAR(128) NULL,
  created_at DATETIME(6) NOT NULL DEFAULT UTC_TIMESTAMP(6),
  reviewed_at DATETIME(6) NULL,
  approved_at DATETIME(6) NULL,
  PRIMARY KEY (candidate_id),
  UNIQUE KEY uq_candidate_revision (contract_upload_id, agreement_id, rule_id, rule_revision),
  KEY idx_candidate_review (tenant_id,legal_entity_id,reviewer_id,state),
  KEY idx_candidate_approval (approval_id),
  CONSTRAINT fk_candidate_upload FOREIGN KEY (contract_upload_id) REFERENCES lhfm_uploads(upload_id),
  CONSTRAINT fk_candidate_reviewer FOREIGN KEY (tenant_id,legal_entity_id,reviewer_id)
    REFERENCES lhfm_reviewer_grants(tenant_id,legal_entity_id,reviewer_id),
  CONSTRAINT fk_candidate_approval FOREIGN KEY (approval_id) REFERENCES lhfm_approval_records(approval_id),
  CONSTRAINT chk_candidate_evidence CHECK (JSON_VALID(evidence_json)),
  CONSTRAINT chk_candidate_rule CHECK (reviewed_rule_json IS NULL OR JSON_VALID(reviewed_rule_json)),
  CONSTRAINT chk_candidate_state CHECK (
    state IN ('EXTRACTED','NEEDS_CONFIRMATION','APPROVED','SUPERSEDED','REVOKED')
  )
) ENGINE=InnoDB;

CREATE TABLE lhfm_contract_candidate_events (
  event_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  candidate_id CHAR(36) NOT NULL,
  tenant_id VARCHAR(128) NOT NULL,
  legal_entity_id VARCHAR(128) NOT NULL,
  actor_id VARCHAR(128) NOT NULL,
  event_type VARCHAR(24) NOT NULL,
  recorded_at DATETIME(6) NOT NULL DEFAULT UTC_TIMESTAMP(6),
  PRIMARY KEY (event_id),
  KEY idx_candidate_events (candidate_id,event_id),
  CONSTRAINT fk_candidate_event FOREIGN KEY (candidate_id)
    REFERENCES lhfm_contract_candidates(candidate_id),
  CONSTRAINT chk_candidate_event CHECK (
    event_type IN ('EXTRACTED','NEEDS_CONFIRMATION','APPROVED','SUPERSEDED','REVOKED')
  )
) ENGINE=InnoDB;
