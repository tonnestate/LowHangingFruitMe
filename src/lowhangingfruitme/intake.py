"""Strict, source-traceable CSV imports for the deterministic rebate kernel.

Frictionless is mandatory for validation and is an optional package dependency.
No column guessing, no implicit completeness claims, and no model-based repairs.
"""
from __future__ import annotations

import csv
from hashlib import sha256
import json
from pathlib import Path
from typing import Any, Callable

from .rebate import Entry, BonusRule, audit
from .readiness import assess_readiness
from .approval_registry import ApprovalRegistry

MAX_CSV_BYTES = 10 * 1024 * 1024
MAX_ROWS = 100_000

COLUMNS = {
    "transactions": (
        "external_id", "supplier_id", "date", "currency",
        "amount_net", "kind", "posted", "basis",
    ),
    "settlements": (
        "external_id", "supplier_id", "date", "currency",
        "amount_net", "kind", "posted", "agreement_id",
        "period_start", "period_end",
    ),
}


def _file(path: str | Path, suffix: str, limit: int) -> tuple[Path, str]:
    path = Path(path)
    if path.is_symlink() or not path.is_file() or path.suffix.lower() != suffix:
        raise ValueError(f"expected a regular local {suffix} file, not a symlink")
    size = path.stat().st_size
    if not 0 < size <= limit:
        raise ValueError(f"{suffix} size must be between 1 and {limit} bytes")
    return path, sha256(path.read_bytes()).hexdigest()


def _validate_with_frictionless(path: Path, fields: tuple[str, ...]) -> None:
    try:
        from frictionless import Resource, Schema
    except ImportError as exc:
        raise RuntimeError(
            "Frictionless validation is required: install lowhangingfruitme[import]"
        ) from exc
    # Metadata/shape validation is provided by the real Frictionless library.
    # Business-typed values are *also* verified by Entry.load below.
    schema = Schema.from_descriptor({"fields": [{"name": name, "type": "string"} for name in fields]})
    try:
        resource = Resource(path=path.name, basepath=str(path.parent), schema=schema, encoding="utf-8-sig")
        report = resource.validate(limit_errors=20)
    except Exception as exc:
        raise ValueError(f"frictionless could not validate {path.name}: {exc}") from exc
    if not report.valid:
        errors = report.flatten(["code", "message"])
        raise ValueError(f"frictionless validation failed: {errors[:20]}")


def import_csv(
    path: str | Path, dataset: str, *,
    source_system: str,
) -> dict[str, Any]:
    """Import a canonical UTF-8 CSV with exact schema and row provenance.

    This is a local data-adapter, NOT a public upload endpoint. Upstream upload
    scanning, isolation, tenant permissions and retention are still required.
    """
    if dataset not in COLUMNS:
        raise ValueError("dataset must be transactions or settlements")
    if not isinstance(source_system, str) or not source_system.strip():
        raise ValueError("source_system is required")
    path, digest = _file(path, ".csv", MAX_CSV_BYTES)
    fields = COLUMNS[dataset]
    with path.open("r", encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source, strict=True)
        headers = reader.fieldnames
        if headers is None or len(headers) != len(set(headers)):
            raise ValueError("missing or duplicate CSV headers")
        if tuple(headers) != fields:
            raise ValueError(
                f"canonical CSV header mismatch: expected {', '.join(fields)}"
            )
        # Fail-closed on any missing, duplicate, malformed, or unexpected value.
        _validate_with_frictionless(path, fields)
        entries: list[dict[str, Any]] = []
        seen: dict[tuple[str, str], dict[str, Any]] = {}
        for row in reader:
            if len(entries) >= MAX_ROWS:
                raise ValueError("CSV row limit exceeded")
            if None in row or any(value is None for value in row.values()):
                raise ValueError(f"malformed row at source line {reader.line_num}")
            line_no = reader.line_num
            entry: dict[str, Any] = {
                "source_system": source_system.strip(),
                "evidence_refs": [f"sha256:{digest}#row={line_no}"],
            }
            for field in fields:
                value = row[field].strip()
                if field == "posted":
                    if value.lower() not in ("true", "false"):
                        raise ValueError(f"line {line_no}: posted must be true/false")
                    entry[field] = value.lower() == "true"
                elif field in ("agreement_id", "period_start", "period_end") and not value:
                    entry[field] = None
                else:
                    if not value:
                        raise ValueError(f"line {line_no}: {field} is empty")
                    entry[field] = value
            # Reuse the canonical kernel's strict typing, sign and date checks.
            try:
                Entry.load(entry, settlement=(dataset == "settlements"))
            except (ValueError, KeyError) as exc:
                raise ValueError(f"line {line_no}: {exc}") from exc
            identity = (entry["source_system"], entry["external_id"])
            if identity in seen:
                raise ValueError(
                    f"duplicate external identity {identity} in {dataset}; "
                    "resolve duplicates before importing"
                )
            seen[identity] = entry
            entries.append(entry)
    if dataset == "transactions" and not entries:
        raise ValueError("transaction dataset cannot be empty")
    return {
        "dataset": dataset,
        "file_sha256": digest,
        "source_system": source_system.strip(),
        "validation": "frictionless+kernel",
        "row_count": len(entries),
        "entries": entries,
    }


def audit_from_csv(
    rule_path: str | Path, transactions_path: str | Path,
    settlements_path: str | Path, *, source_system: str,
    completeness: dict[str, bool], controls: dict[str, Any] | None = None,
    approval_receipt: dict[str, Any] | None = None,
    approval_key: bytes | None = None,
    approval_scope: dict[str, str] | None = None,
    contract_source_path: str | Path | None = None,
    approval_registry: ApprovalRegistry | None = None,
    approval_actor_id: str | None = None,
    reauthorize_before_dispatch: Callable[[], None] | None = None,
) -> dict[str, Any]:
    """End-to-end local CSV -> validated dataset -> existing audit() function.

    The operator must supply independently justified completeness assertions;
    no flag is silently set to True based on successful parsing.
    """
    rule_path, rule_digest = _file(rule_path, ".json", 1024 * 1024)
    try:
        rule = json.loads(rule_path.read_text(encoding="utf-8"))
    except (ValueError, UnicodeError) as exc:
        raise ValueError("invalid UTF-8 JSON rule") from exc
    if not isinstance(rule, dict):
        raise ValueError("rule must be an object")
    BonusRule.load(rule)
    if type(completeness) is not dict or set(completeness) != {
        "transactions_complete", "settlements_complete", "agreements_complete"
    } or any(type(v) is not bool for v in completeness.values()):
        raise ValueError("three explicit boolean completeness assertions required")
    txns = import_csv(transactions_path, "transactions", source_system=source_system)
    settlements = import_csv(settlements_path, "settlements", source_system=source_system)
    payload = {
        "rule": rule,
        "transactions": txns["entries"],
        "settlements": settlements["entries"],
        "completeness": completeness,
    }
    document_sha256 = None
    if contract_source_path is not None:
        contract_source_path = Path(contract_source_path)
        if contract_source_path.is_symlink() or not contract_source_path.is_file():
            raise ValueError("contract source must be a regular local file, not a symlink")
        if not 0 < contract_source_path.stat().st_size <= 20 * 1024 * 1024:
            raise ValueError("contract source must be nonempty and <=20MB")
        document_sha256 = sha256(contract_source_path.read_bytes()).hexdigest()
    readiness = assess_readiness(
        payload["rule"], payload["transactions"], payload["settlements"],
        payload["completeness"], controls,
        approval_receipt=approval_receipt, approval_key=approval_key,
        approval_scope=approval_scope, document_sha256=document_sha256,
    )
    if approval_registry is None and readiness["audit_admissible"]:
        # A cryptographically valid receipt alone may be stale, revoked or
        # not registered. No registry = no final calculation, even in CLI.
        readiness["status"] = "LIMITED"
        readiness["audit_admissible"] = False
        readiness["issues"].append({
            "code": "APPROVAL_REGISTRY_UNAVAILABLE",
            "field": "approval_registry",
            "severity": "WARNING",
            "explanation": "Persistent approval/revocation verification is unavailable",
        })
    if not readiness["audit_admissible"]:
        # This is a pre-audit diagnostics result, never a money finding.
        return {
            "status": "REVIEW_REQUIRED" if readiness["status"] == "LIMITED" else "NOT_CALCULABLE",
            "audit_executed": False, "readiness": readiness,
            "difference_net": None, "expected_bonus_net": None, "recorded_bonus_net": None,
            "billable_recovery_net": "0.00", "fee_due_net": "0.00",
            "warnings": [issue["code"] for issue in readiness["issues"]],
            "imports": [{k: v for k, v in item.items() if k != "entries"}
                        for item in (txns, settlements)],
            "rule_file_sha256": rule_digest,
            "completeness_source": "operator_assertion_not_independently_verified",
        }
    # This is the DISPATCH boundary: repeat signature+source+scope checks
    # and lock the registry row across the calculation. Revoke/disable cannot
    # commit in another process while the protected calculation is running.
    assert approval_registry is not None
    assert approval_receipt is not None and approval_key is not None
    assert approval_scope is not None and document_sha256 is not None
    try:
        with approval_registry.guard(
            approval_receipt, rule=rule, key=approval_key,
            document_sha256=document_sha256,
            tenant_id=approval_scope["tenant_id"],
            legal_entity_id=approval_scope["legal_entity_id"],
            acting_reviewer_id=approval_actor_id,
        ) as dispatch_approval:
            if reauthorize_before_dispatch is not None:
                reauthorize_before_dispatch()
            result = audit(payload)
    except (PermissionError, ValueError) as exc:
        readiness["status"] = "NOT_READY"
        readiness["audit_admissible"] = False
        readiness["issues"].append({
            "code": "APPROVAL_NOT_ACTIVE_AT_DISPATCH",
            "field": "approval_registry", "severity": "BLOCKER",
            "explanation": str(exc),
        })
        return {
            "status": "NOT_CALCULABLE", "audit_executed": False,
            "readiness": readiness,
            "difference_net": None, "expected_bonus_net": None,
            "recorded_bonus_net": None, "billable_recovery_net": "0.00",
            "fee_due_net": "0.00",
            "warnings": [item["code"] for item in readiness["issues"]],
            "imports": [{k: v for k, v in item.items() if k != "entries"}
                        for item in (txns, settlements)],
            "rule_file_sha256": rule_digest,
            "completeness_source": "operator_assertion_not_independently_verified",
        }
    # Verified registry status at dispatch, not just a signed local receipt.
    readiness["approval_verification"] = dispatch_approval
    result["warnings"] = [w for w in result["warnings"] if w != "UNVERIFIED_APPROVAL_CONTEXT"]
    if result["status"] == "REVIEW_REQUIRED" and not result["warnings"]:
        result["status"] = "EVIDENCED"
    result["audit_executed"] = True
    result["approval_verification"] = readiness["approval_verification"]
    result["readiness"] = readiness
    result["imports"] = [
        {k: v for k, v in item.items() if k != "entries"}
        for item in (txns, settlements)
    ]
    result["rule_file_sha256"] = rule_digest
    result["completeness_source"] = "operator_assertion_not_independently_verified"
    return result
