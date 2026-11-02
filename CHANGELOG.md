# Changelog

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
