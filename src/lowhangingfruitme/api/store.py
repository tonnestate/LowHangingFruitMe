"""MariaDB persistence and private snapshot handling for bounded audit API.

Operator-provisioned bundles are NOT customer uploads. The HTTP layer accepts
only opaque bundle UUIDs. All file paths are stored server-side, validated as
non-symlink members of one private root and copied into a fresh private snapshot
before the existing deterministic audited calculation.
"""
from __future__ import annotations

from contextlib import contextmanager
from hashlib import sha256
import json
from pathlib import Path
import re
import shutil
import tempfile
from typing import Any, Iterator
from uuid import uuid4

from ..approval_registry import ApprovalRegistry


ROLES = ("rule", "transactions", "settlements", "contract")
SUFFIX = {"rule": ".json", "transactions": ".csv",
          "settlements": ".csv", "contract": ".txt"}
MAX_BYTES = {"rule": 1024 * 1024, "transactions": 16 * 1024 * 1024,
             "settlements": 16 * 1024 * 1024, "contract": 20 * 1024 * 1024}
IDENTIFIER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
HEX_SHA256 = re.compile(r"^[a-f0-9]{64}$")


class BundleNotFound(LookupError):
    pass


class RunConflict(ValueError):
    pass


class PrivateAuditStore:
    """Uses the existing dedicated MariaDB connection factory, no new DB."""

    def __init__(self, *, registry: ApprovalRegistry, source_root: str | Path) -> None:
        self._connect = registry._connect
        self.root = Path(source_root).resolve(strict=True)
        if not self.root.is_dir():
            raise ValueError("private source root must be an existing directory")

    def _private_path(self, relative: str) -> Path:
        # No direct HTTP route may call this with a user-provided path.
        if not isinstance(relative, str) or len(relative) > 200 or not relative:
            raise ValueError("invalid private source path")
        rel = Path(relative)
        if rel.is_absolute() or any(p in ("..", ".", "") for p in rel.parts):
            raise ValueError("source path escapes private root")
        check = self.root
        for part in rel.parts:
            check = check / part
            if check.is_symlink():
                raise ValueError("symlink not allowed in source path")
        path = check.resolve(strict=True)
        try:
            path.relative_to(self.root)
        except ValueError as exc:
            raise ValueError("source path escapes private root") from exc
        if not path.is_file():
            raise ValueError("source path must reference a regular private file")
        return path

    def _checked_copy(self, *, relative: str, expected_hash: str,
                      dest: Path, role: str) -> None:
        if not isinstance(expected_hash, str) or not HEX_SHA256.fullmatch(expected_hash):
            raise ValueError("invalid source content hash")
        path = self._private_path(relative)
        if path.suffix.lower() != SUFFIX[role]:
            raise ValueError("invalid source suffix for " + role)
        size = path.stat().st_size
        if not 0 < size <= MAX_BYTES[role]:
            raise ValueError("source file outside allowed size")
        digest = sha256()
        with path.open("rb") as source, dest.open("xb") as out:
            while chunk := source.read(65536):
                digest.update(chunk)
                out.write(chunk)
                if out.tell() > MAX_BYTES[role]:
                    raise ValueError("source grew beyond allowed size")
        if digest.hexdigest() != expected_hash:
            raise ValueError("operator-provisioned source changed since registration")

    @staticmethod
    def _validated_manifest(manifest: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(manifest, dict) or set(manifest) != {
            "files", "source_system", "controls", "completeness", "approval_receipt"
        }:
            raise ValueError("complete server-owned manifest required")
        files = manifest["files"]
        if not isinstance(files, dict) or set(files) != set(ROLES):
            raise ValueError("four source file references required")
        for role in ROLES:
            ref = files[role]
            if not isinstance(ref, dict) or set(ref) != {"path", "sha256"}:
                raise ValueError("source file entry needs path and SHA256")
            if not isinstance(ref["path"], str) or not isinstance(ref["sha256"], str):
                raise ValueError("invalid source descriptor")
        if not isinstance(manifest["source_system"], str) or not IDENTIFIER.fullmatch(manifest["source_system"]):
            raise ValueError("invalid source system")
        if not isinstance(manifest["controls"], dict) or not isinstance(manifest["approval_receipt"], dict):
            raise ValueError("controls and signed receipt must be objects")
        if (type(manifest["completeness"]) is not dict
                or set(manifest["completeness"]) != {
                    "transactions_complete", "settlements_complete", "agreements_complete"
                } or any(type(v) is not bool for v in manifest["completeness"].values())):
            raise ValueError("exact explicit completeness assertions required")
        if len(json.dumps(manifest, ensure_ascii=False)) > 65536:
            raise ValueError("source manifest too large")
        return manifest

    def provision_bundle(self, *, bundle_id: str, tenant_id: str,
                         legal_entity_id: str, manifest: dict[str, Any]) -> None:
        """TRUSTED OPERATOR ONLY. Not exposed via HTTP to customers."""
        self._validated_manifest(manifest)
        for role, ref in manifest["files"].items():
            path = self._private_path(ref["path"])
            if path.suffix.lower() != SUFFIX[role]:
                raise ValueError("invalid source format")
            if not HEX_SHA256.fullmatch(ref["sha256"]):
                raise ValueError("invalid source SHA-256")
            if not 0 < path.stat().st_size <= MAX_BYTES[role]:
                raise ValueError("source too large")
            if sha256(path.read_bytes()).hexdigest() != ref["sha256"]:
                raise ValueError("operator source SHA mismatch")
        if str(manifest["approval_receipt"].get("tenant_id")) != tenant_id:
            raise ValueError("approval tenant mismatch")
        if str(manifest["approval_receipt"].get("legal_entity_id")) != legal_entity_id:
            raise ValueError("approval legal entity mismatch")
        connection = self._connect()
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    """INSERT INTO lhfm_api_bundles
                    (bundle_id, tenant_id, legal_entity_id, manifest_json)
                    VALUES (%s,%s,%s,%s)""",
                    (bundle_id, tenant_id, legal_entity_id,
                     json.dumps(manifest, sort_keys=True, ensure_ascii=False)),
                )
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def load_bundle(self, *, bundle_id: str, tenant_id: str,
                    legal_entity_id: str, reviewer_id: str) -> dict[str, Any]:
        connection = self._connect()
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    """SELECT manifest_json FROM lhfm_api_bundles
                       WHERE bundle_id=%s AND tenant_id=%s AND legal_entity_id=%s""",
                    (bundle_id, tenant_id, legal_entity_id),
                )
                row = cursor.fetchone()
            if not row:
                raise BundleNotFound("source bundle not present in authorized scope")
            manifest = self._validated_manifest(json.loads(row["manifest_json"]))
            if manifest["approval_receipt"].get("reviewer_id") != reviewer_id:
                raise PermissionError("signed approval belongs to a different reviewer")
            return manifest
        finally:
            connection.close()

    @contextmanager
    def snapshot(self, manifest: dict[str, Any]) -> Iterator[dict[str, Path]]:
        self._validated_manifest(manifest)
        with tempfile.TemporaryDirectory(prefix="lhfm-audit-snapshot-") as tmp:
            copied: dict[str, Path] = {}
            for role in ROLES:
                item = manifest["files"][role]
                dst = Path(tmp) / (role + SUFFIX[role])
                self._checked_copy(
                    relative=item["path"], expected_hash=item["sha256"],
                    dest=dst, role=role,
                )
                copied[role] = dst
            yield copied

    def reserve_run(self, *, tenant_id: str, legal_entity_id: str,
                    reviewer_id: str, bundle_id: str,
                    idempotency_key: str) -> tuple[dict[str, Any], bool]:
        signature = sha256(
            json.dumps([tenant_id, legal_entity_id, reviewer_id, bundle_id],
                       separators=(",", ":")).encode()
        ).hexdigest()
        connection = self._connect()
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    """SELECT audit_id, request_sha256, status, audit_executed
                       FROM lhfm_api_runs WHERE tenant_id=%s AND
                       legal_entity_id=%s AND reviewer_id=%s AND idempotency_key=%s
                       FOR UPDATE""",
                    (tenant_id, legal_entity_id, reviewer_id, idempotency_key),
                )
                existing = cursor.fetchone()
                if existing:
                    if existing["request_sha256"] != signature:
                        raise RunConflict("idempotency key reused with different bundle")
                    connection.commit()
                    return existing, False
                audit_id = str(uuid4())
                cursor.execute(
                    """INSERT INTO lhfm_api_runs
                       (audit_id, tenant_id, legal_entity_id, reviewer_id, bundle_id,
                        idempotency_key, request_sha256, status, audit_executed)
                       VALUES (%s,%s,%s,%s,%s,%s,%s,'PROCESSING',0)""",
                    (audit_id, tenant_id, legal_entity_id, reviewer_id,
                     bundle_id, idempotency_key, signature),
                )
            connection.commit()
            return {"audit_id": audit_id, "status": "PROCESSING", "audit_executed": False}, True
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def finish_run(self, *, audit_id: str, report: dict[str, Any]) -> None:
        state = "COMPLETED" if report.get("audit_executed") is True else "NEEDS_REVIEW"
        connection = self._connect()
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    """UPDATE lhfm_api_runs SET status=%s, audit_executed=%s,
                       report_json=%s, finished_at=UTC_TIMESTAMP(6)
                       WHERE audit_id=%s AND status='PROCESSING'""",
                    (state, bool(report.get("audit_executed")),
                     json.dumps(report, sort_keys=True, ensure_ascii=False), audit_id),
                )
                if cursor.rowcount != 1:
                    raise RunConflict("audit run state changed unexpectedly")
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def fail_run(self, *, audit_id: str) -> None:
        # Error details must not leak source paths or customer financial data.
        connection = self._connect()
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    """UPDATE lhfm_api_runs SET status='FAILED',
                       finished_at=UTC_TIMESTAMP(6)
                       WHERE audit_id=%s AND status='PROCESSING'""",
                    (audit_id,),
                )
            connection.commit()
        finally:
            connection.close()

    def get_run(self, *, audit_id: str, tenant_id: str,
                legal_entity_id: str, reviewer_id: str) -> dict[str, Any]:
        connection = self._connect()
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    """SELECT audit_id, status, audit_executed, report_json
                       FROM lhfm_api_runs
                       WHERE audit_id=%s AND tenant_id=%s AND legal_entity_id=%s
                         AND reviewer_id=%s""",
                    (audit_id, tenant_id, legal_entity_id, reviewer_id),
                )
                row = cursor.fetchone()
            if not row:
                raise BundleNotFound("audit run not present in authorized scope")
            return {
                "audit_id": row["audit_id"],
                "status": row["status"],
                "audit_executed": bool(row["audit_executed"]),
                "report": json.loads(row["report_json"]) if row["report_json"] else None,
            }
        finally:
            connection.close()
