"""Fail-closed operator reconciliation for abandoned financial audit reservations.

A running worker may outlive an HTTP request. Time alone therefore NEVER
authorizes interruption; a separately verified full worker stop is mandatory.
This command does not retry work, purge evidence or change idempotency keys.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from typing import Any, Callable, Mapping
from uuid import UUID

from .approval_registry import ApprovalRegistry
from .schema import require_operational_schema

MINIMUM_AGE_SECONDS = 3600
SCOPE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
INCIDENT = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:/-]{0,199}$")


class AuditReconciliationBlocked(RuntimeError):
    """Stop on a missing review, ambiguous state or changed reservation."""


def reconcile_abandoned_audit(
    *, connect: Callable[[], Any], audit_id: str, tenant_id: str,
    legal_entity_id: str, operator_id: str, incident_ref: str,
    apply: bool = False, approvals: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """Explicit single-run change PROCESSING -> FAILED under row lock.

    A new audit requires an entirely new idempotency key, and independent
    renewed source/contract review. The original key forever identifies the
    interrupted reservation. No automatic re-dispatch is possible.
    """
    try:
        if str(UUID(audit_id)) != audit_id:
            raise ValueError("noncanonical UUID")
    except (ValueError, TypeError, AttributeError) as exc:
        raise AuditReconciliationBlocked("invalid canonical audit ID") from exc
    if any(not isinstance(v, str) or not SCOPE.fullmatch(v)
           for v in (tenant_id, legal_entity_id, operator_id)):
        raise AuditReconciliationBlocked("invalid scope or operator identity")
    if not isinstance(incident_ref, str) or not INCIDENT.fullmatch(incident_ref):
        raise AuditReconciliationBlocked("external incident reference is required")
    env = os.environ if approvals is None else approvals
    if apply and (
        env.get("LHFM_AUDIT_RECONCILIATION_APPROVED") != "YES"
        or env.get("LHFM_AUDIT_WORKERS_STOPPED") != "YES"
    ):
        raise AuditReconciliationBlocked(
            "operator approval and verified stop of all audit workers required"
        )
    db = connect()
    try:
        with db.cursor() as cur:
            sql = (
                "SELECT status,audit_executed,report_json,finished_at,"
                " TIMESTAMPDIFF(SECOND,started_at,UTC_TIMESTAMP(6)) AS elapsed_seconds"
                " FROM lhfm_api_runs WHERE audit_id=%s AND tenant_id=%s"
                " AND legal_entity_id=%s"
            )
            if apply:
                sql += " FOR UPDATE"
            cur.execute(sql, (audit_id, tenant_id, legal_entity_id))
            row = cur.fetchone()
            if not row:
                raise AuditReconciliationBlocked("audit not found in exact scope")
            if (row["status"] != "PROCESSING" or row["finished_at"] is not None
                    or row["report_json"] is not None or bool(row["audit_executed"])):
                raise AuditReconciliationBlocked(
                    "only unfinished PROCESSING without any financial report is eligible"
                )
            elapsed = row["elapsed_seconds"]
            if elapsed is None or int(elapsed) < 0:
                raise AuditReconciliationBlocked("invalid audit reservation timestamp")
            eligible = int(elapsed) >= MINIMUM_AGE_SECONDS
            if apply:
                if not eligible:
                    raise AuditReconciliationBlocked("audit reservation is too recent")
                cur.execute(
                    "UPDATE lhfm_api_runs SET status='FAILED',"
                    " finished_at=UTC_TIMESTAMP(6)"
                    " WHERE audit_id=%s AND tenant_id=%s AND legal_entity_id=%s"
                    " AND status='PROCESSING' AND report_json IS NULL"
                    " AND finished_at IS NULL AND audit_executed=0"
                    " AND started_at<=DATE_SUB(UTC_TIMESTAMP(6),INTERVAL 60 MINUTE)",
                    (audit_id, tenant_id, legal_entity_id),
                )
                if cur.rowcount != 1:
                    raise AuditReconciliationBlocked("audit state changed concurrently")
                cur.execute(
                    "INSERT INTO lhfm_audit_reconciliation_events"
                    " (audit_id,tenant_id,legal_entity_id,operator_id,incident_ref,"
                    " prior_state) VALUES (%s,%s,%s,%s,%s,'PROCESSING')",
                    (audit_id, tenant_id, legal_entity_id, operator_id, incident_ref),
                )
                db.commit()
            else:
                db.rollback()
            return {
                "mode": "applied" if apply else "dry_run",
                "audit_id": audit_id,
                "eligible_after_worker_shutdown": eligible,
                "resulting_state": "FAILED" if apply else "PROCESSING",
                "financial_report_modified": False,
                "idempotency_key_reusable": False,
                "retry_automatic": False,
            }
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Offline reconciliation of ONE abandoned audit (dry run by default)"
    )
    parser.add_argument("--audit-id", required=True)
    parser.add_argument("--tenant-id", required=True)
    parser.add_argument("--legal-entity-id", required=True)
    parser.add_argument("--operator-id", required=True)
    parser.add_argument("--incident-ref", required=True)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    try:
        if (os.geteuid() == 0
                or os.environ.get("LHFM_DB_HOST") != "127.0.0.1"
                or os.environ.get("LHFM_DB_USER", "").lower()
                   in ("root", "admin", "mysql")
                or os.environ.get("LHFM_DB_NAME", "").startswith("lhfm_restore_")):
            raise AuditReconciliationBlocked(
                "unprivileged operator and dedicated loopback database required"
            )
        if args.apply and (
            os.environ.get("LHFM_AUDIT_RECONCILIATION_APPROVED") != "YES"
            or os.environ.get("LHFM_AUDIT_WORKERS_STOPPED") != "YES"
        ):
            raise AuditReconciliationBlocked("maintenance authorization required")
        registry = ApprovalRegistry.from_environment()
        require_operational_schema(registry._connect)
        result = reconcile_abandoned_audit(
            connect=registry._connect, audit_id=args.audit_id,
            tenant_id=args.tenant_id, legal_entity_id=args.legal_entity_id,
            operator_id=args.operator_id, incident_ref=args.incident_ref,
            apply=args.apply,
        )
    except Exception:
        print("LHFM_AUDIT_RECONCILIATION_BLOCKED", file=sys.stderr)
        return 2
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
