# Implementation status – rebate kernel 0.1.0

**Status:** Local pure-Python calculation kernel; no live ERP, portal, invoice, legal recovery or production validation. Tests use synthetic data only.

## Implemented

- Independent pure-Python calculation function and a JSON CLI; no LLM, external network call or data write.
- Approved, versioned rules: flat percentage, retroactive full-base tier, marginal tier, fixed threshold reward.
- Verified precision using `decimal.Decimal` and explicit half-up cent rounding; EUR-only by design.
- Purchase/return basis, supplier, source-period, posting-status gating and source-ID deduplication.
- Settlement credits/reversals matched only with exact supplier, agreement and period. Unallocated credits cause review.
- Explicit source-evidence and completion states; a computed difference is **not** a legal claim or a billable success fee.
- Input snapshot SHA-256, deterministic output with included/excluded source identifiers and warnings.
- Reproducible offline tests and CI smoke test.

## Explicitly not implemented

- Secure multi-tenant upload and customer login, parsing PDFs, mapping Excel/CSV, business rules extraction, approval workflow UI, PDF/XLSX export, audit histories.
- A period-completeness proof independent of customer assertion; currently required flags are **customer-/operator-supplied**. Therefore the status `EVIDENCED` means a reconciliation supported by submitted evidence, **not** independent proof that all transactions or agreements exist.
- Rebate-product exclusions, currency conversion, supplier group consolidation, partial periods, cross-period credits, rule amendments and precedence, complex year-over-year bonuses, dynamic FX, statutory claim validity.
- RecoveryEvent / fee attribution / billing ledger. `billable_recovery_net` and `fee_due_net` deliberately return **0.00** at this stage; the kernel never infers realised cash from booked credits.
- Donor adapters (Docling etc.) and ERP connectors. No donor component is installed in this package.
- Independent third-party audit, real-data validation, multi-tenant security testing or customer deployment.

## Run locally

Python >=3.11, no runtime dependencies:

    python -m pip install -e .
    python -m unittest discover -s tests -v
    python -m lowhangingfruitme.cli tests/fixtures/flat_rebate.json

CLI exit code 0 = data-evidenced, 1 = needs review/not calculable, 2 = input error. Report stdout JSON. Never upload real customer data to public GitHub.

## Next acceptance gates

1. Donor trial using isolated Docling and Frictionless with traceable page/cell extraction and import quality reports.
2. Source-specific complete-period controls (running totals, supplier account matching, bounded input snapshots), signed reviewer approval of imported rule.
3. Signed engagement and recovery ledger with separate economic-realisation proof, then customer portal/API.
