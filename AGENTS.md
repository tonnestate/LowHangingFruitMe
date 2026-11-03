# LowHangingFruitMe – implementation guardrails

## Authoritative sources
Read actual GitHub main HEAD and these files before editing: docs/CONCEPT.md, docs/DONORS.md, docs/API_AND_DATA.md, docs/LEGAL_AND_REVENUE.md, docs/DELIVERY_PLAN.md and docs/IMPLEMENTATION_STATUS.md. A statement in a document is not proof of implementation.

## Engineering contract

1. Change only the requested workstream. Integrate into the actual program path rather than building an unrelated second implementation. Keep main installable and tested.
2. Money = Decimal, explicit cent rounding and exact contract semantics; never silently infer ambiguous tiers, supplier identity, FX, credit-note attribution or data completeness.
3. Every computed line must link to source ID, original file hash/page or row, rule version and calculation version. Source content is untrusted.
4. A model may propose rules but cannot approve or authoritatively calculate a contractual monetary entitlement. NEVER rely on `approved=true` alone; canonical customer audit requires verified HMAC receipt bound to exact contract document digest, tenant, legal entity and rule hash. Receipt issuance must be behind real authenticated role checks before deployment.
5. A calculated difference is **not** a legally established claim, realised recovery or automatically billable success fee.
6. Do not add whole ERP backends, new DBs, cloud AI services or duplicated FruitStack orchestration without explicit need and verification.
7. No customer data, passwords, private FruitStack code or live financial records in this public repo.
8. Every donor must have source, licence, dependency provenance, reproducible test and benchmark before being called integrated or production ready.
9. External actions require authority and idempotency. No automated supplier communication, Inkasso or invoice creation based merely on an LLM proposal.
10. Document actual commands, result evidence and gaps; no fabricated CI/production claims.

## Verification commands

    python -m pip install -e ".[import]"
    python -m unittest discover -s tests -v
    python -m compileall -q src tests
    python -m lowhangingfruitme.cli tests/fixtures/flat_rebate.json
    lhfm audit-csv --rule tests/fixtures/rule.json --transactions tests/fixtures/transactions.csv --settlements tests/fixtures/settlements.csv --source-system erp --confirm-transactions-complete --confirm-settlements-complete --confirm-agreements-complete

Docling integration requires separate optional installation and real PDF acceptance on the actual deployment host.

**CI-only receipt generation:** `tests/scripts/make_synthetic_approval.py` assumes a fictitious reviewer and MUST NOT be exposed in production. Real issuance requires upstream authenticated actor, role/tenant authorization, stable backend key custody, replay/revocation storage and audit log.

## Registry requirement (v0.5.0)
Canonical customer CSV audits require a registered ACTIVE approval with matching tenant/entity scope and a live reviewer grant. All final calculations must execute inside `ApprovalRegistry.guard()` so a concurrent revoke cannot commit between verification and completion. The future login/IdP must authenticate the actor; passing a reviewer ID to the library is not authentication. Never expose test-only reviewer provisioning or signer scripts.

## Access tokens / auth facade (v0.6.0)

All future customer-facing authentication **must** use `AccessTokenVerifier` and `AuthenticatedApprovalService` or an equally verified boundary. Never expose raw `ApprovalRegistry.register/revoke` or `issue_approval` as endpoints accepting arbitrary `authenticated_actor_id` strings. Accept only RS256 access tokens (`typ=at+jwt`) from configured HTTPS issuer/audience/client; never fetch token-provided key URLs, accept ID tokens, or infer tenant permissions from token claims. The DB reviewer grant must be checked before filesystem access and again within the row-locked calculation. Local CLI remains a synthetic/dev utility, not an HTTP backend.

## Next.js marketing website – separate public workstream

`portal/` is an authorized, independent Next.js marketing application, **not** a WordPress plugin or the protected customer service. Only the tested `docs/Neon-Low-Hanging-FruitMe-Banner.png` may provide brand colors; generate CSS palette and pixel provenance from the actual original at build time. Do not adopt DistroAgents copyrights, assets, text or unjustified statistics. Keep 3% of **verified actually realized incremental net recovery** as commercial target; pilot contracting still requires legal acceptance. No invented customer cases, certifications, SOC 2, ERP connectors or autonomous claim recovery. Public launch must remain disabled until real legal text, protected contact paths, HTTPS, security and authorization are independently approved. The existing Apache/WordPress vhosts must never be changed in a development run.

`npm test`, `npm run build`, `npm run typecheck`, `npm run pack:standalone` (inside portal) plus CI Playwright 1440/768/390 are the frontend release evidence. Never claim a VPS deployment without inspecting and operating the actual server with explicit authority.

## Audit API v0.8 – protected private-bundle boundary

The HTTP API under `src/lowhangingfruitme/api/` allows only `POST /v1/audits` and `GET /v1/audits/{id}` for a verified JWT subject with the active exact scoped MariaDB reviewer grant. Never accept filesystem paths, rule JSON, unsigned receipt content, customer-supplied approval keys or completeness claims in HTTP requests. Source manifests are operator-provisioned and must be SHA256-bound to actual private source bytes and the signed approval receipt; snapshot every source prior to calculation. Idempotency must be enforced by the MariaDB UNIQUE constraint even under concurrent requests; crashes remain explicit PROCESSING until manual recovery. No implicit repeat execution and no fee based on calculated discrepancies. The local API is **not safe for production/public upload** without a real IdP, tenant enrollment, private storage, scanning, queue isolation, limits and an operational security review. See `docs/AUDIT_API.md`.

## Private upload Staging v0.9

`POST /v1/uploads`, `PUT /v1/uploads/{id}/content` and `GET /v1/uploads/{id}` are the ONLY current HTTP upload paths. Require an actual verified RS256 access-token subject, `lhfm:upload:write` and live tenant/legal reviewer grant. Never trust client filenames, URLs, filesystem paths, media types, scanner status or approval content. Strict 16-MiB streaming cap and exact SHA-256 + byte length required. Stage files exclusively in a 0700 private root, file mode 0600, with MariaDB one-shot state transitions. Only a positive actual ClamAV verdict from a separately provisioned LOCAL UNIX-socket scanner permits post-scan file inspection and promotion. Production configuration without a trusted ClamAV service must be fail-closed. **CLEAN != approved financial data**; never feed CLEAN files directly to the audit engine or approve rules automatically. Uploaded content must stay outside the operator-approved source root and Apache public files. Work remaining: real ClamAV test, crypto storage, retention, formal file-to-dataset promotion, roles and browser login, HTTP rate limits and ongoing operational checks. See `docs/UPLOAD_INTAKE.md`.

## End-to-end pilot 0.12 safety boundary

A customer-facing report is downloadable **only** with active reviewer and tenant/legal entity permissions, both audit/ledger scopes, an actually completed EVIDENCED audit, reconciled ledger amounts and original source hashes. Always keep a calculated variance separate from manually attested realization and legally billable fees. The 3%-fee is a proposal only; `fee_due_net` remains zero until an explicit contractual fee allocation and invoicing approval exists. Never treat a signed mapping, a synthetic PDF or a finance actor assertion as independently proven bank settlement. Maintain fail-closed read-only exports and never leak auth tokens or private source paths.
