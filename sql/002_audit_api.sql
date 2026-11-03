-- LowHangingFruitMe API audit bundles and runs (dedicated lhfm_test / dedicated app DB).
-- No tenant is inferred from an HTTP path; the service validates JWT + DB grant.
-- Execute through controlled migration, never implicitly on HTTP startup.
CREATE TABLE IF NOT EXISTS lhfm_api_bundles (
  bundle_id CHAR(36) NOT NULL,
  tenant_id VARCHAR(128) NOT NULL,
  legal_entity_id VARCHAR(128) NOT NULL,
  manifest_json LONGTEXT NOT NULL,
  created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (bundle_id),
  UNIQUE KEY uq_bundle_scope (bundle_id, tenant_id, legal_entity_id),
  CONSTRAINT chk_manifest_json CHECK (JSON_VALID(manifest_json))
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS lhfm_api_runs (
  audit_id CHAR(36) NOT NULL,
  tenant_id VARCHAR(128) NOT NULL,
  legal_entity_id VARCHAR(128) NOT NULL,
  reviewer_id VARCHAR(128) NOT NULL,
  bundle_id CHAR(36) NOT NULL,
  idempotency_key CHAR(36) NOT NULL,
  request_sha256 CHAR(64) NOT NULL,
  status VARCHAR(20) NOT NULL,
  audit_executed BOOLEAN NOT NULL DEFAULT 0,
  report_json LONGTEXT NULL,
  started_at DATETIME(6) NOT NULL DEFAULT UTC_TIMESTAMP(6),
  finished_at DATETIME(6) NULL,
  PRIMARY KEY (audit_id),
  UNIQUE KEY uq_idempotency (tenant_id, legal_entity_id, reviewer_id, idempotency_key),
  KEY idx_audit_scope (tenant_id, legal_entity_id, reviewer_id, started_at),
  CONSTRAINT fk_api_bundle_scope FOREIGN KEY (bundle_id, tenant_id, legal_entity_id)
    REFERENCES lhfm_api_bundles (bundle_id, tenant_id, legal_entity_id),
  CONSTRAINT chk_api_run_status CHECK (
    status IN ('PROCESSING','NEEDS_REVIEW','COMPLETED','FAILED')
  ),
  CONSTRAINT chk_api_report_json CHECK (report_json IS NULL OR JSON_VALID(report_json))
) ENGINE=InnoDB;
