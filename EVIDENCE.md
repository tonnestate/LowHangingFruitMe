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

## Contract-source-bound rule approval v0.4.0 (implemented and CI validated)

**Tested commit:** [6119d3172e0196d5e8c5cd8297d95b0fcbb69a4d](https://github.com/tonnestate/LowHangingFruitMe/commit/6119d3172e0196d5e8c5cd8297d95b0fcbb69a4d)  
**GitHub Actions run:** [41516848479](https://github.com/tonnestate/LowHangingFruitMe/actions/runs/41516848479) – success on main.

Executed on Python 3.11 and Python 3.12:
- **72 unit/integration tests** per runner – passed.
- Actual Frictionless integration, compile check, unapproved JSON calculator preview, sign-and-verify synthetic approval for canonical CSV audit, source import CLI – passed.
- Source distribution and wheel builds, clean wheel installation plus preview smoke – passed.
- Tests cover HMAC signature tampering, rule amount/revision/source-reference mutation, wrong document digest, wrong tenant/company, future-dated approval, unapproved or uncited rule, missing key and missing proof.

**Hard limitation:** The receipt's listed reviewer is not authenticated by this standalone module; there is no database of authorized reviewers, no revocation store, no persistent approved source registry and no production-grade key management. CI creates a random key for each run and a fictitious signer solely for synthetic testing. A signed receipt alone does not authenticate a real employee or establish a legally enforceable claim. Do not expose the signing function publicly.

## v0.5.0 – MariaDB-based approval registry

The source includes `ApprovalRegistry.register()`, `revoke()` and `guard()`, plus dedicated InnoDB DDL and real MariaDB CI tests. The registry is intentionally isolated from any existing TonnEstate database. The GitHub Actions CI creates `lhfm_test` with synthetic grants, using no customer data.

**Validation status:** See the newest GitHub Actions run for the current main SHA. An authenticated real identity-provider connection and production reviewer authorization are **not** implemented. The registry is not a legally compliant signature/consent service by itself.

### Verified database acceptance (real MariaDB 11.4)

- Commit tested: [7591f49cbb71b6be6145e343d74bbfa92233e557](https://github.com/tonnestate/LowHangingFruitMe/commit/7591f49cbb71b6be6145e343d74bbfa92233e557)
- Workflow: [GitHub Actions 41521838285](https://github.com/tonnestate/LowHangingFruitMe/actions/runs/41521838285) – **completed/success** for Python 3.11 and 3.12.
- **81 tests**, successful on both matrix versions. Both runners used an actual isolated MariaDB 11.4 service, synthetic reviewer grant, registration, revocation and locking checks. Frictionless import, approved CSV CLI smoke, wheel/sdist build and clean wheel installation smoke also passed.
- Concurrent revoke test deliberately attempts a revoke while an audit holds the InnoDB row lock. The revoke does not complete inside the protected interval and succeeds after guard release.
- Limitations: no real IdP, real finance transactions, legal contract verification, authorized reviewer onboarding, production database and no external penetration test.


## v0.6.0 – RSA JWT access authentication and signed approval service

**Executed integration commit:** [d07f2a91f05173a15da408e27a22b7660280aaa4](https://github.com/tonnestate/LowHangingFruitMe/commit/d07f2a91f05173a15da408e27a22b7660280aaa4)  
**Actual run:** [GitHub Actions 41523377852](https://github.com/tonnestate/LowHangingFruitMe/actions/runs/41523377852) — completed / success.

Under **Python 3.11 and Python 3.12, 103 tests passed** on each runner. Executed real RSA-signature validation with private keys generated only in test memory, actual MariaDB role/approval/revocation checks, authenticated synthetic CSV-to-rebate audit, token recheck at dispatch, canonical CSV CLI smoke, wheel and sdist build and clean-wheel installation smoke.

Observed negative tests include modified RSA token, wrong issuer/audience/client/key ID, ID token confusion, expiry or excessive lifetime, missing scopes and required claims, cross-tenant permission failure, malicious JOSE key URL, revoked approval and second authorization failure at dispatch.

**Important boundary:** No real external identity-provider login occurred. The simulated issuer's RSA private key was generated by CI tests, not obtained from an IdP. Static JWKS key loading, provisioned role grants and session/credential life cycle are not yet validated as an operated service. No publicly accessible app or customer data were involved.

## v0.7.0 – export-first intake implementation

**Tested source commit:** [bdc89664ecb9033d2426bda2ecc722619afb8f18](https://github.com/tonnestate/LowHangingFruitMe/commit/bdc89664ecb9033d2426bda2ecc722619afb8f18)  
**Observed GitHub Actions:** [41532836887](https://github.com/tonnestate/LowHangingFruitMe/actions/runs/41532836887) — completed / success.

On Python **3.11 and 3.12**, **136 tests** passed per runner, including real Frictionless and MariaDB, CSV and XLSX format/locale/mapping tests, XRechnung-style root classification and malicious XML rejection, end-to-end canonical export-to-signed-audit, CLI smoke of existing CSV audit, and installation from a built wheel.

The new `inspect-source`/`normalize-source` CLI commands were added in a later commit and are subject to a subsequent full CI run and explicit CLI test. This evidence line does **not** claim those later commands were part of run 41532836887.

**No real ERP-system or third-party SOC 2 verification**: DistroAgents' reference to ERP compatibility and SOC 2 Type II on their website does not transfer to LowHangingFruitMe. Only offline local importer adapters were tested, with synthetic records and reviewer assertions.

### v0.7.0 final verification including public intake commands

**Final code and documentation commit:** [cfe53ea53d75340726a2240914fe19c875e54c0d](https://github.com/tonnestate/LowHangingFruitMe/commit/cfe53ea53d75340726a2240914fe19c875e54c0d)  
**GitHub Actions:** [41533241153](https://github.com/tonnestate/LowHangingFruitMe/actions/runs/41533241153) — completed / success on main.

**140 tests passed on each of Python 3.11 and 3.12.** The expanded tests explicitly invoke `lhfm inspect-source` and `lhfm normalize-source` as subprocesses against synthetic German-format ERP exports, check source-hash-bound reviewed mapping and refusal to overwrite existing output. The workflows also passed existing MariaDB/Frictionless audit smoke, wheel/sdist build and fresh-wheel installation.

No vendor-specific P21/Eclipse/NetSuite/SAP/Infor/Sage/Lexware/Odoo connector tests, real invoice XML parsing, external SOC 2 attestation, or production customer document imports were executed in this run.

## Marketing portal 0.1.0 – real browser/build evidence (2026-11-03)

**Verified code commit:** [5f30a4bf0cd638e63c9fda53a9c3c19de0f8ed2f](https://github.com/tonnestate/LowHangingFruitMe/commit/5f30a4bf0cd638e63c9fda53a9c3c19de0f8ed2f)  
**GitHub Actions workflow:** [41586331503](https://github.com/tonnestate/LowHangingFruitMe/actions/runs/41586331503) — **completed / success**.

- `npm test`: **7 passed**, includes 3% fee integer-cent arithmetic, original banner hash equivalence, measured pixel-derived CSS and dark/light contrast, and staged/public legal gate refusal.
- `npm run build`: successful on Next.js 16; `npm run typecheck`: successful; standalone static/public assets packaged for separate Node server.
- `npm run test:e2e`: **12 passed** on headless Chromium; actual viewports 1440, 768 and 390 pixels. Tests cover rendered page/visible original banner, fee display, responsive mobile/desktop navigation, openable FAQ, proper 404 and non-indexable staging `robots.txt`/meta. Screenshot and measured-brand JSON uploaded as workflow artifacts.
- Original PNG verified from source at build: **1983 × 793 pixels**, SHA-256 `1525d2f792a9e5fd8aee4f564f34ba048b33fe37956204fff108f7b49f5b797c`. Generated brand measurement report records original pixel coordinates and colors; no guessed HEX tokens claimed.
- Production Apache, WordPress, DNS, server ports and SSL certificates were **not touched**. No customer marketing leads, financial data or live ERP accounts were used. This is staging build evidence only, not proof of deployed live website.
- DistroAgents visual pixel-matching or interaction reverse engineering in the *reference's live browser* remains open. We tested our own website, not a 1:1 reproduction.
