# Changelog

## 0.3.0 – data-readiness and independent control-total reconciliation (development; 2026-11-02)

- Added deterministic supplier/period/contract scope gate before the canonical CSV audit.
- Requires separately supplied ERP control-report row counts and net totals for both purchasing and rebate settlements to allow the calculation path.
- Returns explicit `READY_FOR_AUDIT`, `LIMITED` or `NOT_READY` with concrete discrepancies, never a misleading readiness percentage.
- Blocks generated bonus differences if control totals are missing, ambiguous, or inconsistent; explicit customer completeness flags alone cannot grant audit admission.
- Control reports are **customer/operator supplied**, not cryptographically authenticated ERP source exports. Commercial completeness and legal claim confirmation remain unproven.
- Expanded synthetic regression tests for admission, mismatch, scope, duplicates and false completeness assertions.

## 0.2.0 – import slice (development; 2026-11-02)

- Strict source-cited Frictionless CSV importer for purchases and supplier settlement data.
- Docling local-PDF segment extraction with provenance; no automatic contractual rule approval.
- CLI, Python 3.11/3.12 CI matrix, synthetic importer tests, canonical schema and repository governance.
- Still no customer portal, Excel mapping, ERP live access, production deployment, recovery fee ledger or live customer evidence.

## 0.1.0 – deterministic calculation slice

- Decimal-based fixed and tiered supplier rebate reconciliation, signed return/credit transactions, status flags and synthetic fixture-based regression tests.
- Calculated differences deliberately do not trigger success-fee billing.
