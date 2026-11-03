# Contract Rule Approval – signed rule receipts with v0.13 R2 semantic binding

**Status:** Implemented for local canonical CSV checks, tested with synthetic records. **Not** a production identity or legal-signature service.

## 1. Purpose

No customer-facing audit may treat a plain `approved: true` as authorization. The actual contract revision and its cited bonus rule must be tied to a review decision. The existing pure calculation kernel remains usable for numerical research, but without a trusted receipt it reports `REVIEW_REQUIRED` and `UNVERIFIED_APPROVAL_CONTEXT`, never `EVIDENCED`.

## 2. Cryptographic record contract

The receipt contains exactly:
- `version` = 1;
- unique `approval_id` (the caller supplies it; uniqueness is **not yet** persisted);
- `tenant_id` and `legal_entity_id`;
- `reviewer_id` and `reviewer_role=contract_reviewer` (signer asserts these, not independently authenticated here);
- UTC ISO 8601 `approved_at`;
- `rule_sha256`, computed from a canonical validated rule projection including rate, tiers, supplier, agreement, period, currency, basis, source references and revision;
- `document_sha256`, measured from exact original contract bytes passed to the local audit;
- `source_revision_id`, indicating the reviewed source revision;
- HMAC-SHA256 `signature` over all the above via domain-separated canonical JSON.

The HMAC secret must have at least 32 bytes. The local CLI reads only `LHFM_APPROVAL_KEY_HEX` from the process environment; it does not accept a key via the JSON report. Signatures are compared with `hmac.compare_digest` and rejected if source/rule/scope data change.

The system checks the signature, declared role, timestamp and source/rule/scope hashes. It does not itself prove: (a) signer employment and authorization, (b) legal validity of any contract, (c) whether the source file is an authentic supplier agreement, (d) whether a signed approval was subsequently revoked, or (e) uniqueness of approval IDs. Those demand authenticated backend state and independent policy checks.

## 3. Strict workflow

1. A trusted uploader stores immutable contract bytes and verifies source permissions.
2. A document adapter identifies evidence spans and proposes a rule; the rule remains unapproved.
3. An authenticated contract reviewer examines the source document and rule. **Future product IAM must** enforce role and tenant access and record the decision durably.
4. A trusted service (not the user or an LLM) issues a signed receipt. The Python `issue_approval` function is a low-level helper and must not be exposed directly in public HTTP endpoints.
5. Canonical CSV intake loads the receipt and the exact source file, verifies HMAC plus tenant/entity/rule/document matching, then assesses source control totals.
6. Only if signed approval and data readiness pass may the canonical audit produce an `EVIDENCED` calculation status. This is still **not** a legally confirmed, collectible or paid claim.
7. Superseded/revoked approvals require persistent inventory and re-run; **not implemented**.

## 4. Local test recipe

All sample data are synthetic and intentionally fictitious. To reproduce the CI path, install `.[import]`, create a fresh random 32-byte hex secret in `LHFM_APPROVAL_KEY_HEX`, run `tests/scripts/make_synthetic_approval.py` to produce a receipt for `tests/fixtures/rule.json` and `tests/fixtures/synthetic_agreement.txt`. Then call `lhfm audit-csv` with `--approval`, `--contract-source`, `--tenant-id T-SYN-1`, `--legal-entity-id LE-SYN-1` and the pre-existing data/readiness flags. The exact command is in the README.

**The test factory assumes a synthetic reviewer identity without authentication and is not allowed in production.** Missing or invalid receipts produce review/block statuses without executing the customer audit.

## 5. Release blockers

- Trusted user authentication, reviewer RBAC and explicit segregation of duties, including seller/customer role differences.
- Immutable approval/revocation ledger in the product metadata store, unique approval IDs, supersession and binding to contracted customer scope.
- Protected signing service with secret rotation/key identifiers, key version retention and no signer access for general users.
- Verified source registry, original file hash and signed/registered source revision, retention policies and backup/restore tests.
- Replay- and cross-process concurrency tests; revocation checked **at dispatch**, not only at a stale prior snapshot.
- Security and legal review of signing/approval workflow, customer data and regulated service boundaries.

**Decision:** The next product-level feature should be an authenticated approval/revocation storage boundary before exposing a public API or customer portal.

## v0.5.0 amendment – persistent registry now implemented

The earlier v0.4 descriptions of missing revocation/persistence have now been **partly superseded**. `src/lowhangingfruitme/approval_registry.py` implements MariaDB ACTIVE/REVOKED persistence, scoped reviewer grants and a SELECT FOR UPDATE calculation guard, and the canonical CSV path refuses to produce final findings without a registry.

This does **not** supply actual reviewer authentication, revocation-aware completed-report distribution, service-wide identity integration, production key custody or legal signature status. See [APPROVAL_REGISTRY.md](APPROVAL_REGISTRY.md) and [EVIDENCE.md](../EVIDENCE.md).

## v0.13: mandatory R2 semantic attestation

Every non-FLAT_RATE rule must include a versioned, exact `tier_semantics` value:
```json
{
  "application": "EXCESS_ONLY",
  "evidence_ref": "agreement.pdf#page=2&clause=4",
  "reviewed": true
}
```
Allowed applications: `FULL_BASE` exclusively for `RETROACTIVE_FULL_BASE`; `EXCESS_ONLY` (exactly one threshold) or `BANDS` (at least two ordered thresholds) for `MARGINAL_PER_TIER`; `FIXED_REWARD` for `FIXED_THRESHOLD_REWARD`. The evidence reference must exist in the rule's approved `evidence_refs` list. R1 rejects extraneous `tier_semantics`.

`rule_sha256` cryptographically binds the parsed tier semantics **only for R2**; the legacy R1 projection is unchanged. The signed human-review marker remains an assertion of an authenticated and authorized reviewer behind `AuthenticatedApprovalService`, not an AI interpretation or independent legal proof. An unknown/mismatched source clause is review-required; no speculative fallback calculation. Incoming bundle HTTP errors use `RULE_SEMANTICS_NEEDS_REVIEW`.
