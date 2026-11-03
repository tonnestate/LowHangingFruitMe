# Private file intake – LowHangingFruitMe v0.9.0

**Implemented code:** `src/lowhangingfruitme/api/uploads.py` and the three HTTP routes in `src/lowhangingfruitme/api/http.py`.  
**Status:** authenticated, bounded private staging with a mandatory scanner verdict. **Not a production customer upload or an accepted financial document repository.** No actual ClamAV daemon or external IdP is connected to the production VPS.

## HTTP contract

All calls require an RFC-9068-style RS256 access JWT for the configured API audience, OAuth scope **`lhfm:upload:write`**, and an active `contract_reviewer` grant for the supplied tenant and legal entity in the existing MariaDB registry. Tenant labels provided by clients never grant authority on their own.

**POST `/v1/uploads`** creates a single-use 15-minute upload intent with exact byte size, lowercase SHA-256, and one of five categories. The body must contain exactly:

~~~json
{
  "tenant_id": "T-SYN-1",
  "legal_entity_id": "LE-SYN-1",
  "kind": "ERP_CSV",
  "byte_size": 14582,
  "sha256": "0000000000000000000000000000000000000000000000000000000000000000"
}
~~~

The SHA-256 shown above is **a placeholder**, not a valid digest of a real file. The server assigns a UUID; the caller does **not** supply a filesystem path, filename or directory.

**PUT `/v1/uploads/{upload_id}/content?tenant_id=...&legal_entity_id=...`** transmits the exact raw bytes with `Content-Type: application/octet-stream` and Bearer auth. Maximum **16 MiB**, declared byte count must match exactly, SHA-256 must match the hash supplied to POST. Multipart forms are **not** accepted. No chunk-resume or repeated PUT after consumption: a failed transfer becomes `REJECTED` and requires a new intent.

**GET `/v1/uploads/{upload_id}?tenant_id=...&legal_entity_id=...`** returns only scoped metadata/status and never file bytes, a private storage path, or a download URL. Final successful status is `CLEAN` **with `usable_for_audit=false`**. It means only scan + basic format checks passed; it is **not** proof of valid accounting, complete ERP data, or accepted contract clauses.

### Supported categories (pilot)

| kind | Expected file | Inspection after malware scanner |
|---|---|---|
| `ERP_CSV` | UTF-8 CSV | Null-byte/encoding check, no ledger interpretation yet |
| `ERP_XLSX` | XLSX | ZIP envelope/layout and bounded decompression safeguards |
| `INVOICE_XML` | XML | Defused-XML parsing, recognized Invoice/CreditNote/CrossIndustryInvoice root, no complete invoice mapping |
| `CONTRACT_PDF` | PDF | %PDF signature, no automated contract acceptance |
| `CONTRACT_DOCX` | DOCX | ZIP envelope/layout safeguards, no automated contract acceptance |

Unrecognized formats, macros/scripts/executables and arbitrary archives are rejected. The document parser is **not** a comprehensive malware or format validator.

## Security and failure behavior

1. A dedicated runtime account owns a **0700** private upload directory, outside the Apache DocumentRoot, WordPress and `LHFM_API_SOURCE_ROOT`. The source root and upload root must not overlap as parent/child in the direction of untrusted files entering the audit root.
2. MariaDB table `lhfm_uploads` records tenant, entity, verified actor, UUID, claimed size and SHA-256 and state. State transitions are SQL-conditional and tenant-/reviewer-bound. `PENDING` expires in 15 minutes; after claim the intent becomes `RECEIVING` and cannot be claimed again. Any error becomes `REJECTED`; a worker crash can leave `RECEIVING` until operator cleanup.
3. File bytes stream into an exclusively created private `.part` path with mode 0600. The code hashes while copying and stops above the declared size or 16 MiB.
4. A **separately configured** trusted ClamAV daemon is contacted via a local UNIX socket using the `zINSTREAM` protocol with a strict timeout. Only an exact `stream: OK` verdict is accepted; infection, timeout, unreachable daemon and ambiguous responses all block promotion.
5. After the scanner verdict, basic file-type inspection runs. A successful file is atomically linked to an unguessable UUID filename; no existing file is overwritten. The temporary file is removed.
6. No file is promoted to a financial dataset or audit bundle by these endpoints. Separately approved contract/rule versions, data mapping, independently supplied ERP control reports and a source-bound signed receipt are still required under the existing `v0.8` calculation guard.

No external filename/URL, server file path, contract override, tax logic, reviewer identity, scan verdict, completeness assertion or source approval receipt may be supplied through the upload API.

## Configuration / isolated development

Only trusted operating configuration, **not checked into GitHub**, may enable uploads:

~~~text
LHFM_UPLOAD_ROOT=/private/absolute/path/owned-by-app
LHFM_CLAMD_UNIX_SOCKET=/run/clamav/clamd.ctl
~~~

The upload root must already exist and have mode **0700**. The clamd UNIX socket path must be explicitly configured; no remote URL scanner is used. Both variables are optional for the legacy v0.8 audit service, but when either is missing, upload endpoints return **503** and cannot accept files. A configured socket without a reachable daemon also causes upload failure and discarded data.

SQL migration: `sql/003_private_uploads.sql` after 001/002, run only through controlled database migration. **CI's** synthetic setup script never runs against a non-`lhfm_test` database.

## Evidence

[GitHub Actions run 41593011185](https://github.com/tonnestate/LowHangingFruitMe/actions/runs/41593011185): **175 Python tests passed each on 3.11 and 3.12** with real MariaDB 11.4. Includes authenticated POST/PUT/GET, isolated scoped permission, stream/size/hash validation, no overwrite, expired and concurrently claimed intents, invalid PDF, unsafe XML, no financial approval bypass, simulated infected and unavailable scanner cases.

An additional **local fake UNIX socket server** verifies the implementation of the ClamAV INSTREAM wire protocol. This **is not** an acceptance test against a real running ClamAV instance or a malware-detection efficacy test. No scanned customer file, personal data, document download, browser account or production server was involved.

## Still blocking live public customer upload

- Real ClamAV service, virus-signature update lifecycle, failure monitoring, file quarantine operator workflow and post-cleanup automation.
- Hardened reverse-proxy body limits, request/concurrency rate limits, authenticated company onboarding, per-user quotas, independent role provisioning, key/session revocation.
- Encrypted tenant-protected object storage, at-rest encryption/key rotation, retention/legal hold and deletion/DSGVO workflows, disaster recovery and privacy approval.
- Controlled promotion of a **clean** file into a tenant-owned immutable data snapshot, reviewed column mapping/contract extraction, and documented link to an approved engagement.
- Durable asynchronous jobs with retry/reconciliation, invoice XML extraction, contract OCR review and the commercial recovery ledger.
- Real endpoint deployment, TLS domain, production IdP, load/security tests, and actual legal notices/contract consent.

**Next implementation gate:** authenticated engagement ownership and controlled promotion of already CLEAN private uploads into source-bound datasets, retaining original provenance. Never feed an unreviewed or unscanned upload directly to `audit_from_csv()`.
