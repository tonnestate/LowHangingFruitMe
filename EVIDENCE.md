# Evidence ledger – LowHangingFruitMe

Last updated: 2026-11-03. This is a record of observed implementation and CI results, not a production certification.

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

## v0.8.0 – authenticated HTTP Audit API: implementation acceptance (2026-11-03)

**Executed source commit:** [80a212abe5e47bfba5ac0ad7e5f68b723a6f9495](https://github.com/tonnestate/LowHangingFruitMe/commit/80a212abe5e47bfba5ac0ad7e5f68b723a6f9495).  
**Verified GitHub Actions:** [41591509755](https://github.com/tonnestate/LowHangingFruitMe/actions/runs/41591509755) – completed/success on **both Python 3.11 and Python 3.12**.

**158 tests passed** per runner including actual MariaDB 11.4, synthetic RSA JWT verification, FastAPI TestClient, canonical Frictionless → readiness → active-registry-locked bonus calculation. New API cases prove guarded POST/GET, source hash and signer binding, 2500.00 EUR synthetic financial difference but **0.00 EUR actual recoveries or fees**, revoked approvals, missing controls, JWT scope/client/tenant denial, 404 vs 403, arbitrary HTTP source path rejection, private path traversal, symlink detection, idempotency replay/conflict and **concurrent single-reservation** under unique DB key.

The test registry `lhfm_test` and source files are synthetic; server-provisioned bundle registration is not a public upload endpoint. **No real IdP, protected tenant document storage, API deployment, virus scanning, async job worker, ERP connection, audit report download through the website or legally approved 3% billing was tested.** This is an API code acceptance, not a live-production certification.

## v0.9.0 – scoped upload staging HTTP acceptance (2026-11-03)

**Executed code commit:** [ecc923cb6d1bfe475ae1b3658429f10cd13287e0](https://github.com/tonnestate/LowHangingFruitMe/commit/ecc923cb6d1bfe475ae1b3658429f10cd13287e0).  
**Verified CI:** [41593011185](https://github.com/tonnestate/LowHangingFruitMe/actions/runs/41593011185) – **completed/success** under Python **3.11 and 3.12**; **175 tests passed per runner** including real MariaDB.

The upload tests cover JWT bearer and scoped grant, unauthorized cross-tenant/actor access, new intent, size and SHA256-bound byte stream, 0600 private file, status GET, no financial-audit bypass, single-writer claim under concurrent requests, expired reservation, tampered/oversized/repeated PUT, invalid content type, malicious invoice XML, malformed PDF, scanner infection/outage fail-closed and no residual file. A fake local clamd-compatible UNIX socket verifies the INSTREAM frame structure. Existing 158 API/kernel tests also pass.

**Limitations:** These tests use a **test-only scanner double**, not a running real ClamAV service or detection efficacy benchmark. A fake UNIX socket protocol implementation also does not prove real daemon configuration, security operations or updated virus signatures. The marketing portal is not connected to a live upload API; no customer upload on the VPS, no encryption at rest and no scope-approved dataset promotion. No external SaaS, billing or ERP integration was exercised.

## 0.12.0 workstream – 03.11.2026

**Confirmed passing code before single-command addition:** [GitHub Actions 41607305907](https://github.com/tonnestate/LowHangingFruitMe/actions/runs/41607305907) (Python), [GitHub Actions 41607305839](https://github.com/tonnestate/LowHangingFruitMe/actions/runs/41607305839) (Portal), commit `8295b1c874709ef19459661e588c0f42a30aaf80`. Both completed successfully. This includes authenticated report download and finance-ledger status controls, and a real PostgreSQL-free MariaDB test service with synthetic sources.

**Later commits** introduced the one-command `audit-sources` and explicit `calculated_variance_net`; their own final status must be read from GitHub Actions, not inferred from the earlier success. Original financial fixtures remain synthetic. Manual goldstandard is independently described in [docs/PILOT_GOLDSTANDARD.md](docs/PILOT_GOLDSTANDARD.md).

No positive claim about actual bank-realized customer money, real customer portal login, live ClamAV on VPS, successful external ERP connection, DOCX/PDF model extraction quality or permission to bill. 

### v0.12.0 acceptance – full integration and one-command path

**Observed latest full code-release CI:** [GitHub Actions 41608125460](https://github.com/tonnestate/LowHangingFruitMe/actions/runs/41608125460), commit [af15f95ea7629da9426e43d01c5bc6ddfe0f97ac](https://github.com/tonnestate/LowHangingFruitMe/commit/af15f95ea7629da9426e43d01c5bc6ddfe0f97ac). **Completed / success**.

- Python 3.11: **261 tests passed**, including real isolated MariaDB, proof-linked recovery ledger, finance-only case status, one-command signed ERP CSV/XLSX source audit, PDF/XLSX/JSON downloaded report, scoped API and safety-negative cases.
- Python 3.12: **261 tests passed**, same test matrix and independent runner.
- Existing CLI smoke, build of installable wheel/sdist and clean wheel smoke also passed.
- All data and approvals were **synthetic**; scanner decisions were CI test adapters. These tests are not evidence of productive installation, real external CRM/ERP account, legal authority or actual bank settlement.

**Portal report-download and case-status verification:** [GitHub Actions 41607305839](https://github.com/tonnestate/LowHangingFruitMe/actions/runs/41607305839) — completed/success at commit `8295b1c874709ef19459661e588c0f42a30aaf80`. Later changes to documentation have their own checks and must be verified separately.

See [synthetic manual goldstandard](docs/PILOT_GOLDSTANDARD.md) and [four-week acceptance matrix](docs/FOUR_WEEK_ACCEPTANCE.md).

## v0.13.0 – signed mapping and quality, early observed successful checks

- [GitHub Actions 41628524925](https://github.com/tonnestate/LowHangingFruitMe/actions/runs/41628524925) – completed/success on commit `84b1e15f82a94b7d606869049b90b06707dce4b0`: isolated tenant tests of signed mapping approval integration and persistence passed on both Python versions.
- [GitHub Actions 41628737637](https://github.com/tonnestate/LowHangingFruitMe/actions/runs/41628737637) – completed/success on commit `bfa3a21deb969f0614261440ab8b2b0b844f3652`: new Readiness quality indicators passed on both versions.
- [GitHub Actions 41629117022](https://github.com/tonnestate/LowHangingFruitMe/actions/runs/41629117022) – completed/success on commit `dec6ff33d59286e65d09eb9ed4902333ca47b1d5`: strict R2 kind/application tests with sourced semantic review passed on both versions.
- [GitHub Actions 41629294987](https://github.com/tonnestate/LowHangingFruitMe/actions/runs/41629294987) – completed/success on commit `3e83ef2ef17dd31166bc59983c2290ad0dc4214f`: **293 Python tests passed on both 3.11 and 3.12**, including source mapping, API, recovery, quality metrics and actual customer XLSX/JSON/PDF export. Wheel packaging and CLI smoke passed. The later R2 HTTP/portal changes require the final release CI check and are not certified by this earlier run.

All figures are synthetic. No automatic real recovery, finance invoice issuance, live ERP connector, independent contract/legal signoff or SOC-2 attestation is established.

### v0.13.0 tested complete code and report/portal path

**Observed Python Actions run:** [41630067012](https://github.com/tonnestate/LowHangingFruitMe/actions/runs/41630067012) — completed / **success**, source revision [e061d908b028610c4eed48539cfd7d13e5940993](https://github.com/tonnestate/LowHangingFruitMe/commit/e061d908b028610c4eed48539cfd7d13e5940993).

- Python 3.11: **299 tests passed** (source upload → authenticated signed-mapping/contract approval → audited calculation → recovery ledger → customer report), actual MariaDB and Frictionless; wheel/sdist build and installation smoke passed.
- Python 3.12: **299 tests passed** with the same synthetic acceptance matrix.
- Tests explicitly cover unconfirmed/mismatched R2 tier semantics, source-cited excess-only acceptance, mapping HMAC replay/tampering/revocation/cross-tenant boundaries, and data_coverage_pct, rule_clarity_pct, reconciliation_completeness_pct in customer exports. Missing controls or inconsistent totals continue to block final financial findings.
- **Observed portal Actions run:** [41629682931](https://github.com/tonnestate/LowHangingFruitMe/actions/runs/41629682931), revision c22dbfda48b008ce1e2557c5d4b9cd15f220f2f1 — completed / success. This includes the existing portal workspace's audit quality and issue display with no design replacement.
- The later AGENTS.md governance-only update and this evidence appendix each trigger their own workflow; their check outcomes are separate from the above code-commit results.

**External/commercial acceptance still OPEN:** no authorized third-party ERP production dataset, external independent controller sign-off, licensed service contract + external RDG assessment, real customer Identity Provider, live malware-scanned/encrypted VPS storage and business-continuity verification, proven bank-realized recovery, invoice approval or Lexware/Odoo/SAP connector. None is implied by 299 synthetic passing tests.


## v0.13.1 – new-case 5% proposal, historical fee preservation (03.11.2026)

**Verified source revision:** [d4747e56d91f83a470d8d9acb417fbc40ce4a450](https://github.com/tonnestate/LowHangingFruitMe/commit/d4747e56d91f83a470d8d9acb417fbc40ce4a450).

- [Python Actions 41694402146](https://github.com/tonnestate/LowHangingFruitMe/actions/runs/41694402146): **completed/success**; **302 tests** on Python 3.11 and **302 tests** on Python 3.12, including real isolated MariaDB, approved synthetic recovery events, retroactive 3%-case preservation, new 5%-rate proposal, customer report, byte-exact source and ledger authorization checks. Normal packaging/CLI checks and compilation succeeded.
- [Portal Actions 41694402050](https://github.com/tonnestate/LowHangingFruitMe/actions/runs/41694402050): **completed/success**; **10 Node unit tests**, production Next.js build and TypeScript checks, **15 browser acceptance tests** (desktop/tablet/mobile). Live website not deployed.
- The earlier intermediate commits on this workstream temporarily failed CI due to a quotation typo and outdated browser fixture, both corrected in the above verified revision. Only the final passing runs are release evidence.
- **Limitations:** SQL 007 migration was exercised against an isolated CI database, not against the operator's production environment. Historic-case preservation is regression-tested with a simulated 300-bps legacy record. This is not proof of old customer billing terms, accepted new contracts, real bank payments or real 5% fee collections. `fee_due_net` remains 0.00, and the independent RDG/success-fee, data-security and real-pilot gates remain open.

## v0.14 development – atomic signed-rule supersession (03.11.2026)

**Observed successful code/test workflow:** [GitHub Actions 41697334882](https://github.com/tonnestate/LowHangingFruitMe/actions/runs/41697334882), source commit [4800b2a5b6a8d03259d22cc3218feb4c8582d044](https://github.com/tonnestate/LowHangingFruitMe/commit/4800b2a5b6a8d03259d22cc3218feb4c8582d044).

- Python 3.11: **310 tests passed** with the actual isolated MariaDB service, Frictionless, regression tests, package build and fresh-wheel smoke checks.
- Python 3.12: **310 tests passed** with the corresponding independent workflow job.
- New tests demonstrate exactly one current reviewed contract revision per scoped supplier rule lineage; a second signed revision prevents new final audited findings from the superseded bundle, but older completed reports remain available in their original saved state.
- The rule-head row lock stops a concurrent supersession from committing during an active guarded calculation. Signed old receipt replays are not accepted as current. Provenance remains approval/document hash and source-revision bound.
- **Intermediate checks:** initial [41696678709](https://github.com/tonnestate/LowHangingFruitMe/actions/runs/41696678709) failed on an outdated negative assertion for the old error text; [41696905481](https://github.com/tonnestate/LowHangingFruitMe/actions/runs/41696905481) failed because the service correctly returned non-final `NEEDS_REVIEW` instead of HTTP 503. Both assertions were updated to the actual safe API contract and all 310 tests subsequently passed.
- **Remaining open:** This is only the current-head/supersession layer of v0.14. No full EXTRACTED/NEEDS_CONFIRMATION proposal state machine, real Docling clause review, migration against existing production DB, IdP/VPS secure runtime, independent commercial legal sign-off or verified real cash recovery. SQL 008 requires controlled manual migration, and pre-migration approvals without lineage require reviewed re-approval. Do not call the entire v0.14 release complete.


## Read-only MariaDB compatibility startup gate (04.11.2026)

**Verified source commit:** [6300564787c623e6eed3779e581de39ad70670fe](https://github.com/tonnestate/LowHangingFruitMe/commit/6300564787c623e6eed3779e581de39ad70670fe).

- [GitHub Actions 41826517951](https://github.com/tonnestate/LowHangingFruitMe/actions/runs/41826517951) — **completed/success** for both Python **3.11 and 3.12**.
- **319 tests passed per runner** including actual isolated MariaDB 11.4, missing SQL 007/008 objects, non-InnoDB schema, missing constraints, wrong historical 3%-default and a successful read-only preflight of the freshly migrated CI database.
- The installed `lhfm-schema-check` command and `create_app_from_environment` share the metadata preflight. API startup fails closed before serving endpoints against an incompatible schema. No migrations or data updates occur at HTTP startup.
- **Not proven:** real existing production schema, production migration from an older release, SQL schema version ledger/checksum runner, restored backup, real IdP, secured VPS or real customer data. SQL 008 still requires explicit operator-controlled migration and legacy approval re-review.


## v0.14 InnoDB revision-lock ordering / MariaDB migration control (04.11.2026)

**Deadlock prevention:** [commit eb6e6839aa4a5bc917e9ec964bb2d7a83694ee95](https://github.com/tonnestate/LowHangingFruitMe/commit/eb6e6839aa4a5bc917e9ec964bb2d7a83694ee95), [Actions 41827901269](https://github.com/tonnestate/LowHangingFruitMe/actions/runs/41827901269), completed/success, both Python 3.11 and 3.12. Revoke now locks revision head before approval and reviewer grant; isolated MariaDB test holds head alone to prove revoke blocks until release.

**Tracked migrations:** [commit 83d45d50a7921be9218ec8eada80ed795c683470](https://github.com/tonnestate/LowHangingFruitMe/commit/83d45d50a7921be9218ec8eada80ed795c683470), [Actions 41828849927](https://github.com/tonnestate/LowHangingFruitMe/actions/runs/41828849927), completed/success: **330 Python tests passed on 3.11 and 330 on 3.12**. CI initialized a real MariaDB 11.4 test schema through `lhfm-migrate`'s underlying controlled runner; passed no-op plan, missing/in-progress/modified-checksum negative cases and startup schema validation. `lhfm-migrate --apply` requires deliberate operator environment flag and backup confirmation outside CI, and cannot silently adopt untracked preexisting LHFM tables.

**Not tested or claimed:** migration of a customer/legacy VPS database, actual disaster recovery from a partial DDL, a working live ClamAV/IdP, completed proposal-state lifecycle, real ERP audit, legal contract acceptance or fee collection. A successful isolated CI job does not authorize production deployment.


## Operational readiness vs liveness (04.11.2026)

[Code commit 493c77ef8277ed84e9425f84352573cbf33a7772](https://github.com/tonnestate/LowHangingFruitMe/commit/493c77ef8277ed84e9425f84352573cbf33a7772); [Python Actions 41829742266](https://github.com/tonnestate/LowHangingFruitMe/actions/runs/41829742266): completed/success under **Python 3.11 and Python 3.12**, **336 tests passed per runner**. The new `GET /readyz` rejects absent upload/promotion/recovery services, untrusted synthetic scanner doubles, missing migration/schema state and absent/bad local clamd protocol responses. `ClamAVScanner.ping()` requires a bounded UNIX-socket zPING/PONG response. The existing `/healthz` remains liveness-only. Synthetic socket tests exercise both positive and negative paths but do **not** demonstrate a real installed daemon, updated malware signatures, production storage or customer security approval.


## Trusted JWKS file hot rotation and concurrency fix (04.11.2026)

[Initial implementation d9a1092be9cabfb8ad5ca3f85369fe96c51e3ba0](https://github.com/tonnestate/LowHangingFruitMe/commit/d9a1092be9cabfb8ad5ca3f85369fe96c51e3ba0); [race-hardening fix 0aa7c0c5c8d2d163359538bc5644fce4013d1492](https://github.com/tonnestate/LowHangingFruitMe/commit/0aa7c0c5c8d2d163359538bc5644fce4013d1492). **Verified:** [GitHub Actions 41830627024](https://github.com/tonnestate/LowHangingFruitMe/actions/runs/41830627024), **completed/success**, **338 Python tests passed on 3.11 and 338 on 3.12** (actual isolated MariaDB). Trusted locally provisioned JWKS are read before verification with no-follow and size checks, hash compared and atomically validated/swapped under the same lock. Tests reject retired signing kids and invalid replacement files and verify recovery after valid publication.

**Boundary:** The test uses synthetic local RSA keys, not a live issuer. This does not supply OIDC onboarding, access-token refresh, refresh token rotation, real user deprovisioning or external revocation. A local public key file update still requires trusted operator publication, host runtime verification and authorized IdP integration.


## Reviewed SQL release checksum pins (04.11.2026)

- [Main commit 63d3bc24a302c472aa32f57667af5cbb6ddad592](https://github.com/tonnestate/LowHangingFruitMe/commit/63d3bc24a302c472aa32f57667af5cbb6ddad592).
- [Actions 41832270878](https://github.com/tonnestate/LowHangingFruitMe/actions/runs/41832270878): **completed/success**, **339 Python tests passed under 3.11 AND 339 under 3.12**. Both the runtime read-only schema gate and controlled installer compare the MariaDB migration ledger / local SQL contents against immutable reviewed SHA-256 pins, not just valid hexadecimal formatting. No customer database or production backup has been used or migrated.

## Document-backed human contract candidate v0.14 (04.11.2026)

- Feature branch `feat/contract-review-gate`; SQL `009_contract_candidates.sql` (pinned SHA-256) and MariaDB reviewer-scoped append-only event ledger. CLEAN source PDF verified by digest, bounded Docling subprocess interface (not an OS/network sandbox), extracted citations, explicit human review with exact rule hash, HMAC approval under row locks, supersession and revocation reflected in the candidate record.
- [Python Actions 41835718850](https://github.com/tonnestate/LowHangingFruitMe/actions/runs/41835718850): **completed/success**, **351 Python tests passed with Python 3.11 and 351 with Python 3.12** on isolated actual MariaDB 11.4 with synthetic PDFs, a fake extractor, synthetic reviewers and cryptographic keys. End-to-end test covers scanned file intake, candidate extraction, wrong SHA-256, a citation absent from original segments, unauthorized subject, duplicate candidate, repeat approval review, signed audit, replay refusal and revocation. A short-lived red CI ([41835206794](https://github.com/tonnestate/LowHangingFruitMe/actions/runs/41835206794)) identified a 409/422 misclassification; fixed in [2afd93f2](https://github.com/tonnestate/LowHangingFruitMe/commit/2afd93f2e829ff59a22036081f883ab1235f3f14), retested green above.
- [Portal Actions 41834409466](https://github.com/tonnestate/LowHangingFruitMe/actions/runs/41834409466): **completed/success**, npm tests, Next.js build, TypeScript check, standalone packaging and 1440/768/390 Playwright acceptance for protected staging; no production OIDC login.
- **Unproven:** actual Docling model installation, real contracts or scanned PDFs, denied parser network egress, paid customer, production ClamAV/IdP/ERP, independent accuracy benchmark, recovery cash realization, legal fee allocation, VPS backup restore or RDG review. Public commercial launch remains blocked by G0-G5 in `docs/GO_LIVE_GATE.md`.


## Fail-closed Docling subprocess sandbox hardening (04.11.2026)

Feature workstream `feat/prod-docling-sandbox`, [GitHub Actions 41841304792](https://github.com/tonnestate/LowHangingFruitMe/actions/runs/41841304792) **completed/success** with **360 Python tests on 3.11 AND 360 on 3.12** (real CI MariaDB 11.4). Technical changes include mandatory root-controlled launcher path, actual Linux worker namespace/loopback-only network check, `/readyz` subprocess preflight, 1-MiB stdout cap (incremental select/read), 120-second max duration, process-group termination for stuck parsers, worker-owned CPU/memory/file descriptor limits, and a private operator example for Bubblewrap. Negative tests cover missing/untrusted launcher, same-network namespace, visible non-loopback interface, output overflow, timeout, invalid worker JSON and spoofed sandbox success. An initial synthetic test suite had CI-runner path ownership assumptions and failed; the tests were decoupled from runner ownership while retaining production root checks. [Run 41841304792](https://github.com/tonnestate/LowHangingFruitMe/actions/runs/41841304792) is the final successful validation.

**Proof limits:** This CI does NOT run Docling with real PDFs or OCR, DOES NOT launch Bubblewrap on the customer's VPS, DOES NOT establish complete process filesystem isolation, nor validate a real ClamAV daemon or live IdP. Real operator sandbox and actual document QA remain G1/G2 **OPEN**. The system refuses document extraction without the configured trusted launcher.

## Server-side confidential OIDC refresh and encrypted session rotation (04.11.2026)

- Feature branch `feat/oidc-token-renewal`: [Portal Actions 41843380537](https://github.com/tonnestate/LowHangingFruitMe/actions/runs/41843380537) **completed/success** (npm unit tests, Next.js build, typecheck, standalone packaging and Playwright browser tests at 1440/768/390), with [earlier detailed unit run 41842914601](https://github.com/tonnestate/LowHangingFruitMe/actions/runs/41842914601): **16 of 16 Node unit tests passed** including actual Auth.js encrypted JWT encode/decode, issuer-pinned HTTPS endpoint, rejected malformed/oversized refresh, proccess-local singleflight, stale cookie fragments. [Python Actions 41843380269](https://github.com/tonnestate/LowHangingFruitMe/actions/runs/41843380269) **completed/success**, **360 unittest cases each** in Python 3.11 and Python 3.12 on actual isolated MariaDB 11.4.
- The trusted Next.js BFF retains API access and refresh credentials exclusively inside the encrypted Auth.js HttpOnly/Secure/SameSite=Lax JWT cookie, calls a configured HTTPS issuer-origin token endpoint for renewal, and re-encrypts the session using the original Auth.js cookie-name salt; failures clear the session. Tokens are not returned to browser JavaScript, and the Python resource server still checks issuer/audience/client, signature, scopes and active database grants.
- **Not proven:** a real identity provider/client registration, actual token issuance or refresh, MFA, token revocation or deprovisioning, redis/multi-process distributed rotation, Apache/TLS and user onboarding. The 15-second refresh reuse cache is confined to a single Node runtime. The actual customer's IdP configuration must be verified externally; G0 remains OPEN.


## v0.15 – Commercial fee handoff (04.11.2026)

- Branch `feat/billing-handoff`, reviewed SQL migration `010_billing_handoff.sql` (SHA256 `03fdff7973d04ab4bf005353edff9f3d1703ee05cdcb7e1545608a3664464c92`), prepared and released billing packets, DB-bound operator-provisioned customer/legal terms, dual-person scoped billing grants, historic 300-bps and new 500-bps rate stability, source-event digest and terms/legal revision fingerprints, stale detection, void with required external correction reference, explicit `invoice_created=false` and `fee_due_net=0.00`.
- [Python Actions 41850007747](https://github.com/tonnestate/LowHangingFruitMe/actions/runs/41850007747): **completed/success**, **424 Python tests passed each** under Python 3.11 and Python 3.12 using real isolated MariaDB 11.4 and synthetic contract/customer/finance operators. Includes E2E source upload → signed financial audit → independently confirmed recovery → commercial terms → dual-role billing packet → stale reversal/terms revision → release/void, wrong actor/tenant and rate-mismatch negative tests.
- [Portal Actions 41848399198](https://github.com/tonnestate/LowHangingFruitMe/actions/runs/41848399198): **completed/success**, BFF allowlist, production build, TypeScript and responsive Playwright checks.
- **Not tested in real operation:** actual B2B signed engagement, legal clearance or tax/invoice authorization, a real bank booking, external invoice number/creation, a customer-/supplier-validated source export, production database upgrade/rollback or actual paid invoice. G4 and public paid launch remain **OPEN**.

Additional contract-rate regression: [Actions 41850007747](https://github.com/tonnestate/LowHangingFruitMe/actions/runs/41850007747) **completed/success**, **424 tests each under Python 3.11 and 3.12** on real isolated MariaDB 11.4. The additional direct legacy-case test verifies a historical 300-bps case creates a 3% handoff (€30 on €1,000) while newly opened cases retain 500 bps. No commercial invoice was actually issued.


## v0.16 – age-encrypted, Ed25519-signed MariaDB + private-file disaster recovery (04.11.2026)

- [GitHub Actions 41855424879](https://github.com/tonnestate/LowHangingFruitMe/actions/runs/41855424879): **completed/success**, actual MariaDB 11.4 service, age-keygen ephemeral identity and ephemeral Ed25519 private/public key. A real `mariadb-dump --single-transaction` of schema/migrations 001–010 and both synthetic private file roots is piped directly into separately authenticated age encrypted ciphertexts. An encrypted manifest hashes each component and is additionally signed using Ed25519. The sandbox command recovers SQL into an empty, separately created `lhfm_restore_ci` database and materializes files in isolated empty private directories; restored file bytes are checked against synthetic originals. Re-restore, forged signature and a modified encrypted archive fail closed. No plaintext archive file is written to the backup directory.
- [Python Actions 41855296597](https://github.com/tonnestate/LowHangingFruitMe/actions/runs/41855296597): **completed/success**, 430 Python unit/integration tests under Python 3.11 AND 430 under Python 3.12. Added DR negative tests for symlink/hardlink, group/world file permissions, source/restore name safety, improper operator authorization, unsafe tar path, and untrusted MariaDB client configuration.
- **Not proven:** actual customer-VPS backup/restore, application-level consistent write freeze, genuine production files, offline key custody and signing authority, offsite encrypted transfer, retention/deletion, complete Apache/IdP/ClamAV/Docling restoration, measured RPO/RTO or legal/financial signoff. This is a synthetic operational integration test only, not a production recovery certificate. See `docs/DISASTER_RECOVERY.md` and G5 in `docs/GO_LIVE_GATE.md`.


**Final hardened DR boundary (04.11.2026):** [Actions 41856986225](https://github.com/tonnestate/LowHangingFruitMe/actions/runs/41856986225) **completed/success** verifies the new source-root/key-location gate does not break the MariaDB 11.4 and signed age file recovery. [Python Actions 41857045105](https://github.com/tonnestate/LowHangingFruitMe/actions/runs/41857045105) **completed/success**, **431 unittest cases on Python 3.11 and 431 on Python 3.12**, including an additional adversarial test that a signing or verification trust key inside the backed-up file tree is rejected. Both encrypted private trees must be physically disjoint. The production VPS and actual backup credential custody have not been exercised.


## v0.17 – fail-closed private API runtime and account-separated systemd service (04.11.2026)

- [Python GitHub Actions 41866179166](https://github.com/tonnestate/LowHangingFruitMe/actions/runs/41866179166): **completed/success** with **443 tests on Python 3.11 and 443 tests on Python 3.12**, plus packaging and wheel-install smoke. Newly installed `lhfm-runtime-check` intentionally returned **exit 2** under synthetic CI defaults, proving that absent real private deployment configuration does not accidentally authorize production boot. Tests cover separate API UID, reject root worker and privileged DB credentials, private 0700 source/upload roots and disjointness, loopback MariaDB, missing runtime services, real FastAPI factory rejecting a preflight failure, and the correct uvicorn loopback-only/proxy-header switches.
- [Encrypted DR Actions 41864436497](https://github.com/tonnestate/LowHangingFruitMe/actions/runs/41864436497): **completed/success** for the earlier Python packaging/runtime step against synthetic MariaDB 11.4, not a live VPS restore.
- API application factory `create_app_from_environment` now calls the mandatory read-only runtime gate **before app construction**. The operator `lhfm-runtime-check` is the same gate when invoked in `ExecStartPre`. Systemd templates separate private `lhfm-api` from Apache/Next.js UID and use root-owned 0600 environment files. Source snapshots remain writable only to the dedicated private API UID because reviewed bundle promotion writes them; neither API nor portal binds a public HTTP listener. New operator runbook: `docs/RUNTIME_DEPLOYMENT.md`.
- **Not proven:** any actual systemd unit installation, public TLS/Apache vhost or firewall, secure credential provisioning on a real host, real OIDC issuer and refresh, ClamAV daemon with live updated signatures, actual Docling offline models and network-isolated parser, signed B2B terms, real ERP independently controlled source data, paid invoice or full application restart. Synthetic unit tests and configuration templates **do not establish production readiness or G0–G5 signoff**.


## v0.18 – operator-only abandoned upload housekeeping (04.11.2026)

- [Python Actions 41892137248](https://github.com/tonnestate/LowHangingFruitMe/actions/runs/41892137248): **completed/success**, 452/452 unittest cases on Python 3.11 and 452/452 on Python 3.12, plus wheel build/fresh-install smoke. The installed `lhfm-upload-housekeeping --apply --limit 100` command **returned 2** in the unapproved CI environment as explicitly required. The nine synthetic MariaDB integration cases cover dry-run without changes, mandatory dual operator approval, time-limited stale PENDING/RECEIVING transition to REJECTED with durable per-upload SQL-011 events, `.part` and `.inspect` hardlink handling, no deletion of CLEAN or already REJECTED customer files, age/mtime defense, malicious symlink/unaccounted hardlink rejection, ambiguous final file hard stop, and bounded/idempotent batching.
- [Encrypted DR Actions 41892137388](https://github.com/tonnestate/LowHangingFruitMe/actions/runs/41892137388): **completed/success**, actual synthetic MariaDB 11.4 migrations 001–011, age-encrypted backup, Ed25519-signed manifest, isolated SQL plus private-files restore, replay/tamper refusal.
- Operator procedure is `docs/UPLOAD_HOUSEKEEPING.md`. All writes require both `LHFM_UPLOAD_HOUSEKEEPING_APPROVED=YES` and `LHFM_UPLOAD_WRITES_STOPPED=YES`, with the upload writers **actually stopped independently**. Nothing schedules or exposes this command publicly. Only old uncompleted staging paths and DB states are in scope; final files, contract evidence, recovered amounts, billing packets and successful CLEAN uploads are never removed by this operator.
- **Not proven:** customer-host operational maintenance, an independent scheduler/shutdown attestation, complete GDPR erasure or legal holds, live ClamAV/Docling/IdP, a real ERP golden dataset, commercial billing/independent legal signoff or end-to-end application restart. Synthetic CI success is not production release approval.
