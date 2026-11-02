# MariaDB approval registry v0.5.0 – persistence, revoke and dispatch

**Status:** implemented in source. Product is still pre-production; no authenticated user-service, real contract accounts or public customer API exist. Read [EVIDENCE.md](../EVIDENCE.md) for actual test run IDs.

## Purpose

The receipt HMAC of v0.4 proves integrity but not continuing authorization. In v0.5, completed CSV audits also require a persistent **ACTIVE** approval in the dedicated MariaDB tables, tied to tenant, legal entity, rule and exact reviewed document. A revoked or unknown approval cannot authorize a calculation, even when the signature is intact.

Database migration: [sql/001_approval_registry.sql](../sql/001_approval_registry.sql), using InnoDB and foreign keys. Tables: scoped reviewer grants; approval records with ACTIVE/REVOKED state; append-only ISSUED/REVOKED events. No TonnEstate schemas or infrastructure are changed.

## Call flow and atomicity

1. An **already authenticated** reviewer with the `contract_reviewer` role is associated with a tenant and legal entity. The grant must be provisioned by a trusted administrative process; this project currently has **no real login or administrative provisioning flow**.
2. Trusted backend signs the exact rule revision and contract hash using a protected HMAC key. The low-level signer does not authenticate the listed reviewer: never call it from an uncontrolled user endpoint.
3. `ApprovalRegistry.register()` validates HMAC, exact tenant and entity, binds actor to reviewer and checks the active grant before writing the record and event in one transaction.
4. At calculation dispatch, `ApprovalRegistry.guard()` revalidates HMAC and obtains MariaDB `SELECT ... FOR UPDATE` locks on the approval and grant rows. The calculation runs **inside the transaction**. Concurrent revocation cannot commit until that calculation exits its guarded interval.
5. `ApprovalRegistry.revoke()` validates an active scoped role grant, locks the same approval row in the **same lock order** as the guard, changes state atomically and records an event. A repeat revoke returns false and adds no duplicate revoke event.
6. If the registry is missing, unavailable, revoked, unregistered or inconsistent, the audit fails closed with no calculated `difference_net`. Data-readiness-only diagnostics remain possible.

This guards the calculation start/interleaving boundary; it does not make file import/contract authenticity atomic, and it does not prevent already distributed historical reports being read. Such reports must later have explicit supersession/revocation semantics. The registry does not sign an audit result or establish a legally collectible claim.

## Real CI test integration

Run GitHub Actions with a dedicated MariaDB 11.4 service for each Python version, install `.[import,registry]`, migrate isolated DB `lhfm_test`, seed one **fictional** scoped reviewer using `tests/scripts/setup_approval_registry.py`. Do not run the test-only provisioner against production; it refuses any database whose name is not exactly `lhfm_test`.

The synthetic approval generator now registers the receipt in MariaDB before the CLI audit. Regression tests exercise wrong tenant, duplicate approval ID, revoke idempotence, revoked dispatch and the real concurrent locking boundary. Production release requires actual authenticated identity/tenant context and credential segregation.

## Secret/operational requirements

- Database credentials live only in trusted runtime secret storage, never end-user forms, GitHub source or model prompts. Runtime variables: `LHFM_DB_HOST, LHFM_DB_PORT, LHFM_DB_USER, LHFM_DB_PASSWORD, LHFM_DB_NAME`.
- HMAC key is `LHFM_APPROVAL_KEY_HEX` and must be bound to the trusted signer. The DB-only scoped reviewer grant does **not** establish actual authenticated identity.
- Dedicated MariaDB schema/database and a least-privilege application role; migration rights separate from application access, encrypted connections/transport and secret rotation required in production.
- Do not expose the local CLI as a web service. Its `--tenant-id` is caller-supplied and is **not** authentication. The future HTTP service must derive tenant and actor from server-verified sessions/credentials.
- Later: business-backed approval revocation/supersession policy, authenticated admin and reviewer identity, immutable source registry, audit events/retention, key IDs/rotation, per-tenant encryption and operational backups.

## Unresolved tests and limitations

CI only tests synthetic records and DB row locking. Business authorization and actual credential assurance are **not** tested until a real identity provider is integrated. A compromised signing key or a trusted caller passing a false identity defeats these administrative checks. Database owner/superuser also has the technical capability to rewrite records; database audit/access controls are a separate security requirement.

Future API/portal cannot be called production-safe until these integration gaps close.

## v0.6.0 authenticated calling boundary

`AuthenticatedApprovalService` uses an RFC 9068 JWT access verifier to derive stable user identity before calling the existing registry. The original low-level registry API still accepts a trusted actor string **for local tools and tests**; it must not be exposed directly through HTTP. The service uses a verified JWT scope plus active scoped MariaDB grant to authorize approve/revoke, and executes an authenticated audit with token/DB rechecks during dispatch. See [AUTHENTICATION.md](AUTHENTICATION.md). There is no production IdP connected or admin grant-provisioning UI.
