-- v0.13.1: preserve existing 3% recovery cases on upgrade; 5% on NEW cases only.
-- Apply after sql/004_recovery_ledger.sql on the dedicated LowHangingFruitMe DB.
-- Existing rows receive 300 bps; insertion now explicitly writes 500 bps.
-- An accepted commercial fee agreement is NOT established by this migration.
ALTER TABLE lhfm_recovery_cases
  ADD COLUMN fee_rate_bps SMALLINT UNSIGNED NOT NULL DEFAULT 300,
  ADD CONSTRAINT chk_case_fee_rate CHECK (fee_rate_bps IN (300,500));
