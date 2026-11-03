-- Append-only finance-attested recovery status directives, never financial claims.
-- MariaDB 11.4, dedicated LowHangingFruitMe schema, production requires migration approval.
CREATE TABLE IF NOT EXISTS lhfm_recovery_case_status_events (
  event_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  case_id CHAR(36) NOT NULL,
  tenant_id VARCHAR(128) NOT NULL,
  legal_entity_id VARCHAR(128) NOT NULL,
  finance_actor_id VARCHAR(128) NOT NULL,
  directive VARCHAR(16) NOT NULL,
  reason VARCHAR(200) NOT NULL,
  recorded_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (event_id),
  KEY idx_case_latest_state (case_id, event_id),
  CONSTRAINT fk_case_status_case FOREIGN KEY (case_id)
    REFERENCES lhfm_recovery_cases(case_id),
  CONSTRAINT chk_case_directive CHECK (directive IN ('DISPUTED','CLOSED','OPEN')),
  CONSTRAINT chk_case_status_reason CHECK (CHAR_LENGTH(reason) > 0)
) ENGINE=InnoDB;
