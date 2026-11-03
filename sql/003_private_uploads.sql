-- v0.9 private upload intake. Apply only to dedicated LowHangingFruitMe DB.
-- Every state transition uses a scoped, conditional UPDATE. No HTTP migrations.
CREATE TABLE IF NOT EXISTS lhfm_uploads (
  upload_id CHAR(36) NOT NULL,
  tenant_id VARCHAR(128) NOT NULL,
  legal_entity_id VARCHAR(128) NOT NULL,
  reviewer_id VARCHAR(128) NOT NULL,
  kind VARCHAR(24) NOT NULL,
  expected_size BIGINT UNSIGNED NOT NULL,
  expected_sha256 CHAR(64) NOT NULL,
  state VARCHAR(16) NOT NULL,
  created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  expires_at DATETIME(6) NOT NULL,
  finished_at DATETIME(6) NULL,
  PRIMARY KEY (upload_id),
  KEY idx_upload_scope (tenant_id, legal_entity_id, reviewer_id, created_at),
  CONSTRAINT chk_upload_state CHECK (state IN ('PENDING','RECEIVING','CLEAN','REJECTED')),
  CONSTRAINT chk_upload_kind CHECK (kind IN (
    'ERP_CSV','ERP_XLSX','INVOICE_XML','CONTRACT_PDF','CONTRACT_DOCX','RECOVERY_PDF'
  )),
  CONSTRAINT chk_upload_size CHECK (expected_size BETWEEN 1 AND 16777216)
) ENGINE=InnoDB;
