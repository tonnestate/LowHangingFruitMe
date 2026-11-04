-- v0.15: audited billing handoff, NOT an invoice or a debt collection service.
-- Commercial terms and billing grants MUST be provisioned out-of-band by
-- separately authorized operators after a genuine customer/legal review.
CREATE TABLE lhfm_billing_grants (
  tenant_id VARCHAR(128) NOT NULL,
  legal_entity_id VARCHAR(128) NOT NULL,
  billing_actor_id VARCHAR(128) NOT NULL,
  active BOOLEAN NOT NULL DEFAULT FALSE,
  PRIMARY KEY (tenant_id, legal_entity_id, billing_actor_id)
) ENGINE=InnoDB;

CREATE TABLE lhfm_commercial_terms (
  tenant_id VARCHAR(128) NOT NULL,
  legal_entity_id VARCHAR(128) NOT NULL,
  agreement_id VARCHAR(128) NOT NULL,
  accepted_terms_sha256 CHAR(64) NOT NULL,
  acceptance_evidence_ref VARCHAR(200) NOT NULL,
  legal_clearance_sha256 CHAR(64) NOT NULL,
  legal_clearance_ref VARCHAR(200) NOT NULL,
  fee_rate_bps SMALLINT UNSIGNED NOT NULL,
  active BOOLEAN NOT NULL DEFAULT FALSE,
  verified_by VARCHAR(128) NOT NULL,
  accepted_at DATETIME(6) NOT NULL,
  checked_at DATETIME(6) NOT NULL,
  PRIMARY KEY (tenant_id,legal_entity_id,agreement_id),
  CONSTRAINT chk_commercial_fee_rate CHECK (fee_rate_bps IN (300,500)),
  CONSTRAINT chk_commercial_provenance CHECK (
    CHAR_LENGTH(acceptance_evidence_ref)>0 AND
    CHAR_LENGTH(legal_clearance_ref)>0 AND CHAR_LENGTH(verified_by)>0
  )
) ENGINE=InnoDB;

CREATE TABLE lhfm_billing_packets (
  packet_id CHAR(36) NOT NULL,
  case_id CHAR(36) NOT NULL,
  tenant_id VARCHAR(128) NOT NULL,
  legal_entity_id VARCHAR(128) NOT NULL,
  agreement_id VARCHAR(128) NOT NULL,
  created_by VARCHAR(128) NOT NULL,
  released_by VARCHAR(128) NULL,
  voided_by VARCHAR(128) NULL,
  void_reason VARCHAR(200) NULL,
  external_correction_ref VARCHAR(200) NULL,
  net_realization_cents BIGINT NOT NULL,
  fee_cents BIGINT NOT NULL,
  fee_rate_bps SMALLINT UNSIGNED NOT NULL,
  accepted_terms_sha256 CHAR(64) NOT NULL,
  legal_clearance_sha256 CHAR(64) NOT NULL,
  ledger_sha256 CHAR(64) NOT NULL,
  evidence_json LONGTEXT NOT NULL,
  state VARCHAR(16) NOT NULL,
  created_at DATETIME(6) NOT NULL DEFAULT UTC_TIMESTAMP(6),
  released_at DATETIME(6) NULL,
  voided_at DATETIME(6) NULL,
  PRIMARY KEY (packet_id),
  UNIQUE KEY uq_billing_packet_snapshot (case_id,ledger_sha256),
  KEY idx_billing_case_history (case_id,created_at),
  CONSTRAINT fk_billing_packet_case FOREIGN KEY (case_id)
    REFERENCES lhfm_recovery_cases(case_id),
  CONSTRAINT fk_billing_packet_creator FOREIGN KEY
    (tenant_id,legal_entity_id,created_by)
    REFERENCES lhfm_billing_grants(tenant_id,legal_entity_id,billing_actor_id),
  CONSTRAINT chk_billing_packet_state CHECK (state IN ('PREPARED','RELEASED','VOIDED')),
  CONSTRAINT chk_billing_packet_fee CHECK (
    net_realization_cents>0 AND fee_cents>=0 AND fee_rate_bps IN (300,500)
  ),
  CONSTRAINT chk_billing_packet_json CHECK (JSON_VALID(evidence_json))
) ENGINE=InnoDB;

CREATE TABLE lhfm_billing_packet_events (
  event_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  packet_id CHAR(36) NOT NULL,
  tenant_id VARCHAR(128) NOT NULL,
  legal_entity_id VARCHAR(128) NOT NULL,
  billing_actor_id VARCHAR(128) NOT NULL,
  event_type VARCHAR(16) NOT NULL,
  reason VARCHAR(200) NULL,
  recorded_at DATETIME(6) NOT NULL DEFAULT UTC_TIMESTAMP(6),
  PRIMARY KEY (event_id),
  KEY idx_packet_event_chain (packet_id,event_id),
  CONSTRAINT fk_billing_event_packet FOREIGN KEY (packet_id)
    REFERENCES lhfm_billing_packets(packet_id),
  CONSTRAINT chk_billing_event_type CHECK (event_type IN ('PREPARED','RELEASED','VOIDED'))
) ENGINE=InnoDB;
