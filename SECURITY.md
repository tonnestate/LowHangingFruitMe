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
