"""Authenticated and reviewed promotion: clean uploads -> signed audit bundle.

The caller must supply a human-reviewed rule and complete, source-hash-bound
mapping plans. Neither the scanner nor AI can approve contractual terms.
All financial calculations still run through AuthenticatedApprovalService.
"""
from __future__ import annotations

from contextlib import ExitStack
from hashlib import sha256
import json
import os
from pathlib import Path
import shutil
from typing import Any
from uuid import uuid4

from ..approval_service import AuthenticatedApprovalService
from ..mapping_approval import MappingApprovalRegistry
from ..universal_import import inspect_source, normalize_source
from .store import PrivateAuditStore
from .uploads import UploadService, UploadRejected


class ReviewRequired(ValueError):
    pass


def _private_file(path: Path, data: bytes) -> str:
    if len(data) > 16 * 1024 * 1024 or not data:
        raise ValueError("generated source is empty or too large")
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    fd = os.open(path, flags, 0o600)
    with os.fdopen(fd, "wb") as output:
        output.write(data)
        output.flush()
        os.fsync(output.fileno())
    return sha256(data).hexdigest()


class ReviewedBundleService:
    def __init__(
        self, *, service: AuthenticatedApprovalService,
        uploads: UploadService, store: PrivateAuditStore,
    ) -> None:
        self.service = service
        self.uploads = uploads
        self.store = store
        self.mapping_registry = MappingApprovalRegistry(
            registry=service.registry, key=service.approval_key,
        )
        if store.root == uploads.root or store.root in uploads.root.parents or uploads.root in store.root.parents:
            raise ValueError("clean staging and approved audit source roots must be independent")

    def inspect(
        self, access_token: str, *, tenant_id: str, legal_entity_id: str,
        upload_id: str, dataset: str, sheet_name: str | None,
    ) -> dict[str, Any]:
        actor = self.service._verified_actor(
            access_token, scope="lhfm:upload:write",
            tenant_id=tenant_id, legal_entity_id=legal_entity_id,
        )
        if dataset not in ("transactions", "settlements"):
            raise ValueError("unknown financial dataset")
        with self.uploads.snapshot_clean(
            upload_id=upload_id, tenant_id=tenant_id,
            legal_entity_id=legal_entity_id, reviewer_id=actor.subject,
            accepted_kinds=("ERP_CSV", "ERP_XLSX"),
        ) as (source, record):
            info = inspect_source(source, dataset=dataset, sheet_name=sheet_name)
        return {**info, "upload_id": upload_id, "dataset": dataset,
                "review_required": True, "audit_ready": False}

    def prepare(
        self, access_token: str, *, tenant_id: str, legal_entity_id: str,
        transaction_upload_id: str, settlement_upload_id: str,
        contract_upload_id: str, transaction_plan: dict[str, Any],
        settlement_plan: dict[str, Any], rule: dict[str, Any],
        source_system: str, source_revision_id: str,
        controls: dict[str, Any] | None, completeness: dict[str, bool],
        confirm_contract_review: bool, confirm_mapping_review: bool,
    ) -> dict[str, Any]:
        actor = self.service._verified_actor(
            access_token, scope="lhfm:approval:write",
            tenant_id=tenant_id, legal_entity_id=legal_entity_id,
        )
        actor.require_scope("lhfm:upload:write")
        if confirm_contract_review is not True or confirm_mapping_review is not True:
            raise ReviewRequired("human contract and mapping review must be confirmed")
        if not isinstance(source_revision_id, str) or not source_revision_id.strip():
            raise ReviewRequired("contract revision reference required")
        if not isinstance(transaction_plan, dict) or not isinstance(settlement_plan, dict):
            raise ReviewRequired("reviewed source mapping plans required")
        for plan in (transaction_plan, settlement_plan):
            if plan.get("reviewed_by") != actor.subject or plan.get("confirmed") is not True:
                raise ReviewRequired("mapping plan reviewer must equal authenticated subject")
        if not isinstance(rule, dict) or rule.get("approved") is not True or not rule.get("evidence_refs"):
            raise ReviewRequired("a reviewed, sourced and approved contract rule is required")
        if transaction_upload_id == settlement_upload_id or contract_upload_id in (
            transaction_upload_id, settlement_upload_id
        ):
            raise ReviewRequired("each financial source needs an independent upload identity")

        with ExitStack() as stack:
            txn, tmeta = stack.enter_context(self.uploads.snapshot_clean(
                upload_id=transaction_upload_id, tenant_id=tenant_id,
                legal_entity_id=legal_entity_id, reviewer_id=actor.subject,
                accepted_kinds=("ERP_CSV", "ERP_XLSX"),
            ))
            settled, smeta = stack.enter_context(self.uploads.snapshot_clean(
                upload_id=settlement_upload_id, tenant_id=tenant_id,
                legal_entity_id=legal_entity_id, reviewer_id=actor.subject,
                accepted_kinds=("ERP_CSV", "ERP_XLSX"),
            ))
            contract, cmeta = stack.enter_context(self.uploads.snapshot_clean(
                upload_id=contract_upload_id, tenant_id=tenant_id,
                legal_entity_id=legal_entity_id, reviewer_id=actor.subject,
                accepted_kinds=("CONTRACT_PDF", "CONTRACT_DOCX"),
            ))
            normalized_txn = normalize_source(
                txn, dataset="transactions", source_system=source_system,
                plan=transaction_plan,
            )
            normalized_settlements = normalize_source(
                settled, dataset="settlements", source_system=source_system,
                plan=settlement_plan,
            )
            # No source records are transformed silently or fabricated.
            bundle_id = str(uuid4())
            staging = self.store.root / (".prepare-" + bundle_id)
            final_dir = self.store.root / bundle_id
            staging.mkdir(mode=0o700)
            signed_id: str | None = None
            mapping_registered = False
            moved = False
            try:
                tx_data = normalized_txn.pop("canonical_csv").encode("utf-8")
                se_data = normalized_settlements.pop("canonical_csv").encode("utf-8")
                tx_digest = _private_file(staging / "transactions.csv", tx_data)
                se_digest = _private_file(staging / "settlements.csv", se_data)
                rule_digest = _private_file(
                    staging / "rule.json",
                    json.dumps(rule, ensure_ascii=False, sort_keys=True,
                               separators=(",", ":"), allow_nan=False).encode("utf-8"),
                )
                contract_name = "contract" + contract.suffix.lower()
                contract_digest = _private_file(staging / contract_name, contract.read_bytes())
                provenance = {
                    "transactions": {
                        "upload_id": transaction_upload_id,
                        "original_sha256": tmeta["expected_sha256"],
                        "mapping_sha256": normalized_txn["mapping_sha256"],
                        "rows": normalized_txn["rows"],
                    },
                    "settlements": {
                        "upload_id": settlement_upload_id,
                        "original_sha256": smeta["expected_sha256"],
                        "mapping_sha256": normalized_settlements["mapping_sha256"],
                        "rows": normalized_settlements["rows"],
                    },
                    "contract": {
                        "upload_id": contract_upload_id,
                        "original_sha256": cmeta["expected_sha256"],
                    },
                }
                # Row-level original-file/row references are kept in the
                # operator-only source directory, hash-bound to the report.
                lineage = {
                    "transactions": normalized_txn["lineage"],
                    "settlements": normalized_settlements["lineage"],
                }
                provenance["lineage_sha256"] = _private_file(
                    staging / "lineage.json",
                    json.dumps(lineage, ensure_ascii=False,
                               separators=(",", ":"), allow_nan=False).encode("utf-8"),
                )
                if final_dir.exists():
                    raise ValueError("target bundle already exists")
                staging.rename(final_dir)
                moved = True

                signed_id = str(uuid4())
                receipt = self.service.approve(
                    access_token, rule=rule, document_sha256=contract_digest,
                    source_revision_id=source_revision_id, approval_id=signed_id,
                    tenant_id=tenant_id, legal_entity_id=legal_entity_id,
                )
                mapping_receipts = self.mapping_registry.register_bundle(
                    bundle_id=bundle_id, tenant_id=tenant_id,
                    legal_entity_id=legal_entity_id, reviewer_id=actor.subject,
                    approval_id=signed_id, provenance=provenance,
                )
                mapping_registered = True
                manifest = {
                    "mapping_approvals": mapping_receipts,
                    "files": {
                        "rule": {"path": bundle_id + "/rule.json", "sha256": rule_digest},
                        "transactions": {"path": bundle_id + "/transactions.csv", "sha256": tx_digest},
                        "settlements": {"path": bundle_id + "/settlements.csv", "sha256": se_digest},
                        "contract": {"path": bundle_id + "/" + contract_name,
                                     "sha256": contract_digest},
                    },
                    "source_system": source_system,
                    "controls": controls,
                    "completeness": completeness,
                    "approval_receipt": receipt,
                    "provenance": provenance,
                }
                self.store.provision_bundle(
                    bundle_id=bundle_id, tenant_id=tenant_id,
                    legal_entity_id=legal_entity_id, manifest=manifest,
                )
                return {
                    "bundle_id": bundle_id, "approval_id": signed_id,
                    "status": "REGISTERED",
                    "mapping_approval_status": "SIGNED_REGISTERED",
                    "reviewed_by": actor.subject,
                    "provenance": provenance,
                    "source_ledger_complete_proven": False,
                    "audit_executed": False,
                }
            except Exception:
                if mapping_registered:
                    try:
                        self.mapping_registry.revoke_bundle(
                            bundle_id=bundle_id, tenant_id=tenant_id,
                            legal_entity_id=legal_entity_id, reviewer_id=actor.subject,
                        )
                    except Exception:
                        # Manual reconciliation required on unavailable DB.
                        pass
                if signed_id is not None:
                    try:
                        self.service.registry.revoke(
                            signed_id, tenant_id=tenant_id,
                            legal_entity_id=legal_entity_id,
                            authenticated_actor_id=actor.subject,
                        )
                    except Exception:
                        # Operational reconciliation is still mandatory if
                        # the DB is unavailable while rolling back.
                        pass
                shutil.rmtree(final_dir if moved else staging, ignore_errors=True)
                raise
