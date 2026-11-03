# Data Readiness – gate v0.3.0

## Measurable audit-level visibility (specified 03.11.2026)

The commercial UX must distinguish a gate verdict from measurement. Planned explicit fields:

- **data_coverage_pct**: bounded count of imported purchase/credit rows against independently supplied ERP *report* denominators, **null** if no valid denominator; not proof of completeness of the original ERP
- **rule_clarity_pct**: number of source-cited and independently human-approved applicable calculation semantics divided by known expected rule count; **null** if the rule universe is unknown; never an LLM confidence score
- **reconciliation_completeness_pct**: percentage of required purchase/settlement control pairs that match by **both row count and net sum**; **null** when no usable controls are supplied
- **blocking reasons**: exact `issues[].code`, affected dataset, requested action; no numeric percentage can bypass existing financial gates

Pilot target: at least **95% value-weighted** purchase coverage and at most **10% relevant rows** remaining in NEEDS_DATA/NEEDS_REVIEW. These are preliminary *pilot intake* thresholds only. An `EVIDENCED` financial finding still requires no relevant unresolved exclusions, explicit verified approval, and exact reconciliation to supplied control reports. External ERP report completeness continues to be **unverified** until separate source-level attestation/validation.

## Purpose and boundaries

The data-readiness check is the first technical prerequisite for generating a canonical CSV supplier-bonus audit. It is **not** a legal assessment of entitlement, accounting certification, fraud detector, financial advice, proof that the customer delivered all supplier data, or a numerical readiness score.

Outcomes:

| Gate status | Meaning | Next step |
|---|---|---|
| READY_FOR_AUDIT | Submitted data are internally valid, the rule has a verified signed approval receipt bound to the exact contract-document digest, and supplied ERP control-report row counts and net sums reconcile exactly, required scope and completeness attestations are present | Run deterministic calculation; retain all caveats |
| LIMITED | No hard contradiction, but separate control totals or completeness attestations are missing | Request missing evidence; return diagnostics without a calculated claim |
| NOT_READY | A material contradiction exists, such as mismatched net total/row count, unknown credit allocation, wrong supplier, unposted transactions, missing rule evidence or unapproved rule | Correct/re-export or authorize review; do **not** compute a difference |

All three statuses include `external_ledger_completeness_proven=false`. A control file provided by the same customer may still omit source records; comparing two customer-supplied numbers is not a third-party audit.

## Mandatory approval gate since v0.4.0

An `approved=true` rule flag is not trusted. A canonical CSV audit also requires a signed HMAC-SHA256 approval receipt, a current exact source-document file, a trusted HMAC key, tenant and legal-entity scopes and a matching rule revision. Missing proof produces `LIMITED` and no financial finding; a tampered/wrong-scope receipt produces `NOT_READY` and no financial finding. Direct low-level JSON calculation is explicitly review-only.

The HMAC proves message integrity if the signing key remains secret. **This prototype does not authenticate reviewers, maintain a revocation ledger or independently verify source-document authenticity.** See [RULE_APPROVAL](RULE_APPROVAL.md).

## Minimal control input

One JSON file per company, supplier, contract and contractual period:

~~~json
{
  "source_system": "erp",
  "supplier_id": "SUP-1",
  "agreement_id": "AGR-1",
  "period_start": "2025-01-01",
  "period_end": "2025-12-31",
  "transactions": {
    "row_count": 2,
    "net_total": "200000.00",
    "source_reference": "source-ledger-report-2025"
  },
  "settlements": {
    "row_count": 1,
    "net_total": "1500.00",
    "source_reference": "source-rebate-account-report-2025"
  }
}
~~~

The example is synthetic. `source_reference` is an identifier of a separately supplied report, **not proof** of authenticity. No implicit data inference is allowed. A source-control report generated from the same imported CSV is circular and provides no genuine independent cross-check.

The imported CSV is validated using real Frictionless (only canonical columns and period/amount formats) followed by the deterministic Entry parser. For each dataset, the control check compares exact row count and Decimal net amount. For settlements the source may have a later booking date, but each record must relate unambiguously to the contractual period. The first version intentionally rejects cross-supplier and cross-period batches, rather than silently excluding potentially relevant rows.

The contract rule still requires `approved=true` and clause evidence. In v0.3.0 this boolean remains an externally supplied assertion; signed/authenticated approval with user identity, immutable source revision and permissions is a separate later release gate.

## Run

Install real Frictionless, first create a **synthetic** approval using the README commands and then execute:

~~~bash
python -m pip install -e ".[import]"
lhfm audit-csv \
  --rule tests/fixtures/rule.json \
  --transactions tests/fixtures/transactions.csv \
  --settlements tests/fixtures/settlements.csv \
  --source-system erp \
  --controls tests/fixtures/source_controls.json \
  --approval /tmp/lhfm-approval.json \
  --contract-source tests/fixtures/synthetic_agreement.txt \
  --tenant-id T-SYN-1 \
  --legal-entity-id LE-SYN-1 \
  --confirm-transactions-complete \
  --confirm-settlements-complete \
  --confirm-agreements-complete
~~~

An omitted control file returns `REVIEW_REQUIRED`, `audit_executed=false` and null monetary findings. A contradiction returns `NOT_CALCULABLE`, `audit_executed=false` and null findings. Exit code 0 means successful technical calculation, 1 means review/not calculated, 2 means invalid input. The code does not send documents to a cloud model or create invoices.

## Test and audit evidence

- Test matching, omitted and contradictory control totals and immutable gate snapshot digest.
- Test false approvals, wrong source system/supplier/period, unposted values, unknown credits, duplicate records, missing source references and invalid decimal precision.
- A clean gate is **not** evidence of real accounting completeness: future control adapters must verify originating ERP total identity, reporting cut-off, export coverage, after-posting adjustments, and independent accounting reconciliation.
- All customer data must remain in a private access-controlled storage service; the current CLI is not a secure public upload platform.

The authoritative implementation is `src/lowhangingfruitme/readiness.py` and its call inside `src/lowhangingfruitme/intake.py`. No other service may bypass this gate when it represents a completed customer audit.

## v0.13 implemented technical indicators

`src/lowhangingfruitme/readiness.py` now calculates `quality_metrics`:

- `data_coverage_pct`: row count ratio **capped at 100.00** against supplied, separately referenced ERP control rows. Both numerator and denominator are exposed. This is not the intended **value-weighted** pilot metric and does not prove an ERP's completeness.
- `rule_clarity_pct`: 100.00 only if this **single-rule** scope has a valid HMAC receipt and cited explicit semantics; otherwise `null`. It does not assess legal meaning of an unverified clause.
- `reconciliation_completeness_pct`: 0/50/100 based on both expected row counts **and** net sum matching for purchase and settlement controls. Without controls, `null`.
- `blocker_codes` and `warning_codes` remain surfaced for rejection reasons. `source_ledger_completeness_proven=false` and `value_weighted_source_coverage_pct=null` are explicit even if every technical check passes.

The existing `audit_admissible` gate does not consume any of these percentages; a mismatch remains `NOT_READY` with no final monetary claim. Customer reports include indicators and their limits; staging portal shows the issue codes. Real independent reporting completeness remains to be validated.
