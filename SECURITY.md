# Security policy

LowHangingFruitMe is **pre-production** financial-data analysis software. Do not upload customer contracts, live invoices, API credentials or customer financial statements to this public repository.

## Boundaries

- Existing intake commands accept local files only. They are **not** a secure multi-tenant upload service.
- PDF processing requires isolated worker processes, malware scanning, egress restrictions, timeout and memory limits before receiving actual customer data. The current Docling adapter does **not** provide OS process isolation.
- Frictionless validates structural CSV input; it cannot prove the commercial completeness of submitted data.
- No raw customer data may be transmitted to third-party AI services without contractual, security and customer authorization.
- No automatic legal-claim determination, supplier communication, recovery action or invoicing exists.

## Vulnerability disclosure

Report vulnerabilities privately via GitHub private vulnerability reporting when available, or request a secure contact from the repository owner. Never post exploit instructions with secrets or customer records as a public issue.

## Production release requirements

Tenant and role isolation, secure upload pipeline, independent completeness controls, at-rest encryption, retention and deletion, dependency/SBOM review, execution sandbox, end-to-end and security testing, backup/restore proof, and contractual/legal approval.

## Approval integrity (v0.4.0)

`LHFM_APPROVAL_KEY_HEX` must only be injected from a protected backend secret store, never be accepted as an end-user field or committed to source. Treat the key as a tenant/organization-authority credential: restrict signer usage to authenticated, authorized contract reviewers, log issuance, use stable unique approval IDs and maintain a revocation/supersession database before real customer operation. HMAC is **not** a qualified electronic signature, independent identity proof or cryptographic validation of the contract's business meaning. The test factory in `tests/scripts/` MUST NOT be deployed or exposed.

The existing CLI is a local development tool. Its `--tenant-id` argument is not trustworthy authorization; no externally accessible API may accept arbitrary tenant claims as access control. All role and scope checks must be imposed by the future authenticated service.

## Token verification and reviewer authority (v0.6.0)

Use dedicated JWT **access** tokens, not OIDC ID tokens or bearer JWTs with generic `typ`; require `at+jwt` and fixed RS256, trusted HTTPS issuer, unique API audience, approved client ID, time-limited validity and server-provisioned public JWKS. Never honor token-provided JWKS URLs. The bearer-token verifier is a library, not login/session management. All HTTP adapters must derive actors from verified access tokens; do not forward untrusted reviewer IDs to lower-level registry methods.

Static public JWKS must be rotated through a trusted deployment mechanism. Protect the HMAC approval signing key separately from the JWT public verification keys. Do not provision active reviewer grants based solely on token claims. The signing authority for JWTs belongs to a selected external IdP, not this repository. Before production, verify IdP configuration, key rotation, user offboarding, administrative grants, tenant isolation and token revocation behavior.

## Universal source import (v0.7.0)

CSV/XLSX and office files are untrusted data. The local helper limits file size, ZIP expansion and row/cell counts, and refuses Excel formulas as trusted financial amounts; it is **not** a hardened malware-scanning or OS-isolated upload service. The XML document classifier uses defusedxml to block entity expansion/XXE. All mapping suggestions are untrusted until manually reviewed, and the reviewed plan is bound to exact source bytes. Do not upload customer financial documents via public CI or send them to outside model services. Source ERP connectors, if implemented, should be read-only with restricted field/tenant/period permissions; no write-back to journals or credits.

We do not have a SOC 2 Type II report. Do not advertise SOC 2, ISO certifications or third-party auditor endorsement unless a corresponding actual, scoped and current independent report exists.

## v0.8 server-provisioned HTTP Audit API

FastAPI accepts only Bearer access JWT, opaque bundle UUID, tenant/legal entity labels and canonical UUID Idempotency-Key. It does not receive filesystem paths, source files, rule overrides or signing secrets over HTTP. The service maps token subject/scope to exact scoped database reviewer grants and revalidates signed approval under InnoDB row lock. Bundle sources are checked within a trusted root and copied to bounded ephemeral snapshots with SHA256 verification, but the source store itself is **not** a hardened public upload service. A missing control report or revoked approval cannot produce a final money finding. Reports are accessible only to their original reviewer with a currently active grant and returned with `Cache-Control: no-store`. No real network-facing access, load limits, WAF, MFA, token revocation, file scanning, secure object store, backup/restore or incident response are implemented. Keep this API local/internal until these controls are independently verified.

## v0.9 – private staging uploads, not public customer intake

Upload API validates signed JWT and database grant, accepts only a server-assigned UUID / exact size + SHA256 / fixed format kind, enforces single-writer SQL state and at most 16MiB raw streamed content. The OS staging area requires mode 0700, exclusive 0600 file creation, post-scan type checks and non-overwriting promotion by hardlink. A real clamd daemon must explicitly report `stream: OK` via trusted local UNIX socket; infection or ambiguous/unavailable result fails closed, with bytes deleted. Exposed GET returns metadata only. **The CI scanner is a test double, not evidence of actual malware protection.** CLEAN uploads do not enter audit calculations and must be independently authorized, normalized and provenance-bound. Before any public launch add quota/rate limiting, genuine identity lifecycle and offboarding, encrypted per-tenant storage, scanning operations/signature update, retention/erasure, revalidation, backup, secure reverse proxy and actual DPA/legal/security approvals.
