"""Signed, persistent and scoped ERP mapping approvals for reviewed upload bundles.

Only the authenticated ReviewedBundleService issues receipts. The HMAC key is
trusted server-side; mapping approval never authorizes the contractual rule.
All rows remain locked while the existing signed-rule audit executes.
"""
from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone
from hashlib import sha256
import hmac
import re
from typing import Any, Iterator
from uuid import UUID

from .approval import _json_bytes, _key
from .approval_registry import ApprovalRegistry

PREFIX = b"LowHangingFruitMe:mapping:v1\0"
FIELDS = frozenset({
    "version", "bundle_id", "dataset", "tenant_id", "legal_entity_id",
    "reviewer_id", "approval_id", "source_sha256", "mapping_sha256", "approved_at",
})
DATASETS = ("transactions", "settlements")
DIGEST = re.compile(r"^[a-f0-9]{64}$")


def _digest(value: Any, field: str) -> str:
    if not isinstance(value, str) or not DIGEST.fullmatch(value):
        raise ValueError(f"{field} must be a lowercase sha256")
    return value


def _text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not 0 < len(value) <= 128:
        raise ValueError(f"{field} must be a bounded nonempty string")
    return value


def _sign(body: dict[str, Any], key: bytes) -> dict[str, str]:
    return {**body, "signature": hmac.new(_key(key), PREFIX + _json_bytes(body), "sha256").hexdigest()}


def _verify(receipt: Any, *, key: bytes, bundle_id: str, dataset: str,
            tenant_id: str, legal_entity_id: str, reviewer_id: str,
            approval_id: str, source_sha256: str, mapping_sha256: str) -> str:
    if not isinstance(receipt, dict) or set(receipt) != FIELDS | {"signature"}:
        raise PermissionError("mapping approval receipt missing or malformed")
    body = {k: receipt[k] for k in FIELDS}
    if body["version"] != "1":
        raise PermissionError("mapping approval version unsupported")
    for name, expected in (
        ("bundle_id", bundle_id), ("dataset", dataset), ("tenant_id", tenant_id),
        ("legal_entity_id", legal_entity_id), ("reviewer_id", reviewer_id),
        ("approval_id", approval_id),
        ("source_sha256", _digest(source_sha256, "source_sha256")),
        ("mapping_sha256", _digest(mapping_sha256, "mapping_sha256")),
    ):
        if not isinstance(body[name], str) or not hmac.compare_digest(body[name], expected):
            raise PermissionError("mapping approval identity or source mismatch")
    try:
        signed_at = datetime.fromisoformat(body["approved_at"])
    except (ValueError, TypeError) as exc:
        raise PermissionError("invalid mapping approval time") from exc
    if signed_at.tzinfo is None or signed_at > datetime.now(timezone.utc):
        raise PermissionError("invalid mapping approval time")
    expected_sig = _sign(body, key)["signature"]
    signature = receipt["signature"]
    if not isinstance(signature, str) or not hmac.compare_digest(signature, expected_sig):
        raise PermissionError("mapping approval HMAC invalid")
    return sha256(_json_bytes(receipt)).hexdigest()


class MappingApprovalRegistry:
    def __init__(self, *, registry: ApprovalRegistry, key: bytes):
        self._connect = registry._connect
        self._key = _key(key)

    def register_bundle(self, *, bundle_id: str, tenant_id: str,
                        legal_entity_id: str, reviewer_id: str,
                        approval_id: str, provenance: dict[str, Any]) -> dict[str, dict[str, str]]:
        """Trusted caller only, after live token/DB authorization and rule approval."""
        if str(UUID(bundle_id)) != bundle_id:
            raise ValueError("noncanonical bundle_id")
        for field, val in (("tenant_id",tenant_id),("legal_entity_id",legal_entity_id),
                           ("reviewer_id",reviewer_id),("approval_id",approval_id)):
            _text(val,field)
        approved_at = datetime.now(timezone.utc).isoformat()
        receipts = {}
        for dataset in DATASETS:
            info = provenance.get(dataset)
            if not isinstance(info, dict):
                raise ValueError("both normalized datasets required")
            body = {
                "version": "1", "bundle_id": bundle_id, "dataset": dataset,
                "tenant_id": tenant_id, "legal_entity_id": legal_entity_id,
                "reviewer_id": reviewer_id, "approval_id": approval_id,
                "source_sha256": _digest(info.get("original_sha256"), "source_sha256"),
                "mapping_sha256": _digest(info.get("mapping_sha256"), "mapping_sha256"),
                "approved_at": approved_at,
            }
            receipts[dataset] = _sign(body, self._key)
        db = self._connect()
        try:
            with db.cursor() as cur:
                cur.execute(
                    """SELECT reviewer_id, state FROM lhfm_approval_records
                       WHERE approval_id=%s AND tenant_id=%s AND legal_entity_id=%s
                       FOR UPDATE""",
                    (approval_id, tenant_id, legal_entity_id),
                )
                approval = cur.fetchone()
                if not approval or approval["reviewer_id"] != reviewer_id or approval["state"] != "ACTIVE":
                    raise PermissionError("signed contract approval absent or inactive")
                cur.execute(
                    """SELECT role, active FROM lhfm_reviewer_grants
                       WHERE tenant_id=%s AND legal_entity_id=%s
                       AND reviewer_id=%s FOR UPDATE""",
                    (tenant_id, legal_entity_id, reviewer_id),
                )
                grant = cur.fetchone()
                if not grant or grant["role"] != "contract_reviewer" or not grant["active"]:
                    raise PermissionError("mapping reviewer has no active scope grant")
                for dataset in DATASETS:
                    receipt = receipts[dataset]
                    cur.execute(
                        """INSERT INTO lhfm_mapping_approvals
                           (bundle_id,dataset,tenant_id,legal_entity_id,reviewer_id,
                            approval_id,source_sha256,mapping_sha256,receipt_sha256,state)
                           VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,'ACTIVE')""",
                        (bundle_id, dataset, tenant_id, legal_entity_id,
                         reviewer_id, approval_id, receipt["source_sha256"],
                         receipt["mapping_sha256"],
                         sha256(_json_bytes(receipt)).hexdigest()),
                    )
                    cur.execute(
                        """INSERT INTO lhfm_mapping_approval_events
                           (bundle_id,dataset,tenant_id,legal_entity_id,actor_id,event_type)
                           VALUES (%s,%s,%s,%s,%s,'ISSUED')""",
                        (bundle_id, dataset, tenant_id, legal_entity_id, reviewer_id),
                    )
            db.commit()
            return receipts
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    @contextmanager
    def guard(self, *, receipts: Any, provenance: dict[str, Any],
              bundle_id: str, tenant_id: str, legal_entity_id: str,
              reviewer_id: str, approval_id: str) -> Iterator[None]:
        """Hold BOTH mapping rows through full signed-rule calculation."""
        if not isinstance(receipts, dict) or set(receipts) != set(DATASETS):
            raise PermissionError("both mapping approval receipts required")
        if not isinstance(provenance, dict):
            raise PermissionError("mapping provenance missing")
        signed = {}
        for dataset in DATASETS:
            info = provenance.get(dataset)
            if not isinstance(info, dict):
                raise PermissionError("missing mapping source provenance")
            signed[dataset] = _verify(
                receipts[dataset], key=self._key, bundle_id=bundle_id,
                dataset=dataset, tenant_id=tenant_id, legal_entity_id=legal_entity_id,
                reviewer_id=reviewer_id, approval_id=approval_id,
                source_sha256=info.get("original_sha256"),
                mapping_sha256=info.get("mapping_sha256"),
            )
        db = self._connect()
        try:
            with db.cursor() as cur:
                cur.execute(
                    """SELECT dataset,approval_id,source_sha256,mapping_sha256,
                              receipt_sha256,reviewer_id,state
                       FROM lhfm_mapping_approvals
                       WHERE bundle_id=%s AND tenant_id=%s AND legal_entity_id=%s
                       ORDER BY dataset FOR UPDATE""",
                    (bundle_id,tenant_id,legal_entity_id),
                )
                rows = {r["dataset"]:r for r in cur.fetchall()}
                if set(rows) != set(DATASETS):
                    raise PermissionError("registered mapping approvals incomplete")
                for dataset in DATASETS:
                    row = rows[dataset]
                    receipt = receipts[dataset]
                    if row["state"] != "ACTIVE":
                        raise PermissionError("mapping approval revoked before dispatch")
                    for name, expected in (
                        ("approval_id",approval_id),("reviewer_id",reviewer_id),
                        ("source_sha256",receipt["source_sha256"]),
                        ("mapping_sha256",receipt["mapping_sha256"]),
                        ("receipt_sha256",signed[dataset]),
                    ):
                        if not hmac.compare_digest(row[name], expected):
                            raise PermissionError("registered mapping content mismatch")
                cur.execute(
                    """SELECT role,active FROM lhfm_reviewer_grants
                       WHERE tenant_id=%s AND legal_entity_id=%s AND reviewer_id=%s
                       FOR UPDATE""", (tenant_id,legal_entity_id,reviewer_id),
                )
                grant=cur.fetchone()
                if not grant or grant["role"]!="contract_reviewer" or not grant["active"]:
                    raise PermissionError("mapping reviewer grant revoked")
                yield
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    def revoke_bundle(self, *, bundle_id: str, tenant_id: str,
                      legal_entity_id: str, reviewer_id: str) -> bool:
        """Trusted reviewer-only fail-closed revocation, with append-only evidence."""
        db = self._connect()
        try:
            changed = False
            with db.cursor() as cur:
                cur.execute(
                    """SELECT dataset,reviewer_id,state FROM lhfm_mapping_approvals
                       WHERE bundle_id=%s AND tenant_id=%s AND legal_entity_id=%s
                       ORDER BY dataset FOR UPDATE""",
                    (bundle_id,tenant_id,legal_entity_id),
                )
                records = cur.fetchall()
                if not records or any(r["reviewer_id"] != reviewer_id for r in records):
                    raise PermissionError("mapping not found in reviewer scope")
                cur.execute(
                    """SELECT role,active FROM lhfm_reviewer_grants
                       WHERE tenant_id=%s AND legal_entity_id=%s AND reviewer_id=%s
                       FOR UPDATE""", (tenant_id,legal_entity_id,reviewer_id),
                )
                grant=cur.fetchone()
                if not grant or grant["role"]!="contract_reviewer" or not grant["active"]:
                    raise PermissionError("mapping reviewer lacks active grant")
                for row in records:
                    if row["state"] == "ACTIVE":
                        cur.execute(
                            """UPDATE lhfm_mapping_approvals
                               SET state='REVOKED',revoked_at=UTC_TIMESTAMP(6)
                               WHERE bundle_id=%s AND dataset=%s AND state='ACTIVE'""",
                            (bundle_id,row["dataset"]),
                        )
                        cur.execute(
                            """INSERT INTO lhfm_mapping_approval_events
                               (bundle_id,dataset,tenant_id,legal_entity_id,actor_id,event_type)
                               VALUES (%s,%s,%s,%s,%s,'REVOKED')""",
                            (bundle_id,row["dataset"],tenant_id,legal_entity_id,reviewer_id),
                        )
                        changed = True
            db.commit()
            return changed
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()
