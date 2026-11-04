-- v0.18: bounded housekeeping of abandoned, unapproved upload intents.
-- No customer CLEAN file or financial evidence is eligible for deletion.
ALTER TABLE lhfm_uploads
  ADD KEY idx_upload_housekeeping (state, expires_at, upload_id);

CREATE TABLE lhfm_upload_housekeeping_events (
  event_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  upload_id CHAR(36) NOT NULL,
  prior_state VARCHAR(16) NOT NULL,
  removed_partials TINYINT UNSIGNED NOT NULL DEFAULT 0,
  recorded_at DATETIME(6) NOT NULL DEFAULT UTC_TIMESTAMP(6),
  PRIMARY KEY (event_id),
  UNIQUE KEY uq_housekeeping_upload (upload_id),
  CONSTRAINT fk_housekeeping_upload FOREIGN KEY (upload_id) REFERENCES lhfm_uploads(upload_id),
  CONSTRAINT chk_housekeeping_prior CHECK (prior_state IN ('PENDING','RECEIVING')),
  CONSTRAINT chk_housekeeping_partials CHECK (removed_partials <= 2)
) ENGINE=InnoDB;
