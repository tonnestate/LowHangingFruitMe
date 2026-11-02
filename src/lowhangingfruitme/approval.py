"""Tamper-evident contract rule approval receipts.

Authenticity requires a secret restricted to a trusted approval service AND
an externally authenticated reviewer; this library does not implement IAM.
No caller-supplied 'approved: true' can replace a verified receipt at the intake.
"""
from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
import hmac
import json
import os
import re
from typing import Any

from .rebate import BonusRule

RECEIPT_FIELDS = frozenset({
    "version", "approval_id", "tenant_id", "legal_entity_id",
    "reviewer_id", "reviewer_role", "approved_at", "rule_sha256",
    "document_sha256", "source_revision_id",
})
SIGNATURE_PREFIX = b"LowHangingFruitMe:approval:v1\0"


def _nonempty(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > 256:
        raise ValueError(f"{field}: nonempty string up to 256 characters required")
    return value.strip()


def _sha256_text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not re.fullmatch("[a-f0-9]{64}", value):
        raise ValueError(f"{field}: lowercase SHA256 digest required")
    return value


def _json_bytes(value: dict[str, Any]) -> bytes:
    return json.dumps(
        value, sort_keys=True, ensure_ascii=False, separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def _key(raw: bytes) -> bytes:
    if not isinstance(raw, bytes) or len(raw) < 32:
        raise ValueError("approval HMAC key must be >=32 secret bytes")
    return raw


def key_from_environment() -> bytes:
    """Read secret from trusted execution environment, never a user payload."""
    raw = os.environ.get("LHFM_APPROVAL_KEY_HEX", "")
    if not re.fullmatch(r"[a-fA-F0-9]{64,}", raw) or len(raw) % 2:
        raise RuntimeError("LHFM_APPROVAL_KEY_HEX is missing or invalid (>=32 bytes)")
    return _key(bytes.fromhex(raw))


def rule_sha256(rule: dict[str, Any]) -> str:
    """Versioned canonical input hash; no 'approved' boolean as authority."""
    parsed = BonusRule.load(rule)
    data = {
        "rule_id": parsed.rule_id, "revision": parsed.revision,
        "kind": parsed.kind.value, "supplier_id": parsed.supplier_id,
        "agreement_id": parsed.agreement_id, "currency": parsed.currency,
        "period_start": parsed.period_start.isoformat(),
        "period_end": parsed.period_end.isoformat(), "basis": parsed.basis,
        "rate": str(parsed.rate) if parsed.rate is not None else None,
        "tiers": [{
            "threshold": str(t.threshold),
            "rate": str(t.rate) if t.rate is not None else None,
            "reward": str(t.reward) if t.reward is not None else None,
        } for t in parsed.tiers],
        "evidence_refs": sorted(parsed.evidence_refs),
    }
    return sha256(_json_bytes(data)).hexdigest()


def issue_approval(
    rule: dict[str, Any], *, key: bytes, tenant_id: str,
    legal_entity_id: str, reviewer_id: str, approval_id: str,
    source_revision_id: str, document_sha256: str,
    approved_at: datetime,
    reviewer_role: str = "contract_reviewer",
) -> dict[str, str]:
    """Trusted service only. NEVER expose as a user-controlled endpoint.

    The caller MUST independently verify the reviewer's authenticated identity,
    reviewer role and access to the indicated tenant/source document.
    """
    _key(key)
    if not BonusRule.load(rule).approved:
        raise ValueError("cannot issue approval for a non-approved rule")
    if not BonusRule.load(rule).evidence_refs:
        raise ValueError("contract source evidence is missing")
    if reviewer_role != "contract_reviewer":
        raise ValueError("only contract_reviewer may issue a receipt")
    if not isinstance(approved_at, datetime) or approved_at.tzinfo is None:
        raise ValueError("approved_at must be timezone aware")
    if approved_at > datetime.now(timezone.utc):
        raise ValueError("approval date may not be in the future")
    body = {
        "version": "1", "approval_id": _nonempty(approval_id, "approval_id"),
        "tenant_id": _nonempty(tenant_id, "tenant_id"),
        "legal_entity_id": _nonempty(legal_entity_id, "legal_entity_id"),
        "reviewer_id": _nonempty(reviewer_id, "reviewer_id"),
        "reviewer_role": "contract_reviewer",
        "approved_at": approved_at.astimezone(timezone.utc).isoformat(),
        "rule_sha256": rule_sha256(rule),
        "document_sha256": _sha256_text(document_sha256, "document_sha256"),
        "source_revision_id": _nonempty(source_revision_id, "source_revision_id"),
    }
    signature = hmac.new(key, SIGNATURE_PREFIX + _json_bytes(body), "sha256").hexdigest()
    return {**body, "signature": signature}


def verify_approval(
    receipt: Any, rule: dict[str, Any], *,
    key: bytes, tenant_id: str, legal_entity_id: str,
    document_sha256: str,
) -> dict[str, str]:
    """Verify HMAC integrity plus exact tenant, legal entity, rule and source hash.

    Does NOT check revocation, reviewer IAM, nonce uniqueness or a trusted
    document registry; those require persistent authorization infrastructure.
    """
    _key(key)
    if not isinstance(receipt, dict) or set(receipt) != RECEIPT_FIELDS | {"signature"}:
        raise ValueError("approval receipt missing or unexpected fields")
    if not BonusRule.load(rule).approved:
        raise ValueError("rule flag is not approved")
    if not BonusRule.load(rule).evidence_refs:
        raise ValueError("contract evidence references are missing")
    body = {name: receipt[name] for name in RECEIPT_FIELDS}
    if body["version"] != "1" or body["reviewer_role"] != "contract_reviewer":
        raise ValueError("unsupported approval version or reviewer role")
    for name in ("approval_id", "tenant_id", "legal_entity_id",
                 "reviewer_id", "source_revision_id"):
        _nonempty(body[name], name)
    _sha256_text(body["rule_sha256"], "rule_sha256")
    _sha256_text(body["document_sha256"], "document_sha256")
    expected = hmac.new(key, SIGNATURE_PREFIX + _json_bytes(body), "sha256").hexdigest()
    signature = receipt["signature"]
    if not isinstance(signature, str) or not hmac.compare_digest(signature, expected):
        raise ValueError("approval signature verification failed")
    if not (hmac.compare_digest(body["rule_sha256"], rule_sha256(rule))
            and hmac.compare_digest(body["document_sha256"],
                                    _sha256_text(document_sha256, "document_sha256"))
            and hmac.compare_digest(body["tenant_id"], _nonempty(tenant_id, "tenant_id"))
            and hmac.compare_digest(body["legal_entity_id"],
                                    _nonempty(legal_entity_id, "legal_entity_id"))):
        raise ValueError("approval scope, rule or contract document digest mismatch")
    try:
        approved_at = datetime.fromisoformat(body["approved_at"])
    except (TypeError, ValueError) as exc:
        raise ValueError("invalid approval timestamp") from exc
    if approved_at.tzinfo is None or approved_at > datetime.now(timezone.utc):
        raise ValueError("approval timestamp is missing timezone or future-dated")
    return {
        "approval_id": body["approval_id"], "reviewer_id": body["reviewer_id"],
        "source_revision_id": body["source_revision_id"],
        "approved_at": body["approved_at"], "rule_sha256": body["rule_sha256"],
        "document_sha256": body["document_sha256"],
        "approval_integrity": "HMAC_SHA256_VERIFIED",
        "reviewer_identity_externally_authenticated": "NOT_VERIFIED_BY_THIS_MODULE",
        "revocation_status": "NOT_CHECKED",
    }
