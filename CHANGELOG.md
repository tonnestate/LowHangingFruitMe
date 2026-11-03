# Changelog

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
