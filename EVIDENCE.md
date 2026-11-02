# Evidence ledger – LowHangingFruitMe

Last updated: 2026-11-02. This is a record of observed implementation and CI results, not a production certification.

## v0.2.0 – validated source intake

**GitHub commit tested:** [a227001d683677db928e48bd58c199cc37d9c3e2](https://github.com/tonnestate/LowHangingFruitMe/commit/a227001d683677db928e48bd58c199cc37d9c3e2)  
**Observed CI:** [GitHub Actions run 41501902562](https://github.com/tonnestate/LowHangingFruitMe/actions/runs/41501902562)  
**Result:** completed / success on the feature branch prior to fast-forward to main.

| Executed check | Python 3.11 | Python 3.12 |
|---|---|---|
| Install package with actual Frictionless dependency | PASS | PASS |
| Python compileall on source and tests | PASS | PASS |
| unittest discover: 35 tests | PASS | PASS |
| Existing JSON rebate-kernel CLI smoke | PASS | PASS |
| Canonical CSV -> Frictionless -> rebate engine CLI smoke | PASS | PASS |

**Observed synthetic sample result:** eligible base EUR 200000.00, expected bonus EUR 4000.00, recorded settlements EUR 1500.00, calculated difference EUR 2500.00; automatic billable success fee EUR 0.00. The data are synthetic; these results are **not real recovered money**.

**Defect detection in CI:** Frictionless integration first failed because an untyped schema dict was passed in place of an internal Schema object. A second failure revealed the field-type constructor requirement. A third failure was the Frictionless unsafe-absolute-path protection. Fixed by using Schema.from_descriptor and a relative resource path with an explicit basepath. The successful run above validates the actual corrected path on both Python versions.

## Verification boundaries

- PDF/Docling: source adapter and mocked document-normalization tests passed, but no real-model or real-document Docling conversion has been executed or benchmarked in this run. Model licensing, OCR quality and runtime resource use remain open.
- CSV: strict canonical format tested with actual Frictionless, but no XLSX, XML, external ERP format, production data or customer-specific column mapping.
- Completeness flags remain operator/customer assertions. They are not independent ERP ledger completeness evidence.
- No secure multi-tenant customer portal, HTTP API, ERP integration, deployment, billing ledger or RDG/legal approval.
- No real-money recovery and no claim of commercial success.

Before any production release: dependency lock/SBOM, malware-safe upload architecture, tenant and access isolation, realistic documents, invoice provenance, financial subject-matter acceptance and legal review.

## v0.1.0 – core calculation

Original deterministic Decimal-based calculation slice contains 19 synthetic regression tests; source remains part of v0.2.0. These tests are executed again within the 35-test CI suite above.

This ledger is updated only with concrete executed SHA, run ID and observed result, never with an unexecuted planned test.

## Reproducible distribution check on main

**Verified commit:** [136a189c9f92433d54a5e5a2f8618bd419a4ad20](https://github.com/tonnestate/LowHangingFruitMe/commit/136a189c9f92433d54a5e5a2f8618bd419a4ad20)  
**GitHub Actions:** [41502347254](https://github.com/tonnestate/LowHangingFruitMe/actions/runs/41502347254) — completed / success.

On **both Python 3.11 and 3.12**, the runner actually installed the package with Frictionless, executed 35 tests, exercised both CLI paths, built an sdist and wheel, and installed the wheel in a fresh virtual environment followed by a kernel smoke test. These are packaging and synthetic software-verification results, not claims about live ERP connectivity, customer data or Docling model performance.

## Data-Readiness Gate v0.3.0 – verified on main

**Source tested:** [571f8503a254aba58f09295865b0aa49ee88a7bb](https://github.com/tonnestate/LowHangingFruitMe/commit/571f8503a254aba58f09295865b0aa49ee88a7bb)  
**GitHub Actions run:** [41505245535](https://github.com/tonnestate/LowHangingFruitMe/actions/runs/41505245535) – completed / success.

Both Python 3.11 and 3.12 runners successfully installed real Frictionless, compiled source/tests, ran **52 unit/integration tests**, completed JSON and CSV CLI smoke checks, built wheel + sdist and performed fresh-wheel installation smoke checks. Tests included matching source controls, missing controls, a control-total mismatch preventing calculation, unsupported supplier/period and unapproved rule.

**Observed limitation:** The control values are independently *supplied* (as a separate document) but their ERP origin is **not independently verified** by the code. A READY_FOR_AUDIT result means the provided controls match the provided data, never a certification of the underlying customer's complete accounting history. The source control manifest can be forged or circular. Real ERP reporting metadata, independent account reconciliation and approved reviewer identity are separate future release gates.

**CI defect found and resolved:** The initial smoke test used a different `source_system` identifier than the control fixture; it was corrected without bypassing the consistency check. In the successful run, the source identity matches exactly. Synthetic tests are not evidence of recovered customer money.
