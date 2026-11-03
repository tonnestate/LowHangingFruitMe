# LowHangingFruitMe authenticated Audit API – v0.8.0 (historical baseline)

**This document records the original v0.8 subset.** For current v0.12 authenticated upload, mapping, ledger and PDF/XLSX/JSON report APIs, see [API_AND_DATA.md](API_AND_DATA.md) and [FOUR_WEEK_ACCEPTANCE.md](FOUR_WEEK_ACCEPTANCE.md). The original v0.8 contract below is retained for traceability.

**Actual implemented boundary:** `src/lowhangingfruitme/api/http.py`, `src/lowhangingfruitme/api/store.py`, `sql/002_audit_api.sql`.  
**Status:** tested **operator-provisioned bundle → JWT-authorized HTTP audit → MariaDB report**. Not deployed; not production ready; no customer uploads.

## Implemented endpoints

| HTTP | Path | Scope | Effect |
|---|---|---|---|
| GET | `/healthz` | none | Minimal liveness response; does not prove DB readiness |
| POST | `/v1/audits` | `lhfm:audit:execute` + active DB reviewer grant | Run an existing registered private bundle through the canonical calculation once |
| GET | `/v1/audits/{audit_id}` | Same JWT/DB grant AND original reviewer ID | Read stored report only in its authorized tenant and legal entity |

### Example POST

The request contains **references only**, never file paths, approval secrets, bank data or source content.

~~~http
POST /v1/audits HTTP/1.1
Authorization: Bearer <valid-RS256-at+jwt-access-token>
Idempotency-Key: 1e7e81a4-6d2d-4fbe-af86-f574df70cd13
Content-Type: application/json

{
  "bundle_id": "34dc9b7c-b1f6-4c08-8852-e0ad2d840f68",
  "tenant_id": "T-SYN-1",
  "legal_entity_id": "LE-SYN-1"
}
~~~

The JWT issuer, audience, client allowlist and trusted local public JWKS are provided by protected operator settings, never inferred from this request. The reviewer subject is verified from the token and checked against the **active scoped MariaDB grant**. A customer cannot select an arbitrary reviewer ID.

A successful first request returns **201**, with `audit_id`, status `COMPLETED` or `NEEDS_REVIEW`, `audit_executed` and `replayed=false`. An identical retry with the same UUID idempotency key returns **200** with the same run ID (or **202** while processing); reusing that key with a different bundle returns **409**. A request with missing/invalid Bearer token fails **401**; denied scope/grant **403**; missing bundle or inaccessible run **404**; bad input **422**. Unexpected execution failure returns **503** with a generic error code, never private file paths or finance data.

GET response includes the persisted JSON report and the same audit ID/status. No request should be cached; the resource server sets `Cache-Control: no-store`.

## Private bundle provision – not an HTTP operation

An operator-approved backend process must register a JSON manifest using `PrivateAuditStore.provision_bundle()`. No HTTP registration endpoint exists. The source root is set by trusted `LHFM_API_SOURCE_ROOT` configuration, separate from Apache DocumentRoot and from the Node marketing site.

The manifest contains exactly:
- `files`: `rule` JSON, `transactions` canonical CSV, `settlements` canonical CSV and `contract` (.pdf, .docx or synthetic .txt), each with private relative path and fixed SHA-256 digest;
- `source_system` identifier;
- `controls` from a **separate ERP control report** (or null, meaning audit cannot run to final result);
- `completeness`: three explicit boolean assertions;
- `approval_receipt`: signed HMAC receipt, already active in MariaDB registry.

Registration checks the source file hashes, the receipt's tenant/legal entity, the rule digest and reviewed contract digest. Each execution copies file bytes into an isolated temporary snapshot **and verifies original SHA-256 while copying**. The verified input then passes only through `AuthenticatedApprovalService.audit_csv()` → Frictionless/readiness checks → original Python Decimal rebate kernel, including the **row-locked MariaDB ACTIVE approval guard** and JWT revalidation.

Original files remain the operator's responsibility. No self-service user-upload, malware scanning, encrypted object storage or data-retention workflow has been added yet.

## Data persistence

Existing dedicated MariaDB database, **new tables only**:
- `lhfm_api_bundles` – scoped, server-provisioned source manifest;
- `lhfm_api_runs` – unique scoped idempotency key, reviewer ownership, audit status and immutable-by-application completed JSON result.

Migration in `sql/002_audit_api.sql`. Do **not** run CI test provisioning scripts against production. A partial run after a process crash remains `PROCESSING` and requires operator recovery; automatic replay/requeue is intentionally absent. A verified report is **not** proof of legal entitlement, realized recovery or an invoice. Billing is **0.00** until separate verified recovery events exist.

## Local staging startup only

Inside a private developer/CI environment:

~~~bash
python -m pip install -e ".[import,registry,auth,universal,api]"
# Apply sql/001_approval_registry.sql and sql/002_audit_api.sql
# via controlled migration tooling against a dedicated DB.
# Configure LHFM_DB_HOST/USER/PASSWORD/NAME, LHFM_APPROVAL_KEY_HEX,
# LHFM_OIDC_ISSUER, LHFM_OIDC_AUDIENCE, LHFM_OIDC_JWKS_FILE,
# LHFM_OIDC_ALLOWED_CLIENT_IDS, LHFM_API_SOURCE_ROOT using trusted secrets.
uvicorn lowhangingfruitme.api.http:create_app_from_environment \
  --factory --host 127.0.0.1 --port 8107
~~~

The local port is only a proposal: verify host conflicts, capacity and TLS reverse proxy setup before any server installation. The existing WordPress/Apache deployment is untouched.

## Validation and critical remaining gaps

`tests/test_api.py` uses synthetic RSA JWTs, real isolated MariaDB and source fixtures. Regression cases cover invalid/missing token and OAuth client, missing scope, cross-tenant denial, unauthorized/unknown bundle, request-path injection, idempotent replay and conflicting use, **concurrent reservation**, file/hash tampering, wrong signed rule and contract hashes, revoked approval, missing independent controls, private path traversal and symlink rejection, completed report with exact `2500.00` calculated difference and **0.00** billable fee.

No actual external IdP enrollment, no end-user registration, no dedicated HTTP rate/CPU limiter, no process-isolated document parser, no real ERP connection, no end-to-end upload, no scalable asynchronous queue, no independent filesystem/object storage protection, no recovery ledger or public portal-to-API integration. A real multi-tenant production release remains blocked.

**Next engineering gate:** authenticated upload-intent and private file staging with scanner isolation, immutable store ownership, tenant/engagement authorization, retention and a bounded worker queue. Do not introduce public multipart upload until these security controls exist.
