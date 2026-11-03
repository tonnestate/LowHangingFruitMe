# Changelog

## Unreleased – v0.14 rule-head supersession workstream

- Added migration 008, a tenant/entity/agreement/rule-scoped authoritative current approval, persistent revision/event lineage and signed source-revision data on each new approval.
- Approval registration atomically replaces the previous current approval (REVOKED with SUPERSEDED event) and blocks all new audits using the old receipt; a running audit holds the head lock until computation finishes.
- Historical audit snapshots remain retrievable. Legacy records lacking lineage cannot pass the new guard without renewed authenticated approval. Ingested extracted rule proposals and full human-review state machine are **still open**; no general-availability or production claim until passing isolated MariaDB CI and real deployment review.


## 0.13.1 – prospective 5% fee proposal with persistent legacy case rate (2026-11-03)

- New Recovery Cases persist 500 basis points (5%) while SQL 007 sets 300 bps (3%) for existing cases. Event replays never overwrite the original case rate.
- API ledger, authorized customer PDF/XLSX/JSON exports and public illustration display the applicable fee proposal; synthetic tests cover cents, reversals and historical rate retention.
- Unchanged: no signed customer fee agreement, independent bank settlement verification, invoice approval or legally billable amount; `fee_due_net=0`. Actual CI results must be recorded in EVIDENCE.md.


## 0.13.0 – signed mapping, strict tier semantics and visible quality (2026-11-03)

- Added separately HMAC-signed and MariaDB-registered transaction/settlement mapping receipts, with precise tenant/legal-entity/actor/source/plan/contract-approval binding and explicit revocation events.
- Protected the existing HTTP audit with both mapping approval row locks while retaining the original HMAC contractual rule and Frictionless/readiness dispatch; unverified uploaded plans cannot silently become billable findings.
- Required exact human-reviewed R2 tier application (FULL_BASE, EXCESS_ONLY, BANDS, FIXED_REWARD), backed by an approved clause reference; R2 semantics now enter the rule's signed digest. Early HTTP rejection `RULE_SEMANTICS_NEEDS_REVIEW` instead of an invented calculation.
- Added audit-level quality metrics with precise source-count denominator, signed technical rule clarity and matched-control percentage; customer-facing PDF/XLSX/JSON reports and the existing Next.js workspace show these indicators and concrete data issues.
- Consolidated `CONCEPT.md`, pilot admission thresholds, narrow Lexware read-only scope and explicit external RDG/3%-success-fee review requirements.
- The measured percentages do not prove source-ERP completeness or independently validate commercial claims. Source-value-weighted coverage, real ERP account, real pilot, independent legal opinion and VPS/IdP deployment are still absent.


## 0.12.0 – closed synthetic pilot path, report downloads and status tracking (2026-11-03)

- Added `lhfm audit-sources`: a single local command consuming separately signed contract receipts, source-hash-bound ERP CSV/XLSX mappings and independent control totals through the existing guarded calculation.
- Added PDF/XLSX/JSON report renderers, same-tenant authenticated FastAPI downloads and Next.js BFF download routes; full detail references remain in the private hash-bound lineage snapshot.
- Added explicit `calculated_variance_net` in engine/Readiness reporting, distinct from realized and billable sums.
- Added persistent finance-authorized case-state annotations for DISPUTED/CLOSED/OPEN, derived NONE/CLAIMED/REALIZED_PARTIAL/REALIZED_FULL, with closure preventing new recovery events.
- Added acceptance tests and documented synthetic manual goldstandard. No real ERP customer data, external banking evidence, independent security examination, production deployment or billing authorization.
- **3 %** remains a manually attestable **fee proposal** based on confirmed realized amount, not an automatic invoice.
- Continued explicitly: original neon banner from `docs/Neon-Low-Hanging-FruitMe-Banner.png` is the sole visual brand reference for the portal.


## 0.9.0 – scoped private staged upload intake (development; 2026-11-03)

- Added `POST /v1/uploads`, `PUT /v1/uploads/{id}/content` and `GET /v1/uploads/{id}`, accepting only JWT-authorized reviewers of the matching tenant/legal entity.
- Added single-use MariaDB upload intent (15 minute TTL) with exact size/SHA256, atomic claim, 16 MiB bounded raw streaming, owner-only private blob staging and strict no-overwrite promotion.
- Added ClamAV clamd UNIX-socket INSTREAM client; an explicit scanner CLEAN verdict is mandatory and unavailability/infection blocks promotion. After scan, basic document/CSV/ZIP/XML type safety checks are applied.
- Each successful staged file remains `usable_for_audit=false`; no automatic financial acceptance, bundle creation or calculation from a raw upload.
- Added real MariaDB synthetic-JWT HTTP tests for tenant separation, hash/size tampering, concurrent reservation, expiry, simulated malware/scan failure, XML entity blocking and protocol framing.
- Still **no live ClamAV daemon, browser login, public upload deployment, end-to-end customer data workflow, ERP connector, recovery ledger or 3%-fee billing**.

## 0.8.0 – authenticated audit API vertical slice (development; 2026-11-03)

- Added FastAPI app with `POST /v1/audits`, `GET /v1/audits/{id}` and liveness, using existing RSA JWT access-token verifier and active scoped MariaDB reviewer authorization.
- Added operator-only private source bundle manifest with exact SHA-256 rule, transaction, settlement and contract-source hashes; rejects file path traversal, symlinks and mismatched signed rule/document digests.
- Added private copied snapshots before the unchanged canonical CSV financial audit. Report remains non-billable until verified economic recovery is recorded separately.
- Added MariaDB audit job ledger and cross-thread atomic idempotency reservation (one execution per scoped request), with statuses PROCESSING, COMPLETED, NEEDS_REVIEW and FAILED.
- Added real MariaDB integration tests using memory-generated RSA access tokens, HTTP TestClient and synthetic source files.
- **No live IdP, customer upload endpoint, production VPS installation, worker queue, legal contract acceptance, Recovery Ledger, billing, ERP connection or third-party certification.**

## Portal 0.1.0 – standalone German marketing site (2026-11-03)

- Introduced a Next.js 16 / React 19 marketing website under `portal/`, separate from the existing Python financial engine (which remains v0.7.0).
- Added original German product pages, five editorial articles, SEO metadata, navigable sections, keyboard-accessible FAQs and responsive desktop/tablet/mobile navigation.
- Added browser-only 3% fee **illustration** using exact integer cents; neither recovery calculation nor billable fee is performed by the browser.
- Reused existing `docs/Neon-Low-Hanging-FruitMe-Banner.png`; automatically extracted audited color tokens and pixel coordinates from that PNG during builds.
- Added noindex/robots staging defaults, enforced operator-provided legal text before public-build opt-in, and transparent pilot-contact gating.
- Added self-hosted Next standalone artifact, separate Apache and systemd templates that preserve existing WordPress services.
- Successful GitHub Actions frontend CI: unit, TypeScript/build, and 3-viewport Playwright interaction checks.
- Still no VPS deployment, production legal approval, protected customer portal, FastAPI upload, invoice parsing or recovery ledger.

## 0.7.0 – ERP-neutral local intake (development; 2026-11-02)

- Accepts noncanonical UTF-8 CSV and selected worksheets of XLSX for inspection; suggests DE/EN columns without approving them.
- Requires exact SHA-256-bound source mapping plan and explicit reviewer confirmation before generating canonical purchases/settlements. Rejects duplicate source IDs, missing posting status, guessed settlement periods and incompatible decimal/date formats.
- Recognizes XML invoice (UBL Invoice/CreditNote and CII), PDF and DOCX as separate document routes; does not yet extract complete invoices or supplier contract rules.
- Preserves original source row/file lineage in audit reports; normalized data pass through the existing Frictionless, Data Readiness and MariaDB/HMAC-gated calculation.
- Adds an interactive-CLI-equivalent inspection command and an explicit non-overwriting normalize command, with synthetic integration/negative tests.
- No vendor ERP-native integration, no public upload, no SOC 2 Type II report, no live customer data, no automatic approval, no 3% fee ledger.

## 0.6.0 – signed access token and scoped approval service (development; 2026-11-02)

- Added PyJWT[crypto] RSA/RS256 JWT access-token verification following the RFC 9068 at+jwt token profile, with configured issuer, audience, trusted public JWKS, client allowlist and expiry checks.
- Rejected token-directed key URLs, untrusted key IDs, untyped/ID JWTs, expired and overlong credentials, missing claims and forged payloads.
- Added authenticated approval service methods to issue/register/revoke a contract approval and execute canonical CSV audits under active MariaDB reviewer grants.
- Restricted authenticated auditing to the original contract reviewer and reverified the access token inside the existing row-locked calculation dispatch.
- Added generated-in-memory RSA cryptographic tests and real MariaDB-backed service integration tests.
- Still **no deployed IdP, HTTP API, browser login, enterprise user lifecycle, live provider test, secured uploads, external ERP or billing**.

## 0.5.0 – persistent approval registry and dispatch lock (development; 2026-11-02)

- Added MariaDB/InnoDB tables for scoped reviewer grants, unique approval IDs, immutable approval digests, ACTIVE/REVOKED status and append-only ISSUE/REVOKE events.
- Added atomic registration and idempotent revocation, with real role-grant lookup.
- Reverified HMAC, tenant, contract source and registered approval at calculation dispatch; locked row until computation finishes, preventing revocation from committing between check and computation.
- Removed ability to promote a signed receipt to final CSV audit without a persistent registry.
- Added MariaDB integration tests and CI service for Python 3.11/3.12.
- No real authentication/IdP, live user management, key rotation, distributed job queue or production deployment. Caller-supplied actor identity is **not independently authenticated** by the library.

## 0.4.0 – contract rule approval integrity (development; 2026-11-02)

- HMAC-SHA256 signed receipts bind a canonical rule revision to a specific contract file's SHA256, a tenant/legal entity, reviewer claim, role, source revision and approval timestamp.
- The canonical CSV audit is fail-closed: unsigned, altered, wrong-tenant, wrong-document or invalid approval does not produce a final monetary finding.
- The standalone numerical calculator now reports REVIEW_REQUIRED and UNVERIFIED_APPROVAL_CONTEXT without an authorized approval intake.
- Synthetic CI approval factory, fresh ephemeral CI keys, tampering/scope tests and full CLI smoke.
- Deliberate limitations: no production IAM, no revocation/persistence of receipt IDs, no genuine legal signature, no validated human identity; HMAC source integrity is not a production authorization system.

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
