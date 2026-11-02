# Universal intake architecture – 0.7.0 (source export first)

## Verified reference and non-claims

DistroAgents publicly states that it works beside an ERP instead of inside it, naming P21, Eclipse, NetSuite, SAP, Infor and Sage, using **read-only access or pure data exports**. Its rebate page describes PDFs of agreements and CSV invoice extracts. These are the provider's claims, not independent confirmation that all six systems have shipping connectors. Sources:

- https://distroagents.com/
- https://distroagents.com/rebate-recovery

The same pages advertise **SOC 2 Type II**. LowHangingFruitMe does **not** possess that report or any equivalent examination. Do not use a SOC 2 badge, claim certification or imply external auditor approval of this repo. Type II requires an external CPA report on controls tested across a defined period; see https://www.aicpa.com/resources/download/illustrative-soc-2-r-report-with-description-and-assertion.

## Commercially important architecture

Primary customer path: ERP export → source upload → file classification → proposed schema mapping → **explicit reviewer confirmation** → canonical normalized dataset with original file hash/row references → independent control-total reconciliation → authenticated source-bound rule approval → deterministic audit → evidence report.

Recurring customer path: approved read-only connector → immutable source snapshot → **same pipeline**. Connector names are **source-system compatibility targets**, not existing modules.

This is **not** an ERP replacement. Never request write access to accounting ledgers and never automatically write claims, credits or journal entries to a source ERP. Prefer read-only permissioned credentials. Product scope covers whole agreement periods, not a universal 90-day window.

## What code actually does

`src/lowhangingfruitme/universal_import.py`:
- **CSV:** UTF-8, comma/semicolon/tab; unknown columns are accepted for inspection, duplicate headers and malformed row counts are rejected.
- **XLSX:** one expressly selected worksheet (or a single-sheet workbook), read-only parser, formula cells rejected instead of trusting cached values.
- **XML invoice:** safe classification of XML roots Invoice/CreditNote/CrossIndustryInvoice using defusedxml; **does not** extract an XRechnung or CII amount into a booked ERP transaction.
- **PDF/DOCX:** signature/layout check and document-route classification only. The existing optional Docling PDF reader is a separate prototype; no real-document OCR acceptance benchmark has passed.
- **Mapping:** stable aliases for common DE/EN headers create *suggestions only*. Each normalization requires a source SHA-256-bound complete mapping plan, named reviewer assertion and explicit date, amount and boolean locale settings.
- **Guardrails:** identity/date/amount/posting status must be actual source fields; settlement agreement and periods must be actual source fields; arbitrary constants cannot silently invent missing reconciliation details.
- **Audit integration:** `audit_from_sources()` calls the **existing** Frictionless CSV, Readiness Gate, HMAC, MariaDB registry and row-locked calculation. No independent permissive calculator has been created.

All sample data are synthetic. `normalized=True` means structurally parsed, not commercially approved. No independent proof of vendor export completeness; a customer-supplied separate control file can still be incomplete.

## Run locally (not a public upload service)

Install:

```bash
python -m pip install -e ".[import,registry,auth,universal]"
lhfm inspect-source --file my_erp_export.csv --dataset transactions
lhfm inspect-source --file my_invoice.xml
```

For structured data, review the suggested mapping, source file hash, field meanings and currency/period controls. Create a plan JSON with **exactly** the following fields:

```json
{
  "source_sha256": "64 lowercase hexadecimal characters from inspect-source",
  "dataset": "transactions",
  "mapping": {
    "external_id": "Belegnummer",
    "supplier_id": "Kreditor",
    "date": "Belegdatum",
    "amount_net": "Nettobetrag",
    "posted": "Gebucht",
    "kind": "Belegart"
  },
  "constants": {"currency": "EUR", "basis": "INVOICE"},
  "sheet_name": null,
  "decimal_format": "DE",
  "date_format": "DE",
  "boolean_format": "DE",
  "reviewed_by": "documented-reviewer-id",
  "confirmed": true
}
```

Then:

```bash
lhfm normalize-source --file my_erp_export.csv --dataset transactions --source-system erp --plan reviewed_plan.json --output transactions.canonical.csv
```

The CLI refuses to overwrite an existing output. The generated CSV remains **an intermediate staging artefact, not an auditable claim**. Store its mapping and original source lineage with the eventual audit result.

## ERP targets – no connector yet

| ERP | Position | Current technical implementation |
|---|---|---|
| Epicor Prophet 21 (P21), Eclipse | Evidence that DistroAgents targets them | Generic CSV/XLSX exports only; no tested vendor format or connector |
| NetSuite | Vendor-specific connector later, official REST API possible subject to role permissions | Generic exports only; no live NetSuite permissions tested |
| SAP | Multiple products/editions, mappings are tenant-specific | Generic exports only |
| Infor | Multiple products/editions; version/tenant-dependent API and exports | Generic exports only |
| Sage | Product family varies substantially | Generic exports only |
| Lexware Office | German pilot/partner priority if sufficient invoice-item data available | Generic exports only |
| Odoo | Planned Odoo.sh/self-hosted module + thin API adapter | Generic exports only |

Do **not** publish badges claiming native connection or compatibility with the above ERPs without real export fixtures and connector tests.

## Audit and compliance gap

DistroAgents' SOC 2 assertion is useful competitive context, **not** authorization for us to advertise SOC 2. Before soliciting actual financial customer data: hardened upload scanning, isolated PDF/Office parsing, authenticated tenant isolation, content encryption, immutable source snapshots, per-tenant retention/erasure, least-privilege access, key management/rotation, security logging, backup restoration, incident response, lawful contractual data processing and independent controls examination planning. A Type II report is optional only after the relevant controls have operated for the examination period.

Until these controls exist, local CLI operations should use non-sensitive synthetic data, never public multi-tenant uploads.
