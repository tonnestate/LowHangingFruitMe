"""Evidence-linked realization ledger and reversible rate-snapshotted fee PROPOSAL.

Amounts use integer euro-cents. A second, independently authorized finance
actor must attest evidence before it counts. No event creates an invoice,
transfers supplier funds or independently proves a bank payment.
"""
from __future__ import annotations

from hashlib import sha256
import json
import re
from typing import Any
from uuid import uuid4

from ..approval_registry import ApprovalRegistry
from .store import PrivateAuditStore, BundleNotFound
from .uploads import UploadService

MONEY = re.compile(r"^(?:0|[1-9][0-9]{0,10})\.[0-9]{2}$")


class CaseConflict(ValueError):
    pass


def _cents(amount: str) -> int:
    if not isinstance(amount, str) or not MONEY.fullmatch(amount):
        raise ValueError("positive, exact two-decimal EUR amount required")
    whole, cents = amount.split(".")
    n = int(whole) * 100 + int(cents)
    if not 0 < n <= 10**13:
        raise ValueError("amount outside supported range")
    return n


def _eur(cents: int) -> str:
    sign = "-" if cents < 0 else ""
    value = abs(cents)
    return f"{sign}{value // 100}.{value % 100:02d}"


NEW_CASE_FEE_RATE_BPS = 500  # 5%, proposal only; no entitlement to invoice.


def _fee_proposal(cents: int, basis_points: int = NEW_CASE_FEE_RATE_BPS) -> str:
    # Half-up cent rounding on aggregate verified net, not on each event.
    if basis_points not in (300, 500):
        raise ValueError("unrecognized, unapproved fee policy")
    return _eur((max(cents, 0) * basis_points + 5000) // 10000)


def _claim_key(report: dict[str, Any], tenant_id: str,
               legal_entity_id: str) -> str:
    """Single pilot supplier/agreement/period is not billable twice."""
    required = ("supplier_id", "agreement_id", "period_start", "period_end", "currency")
    if any(not report.get(key) for key in required) or report["currency"] != "EUR":
        raise CaseConflict("case lacks an unambiguous EUR contract period")
    reference = [tenant_id, legal_entity_id] + [report[name] for name in required]
    return sha256(json.dumps(reference, separators=(",", ":")).encode()).hexdigest()


class RecoveryLedger:
    def __init__(
        self, *, registry: ApprovalRegistry,
        store: PrivateAuditStore, uploads: UploadService,
    ) -> None:
        self._connect = registry._connect
        self.store = store
        self.uploads = uploads

    def require_finance_grant(
        self, *, tenant_id: str, legal_entity_id: str,
        finance_actor_id: str,
    ) -> None:
        db = self._connect()
        try:
            with db.cursor() as cur:
                cur.execute(
                    """SELECT active FROM lhfm_finance_grants
                       WHERE tenant_id=%s AND legal_entity_id=%s
                         AND finance_actor_id=%s""",
                    (tenant_id, legal_entity_id, finance_actor_id),
                )
                record = cur.fetchone()
            if not record or not record["active"]:
                raise PermissionError("not an active finance verifier")
        finally:
            db.close()

    def _audited(
        self, *, audit_id: str, tenant_id: str,
        legal_entity_id: str, reviewer_id: str,
    ) -> tuple[dict[str, Any], int]:
        audit = self.store.get_run(
            audit_id=audit_id, tenant_id=tenant_id,
            legal_entity_id=legal_entity_id, reviewer_id=reviewer_id,
        )
        report = audit.get("report")
        if (audit["status"] != "COMPLETED" or audit["audit_executed"] is not True
                or not isinstance(report, dict)
                or report.get("status") != "EVIDENCED"
                or not isinstance(report.get("readiness"), dict)
                or report["readiness"].get("audit_admissible") is not True
                or report.get("currency") != "EUR"):
            raise CaseConflict("only an evidentially completed EUR audit can enter recovery")
        cents = _cents(report.get("difference_net"))
        return report, cents

    def record(
        self, *, audit_id: str, tenant_id: str,
        legal_entity_id: str, reviewer_id: str,
        kind: str, amount_net: str, evidence_upload_id: str,
        idempotency_key: str, reverses_event_id: str | None,
    ) -> dict[str, Any]:
        if kind not in ("REALIZATION", "REVERSAL"):
            raise ValueError("unknown recovery event kind")
        if (kind == "REVERSAL") != bool(reverses_event_id):
            raise ValueError("reversal must identify original realized event")
        cents = _cents(amount_net)
        report, difference = self._audited(
            audit_id=audit_id, tenant_id=tenant_id,
            legal_entity_id=legal_entity_id, reviewer_id=reviewer_id,
        )
        with self.uploads.snapshot_clean(
            upload_id=evidence_upload_id, tenant_id=tenant_id,
            legal_entity_id=legal_entity_id, reviewer_id=reviewer_id,
            accepted_kinds=("RECOVERY_PDF",),
        ):
            pass
        claim_hash = _claim_key(report, tenant_id, legal_entity_id)
        signature = sha256(
            json.dumps([audit_id,kind,cents,evidence_upload_id,reverses_event_id],
                       separators=(",", ":")).encode()
        ).hexdigest()
        db=self._connect()
        try:
            with db.cursor() as cur:
                case_id = str(uuid4())
                cur.execute(
                    """INSERT INTO lhfm_recovery_cases
                       (case_id,audit_id,tenant_id,legal_entity_id,reviewer_id,
                        claim_sha256,difference_cents,fee_rate_bps)
                       VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
                       ON DUPLICATE KEY UPDATE case_id=case_id""",
                    (case_id,audit_id,tenant_id,legal_entity_id,
                     reviewer_id,claim_hash,difference,NEW_CASE_FEE_RATE_BPS),
                )
                cur.execute(
                    """SELECT case_id,difference_cents FROM lhfm_recovery_cases
                       WHERE audit_id=%s AND tenant_id=%s AND legal_entity_id=%s
                         AND reviewer_id=%s FOR UPDATE""",
                    (audit_id,tenant_id,legal_entity_id,reviewer_id),
                )
                row = cur.fetchone()
                if not row or row["difference_cents"] != difference:
                    raise CaseConflict("contract period already has a different recovery case")
                case_id=row["case_id"]
                cur.execute(
                    """SELECT directive FROM lhfm_recovery_case_status_events
                       WHERE case_id=%s ORDER BY event_id DESC LIMIT 1""",
                    (case_id,),
                )
                directive=cur.fetchone()
                if directive and directive["directive"]=="CLOSED":
                    raise CaseConflict("closed recovery case requires explicit reopening")
                if kind == "REVERSAL":
                    cur.execute(
                        """SELECT kind,state FROM lhfm_recovery_events
                           WHERE event_id=%s AND case_id=%s""",
                        (reverses_event_id,case_id),
                    )
                    original=cur.fetchone()
                    if not original or original["kind"]!="REALIZATION" or original["state"]!="CONFIRMED":
                        raise CaseConflict("reversal must reference confirmed realization in same case")
                event_id=str(uuid4())
                cur.execute(
                    """INSERT INTO lhfm_recovery_events
                       (event_id,case_id,tenant_id,legal_entity_id,reporter_id,
                        kind,amount_cents,evidence_upload_id,reverses_event_id,
                        request_sha256,idempotency_key,state)
                       VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'REPORTED')
                       ON DUPLICATE KEY UPDATE event_id=event_id""",
                    (event_id,case_id,tenant_id,legal_entity_id,reviewer_id,
                     kind,cents,evidence_upload_id,reverses_event_id,
                     signature,idempotency_key),
                )
                cur.execute(
                    """SELECT event_id,request_sha256,state FROM lhfm_recovery_events
                       WHERE case_id=%s AND idempotency_key=%s FOR UPDATE""",
                    (case_id,idempotency_key),
                )
                existing=cur.fetchone()
                if not existing or existing["request_sha256"]!=signature:
                    raise CaseConflict("recovery event conflict: reuse or duplicate evidence")
            db.commit()
            return {
                "case_id":case_id, "event_id":existing["event_id"],
                "status":existing["state"],"kind":kind,
                "amount_net":_eur(cents), "invoice_created":False,
            }
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    def resolve(
        self, *, event_id: str, tenant_id: str,
        legal_entity_id: str, finance_actor_id: str,
        confirmed: bool,
    ) -> dict[str, Any]:
        """Independent actor assertion, serialized across one recovery case."""
        self.require_finance_grant(
            tenant_id=tenant_id, legal_entity_id=legal_entity_id,
            finance_actor_id=finance_actor_id,
        )
        db=self._connect()
        try:
            with db.cursor() as cur:
                cur.execute(
                    """SELECT case_id FROM lhfm_recovery_events
                       WHERE event_id=%s AND tenant_id=%s AND legal_entity_id=%s""",
                    (event_id,tenant_id,legal_entity_id),
                )
                initial=cur.fetchone()
                if initial is None:
                    raise BundleNotFound("recovery event absent in authenticated scope")
                case_id=initial["case_id"]
                cur.execute(
                    """SELECT difference_cents FROM lhfm_recovery_cases
                       WHERE case_id=%s AND tenant_id=%s AND legal_entity_id=%s
                       FOR UPDATE""",
                    (case_id,tenant_id,legal_entity_id),
                )
                case=cur.fetchone()
                if case is None:
                    raise BundleNotFound("recovery case absent in scope")
                cur.execute(
                    """SELECT event_id,kind,amount_cents,reporter_id,
                              evidence_upload_id,reverses_event_id,state,verified_by
                       FROM lhfm_recovery_events
                       WHERE event_id=%s AND case_id=%s FOR UPDATE""",
                    (event_id,case_id),
                )
                entry=cur.fetchone()
                if entry is None:
                    raise BundleNotFound("recovery event absent")
                if finance_actor_id==entry["reporter_id"]:
                    raise PermissionError("reporter cannot independently confirm own recovery")
                desired="CONFIRMED" if confirmed else "REJECTED"
                if entry["state"]!= "REPORTED":
                    if entry["state"]==desired and entry["verified_by"]==finance_actor_id:
                        db.commit()
                        return {"event_id":event_id,"status":desired,"idempotent":True,
                                "invoice_created":False}
                    raise CaseConflict("cannot change an already reviewed event")
                # Confirm the evidence is still clean, owner-bound and hash-safe.
                # Uploaded PDF itself is NOT proof of a bank transfer.
                with self.uploads.snapshot_clean(
                    upload_id=entry["evidence_upload_id"], tenant_id=tenant_id,
                    legal_entity_id=legal_entity_id, reviewer_id=entry["reporter_id"],
                    accepted_kinds=("RECOVERY_PDF",),
                ):
                    pass
                cur.execute(
                    """SELECT event_id,kind,amount_cents,reverses_event_id
                       FROM lhfm_recovery_events
                       WHERE case_id=%s AND state='CONFIRMED' FOR UPDATE""",
                    (case_id,),
                )
                events=cur.fetchall()
                realized={e["event_id"]:int(e["amount_cents"])
                          for e in events if e["kind"]=="REALIZATION"}
                reversals={}
                for e in events:
                    if e["kind"]=="REVERSAL":
                        target=e["reverses_event_id"]
                        reversals[target]=reversals.get(target,0)+int(e["amount_cents"])
                net=sum(realized.values())-sum(reversals.values())
                amount=int(entry["amount_cents"])
                if confirmed:
                    if entry["kind"]=="REALIZATION":
                        if net+amount>int(case["difference_cents"]):
                            raise CaseConflict("confirmed recovery exceeds audited difference")
                    else:
                        target=entry["reverses_event_id"]
                        if target not in realized or reversals.get(target,0)+amount>realized[target]:
                            raise CaseConflict("reversal exceeds confirmed original realization")
                        if net-amount<0:
                            raise CaseConflict("reversal exceeds remaining net recovery")
                # Recheck independently provisioned grant under the same TX.
                cur.execute(
                    """SELECT active FROM lhfm_finance_grants
                       WHERE tenant_id=%s AND legal_entity_id=%s
                         AND finance_actor_id=%s FOR UPDATE""",
                    (tenant_id,legal_entity_id,finance_actor_id),
                )
                grant=cur.fetchone()
                if not grant or not grant["active"]:
                    raise PermissionError("finance grant revoked during review")
                cur.execute(
                    """UPDATE lhfm_recovery_events SET state=%s,verified_by=%s,
                       verified_at=UTC_TIMESTAMP(6)
                       WHERE event_id=%s AND state='REPORTED'""",
                    (desired,finance_actor_id,event_id),
                )
                if cur.rowcount!=1:
                    raise CaseConflict("concurrent recovery review")
            db.commit()
            return {"event_id":event_id,"status":desired,"idempotent":False,
                    "invoice_created":False}
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    def annotate_status(
        self, *, audit_id: str, tenant_id: str,
        legal_entity_id: str, finance_actor_id: str,
        directive: str, reason: str,
    ) -> dict[str, Any]:
        """Append a finance-attested dispute/closure/reopen event; never mutate money."""
        if directive not in ("DISPUTED", "CLOSED", "OPEN"):
            raise ValueError("unknown recovery status directive")
        if not isinstance(reason, str) or not reason.strip() or len(reason) > 200:
            raise ValueError("a concise documented reason is required")
        self.require_finance_grant(
            tenant_id=tenant_id, legal_entity_id=legal_entity_id,
            finance_actor_id=finance_actor_id,
        )
        db=self._connect()
        try:
            with db.cursor() as cur:
                cur.execute(
                    """SELECT case_id FROM lhfm_recovery_cases
                       WHERE audit_id=%s AND tenant_id=%s AND legal_entity_id=%s
                       FOR UPDATE""",
                    (audit_id,tenant_id,legal_entity_id),
                )
                found=cur.fetchone()
                if found is None:
                    raise BundleNotFound("no recovery case exists in this scope")
                case_id=found["case_id"]
                if directive=="CLOSED":
                    cur.execute(
                        """SELECT COUNT(*) AS pending FROM lhfm_recovery_events
                           WHERE case_id=%s AND state='REPORTED'""",
                        (case_id,),
                    )
                    if int(cur.fetchone()["pending"])>0:
                        raise CaseConflict("cannot close with unreviewed recovery evidence")
                cur.execute(
                    """SELECT active FROM lhfm_finance_grants
                       WHERE tenant_id=%s AND legal_entity_id=%s
                         AND finance_actor_id=%s FOR UPDATE""",
                    (tenant_id,legal_entity_id,finance_actor_id),
                )
                grant=cur.fetchone()
                if not grant or not grant["active"]:
                    raise PermissionError("finance permission revoked during transition")
                cur.execute(
                    """INSERT INTO lhfm_recovery_case_status_events
                       (case_id,tenant_id,legal_entity_id,finance_actor_id,
                        directive,reason)
                       VALUES (%s,%s,%s,%s,%s,%s)""",
                    (case_id,tenant_id,legal_entity_id,
                     finance_actor_id,directive,reason.strip()),
                )
            db.commit()
            return {"audit_id":audit_id,"case_id":case_id,
                    "directive":directive,"status_event_recorded":True,
                    "invoice_created":False}
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    def ledger(
        self, *, audit_id: str, tenant_id: str,
        legal_entity_id: str, reviewer_id: str,
    ) -> dict[str, Any]:
        report,difference=self._audited(
            audit_id=audit_id, tenant_id=tenant_id,
            legal_entity_id=legal_entity_id, reviewer_id=reviewer_id,
        )
        db=self._connect()
        try:
            with db.cursor() as cur:
                cur.execute(
                    ""SELECT case_id,fee_rate_bps FROM lhfm_recovery_cases
                       WHERE audit_id=%s AND tenant_id=%s AND legal_entity_id=%s
                         AND reviewer_id=%s""",
                    (audit_id,tenant_id,legal_entity_id,reviewer_id),
                )
                case=cur.fetchone()
                rows=[]
                annotation=None
                if case:
                    cur.execute(
                        """SELECT directive,reason,finance_actor_id,recorded_at
                           FROM lhfm_recovery_case_status_events
                           WHERE case_id=%s ORDER BY event_id DESC LIMIT 1""",
                        (case["case_id"],),
                    )
                    annotation=cur.fetchone()
                    cur.execute(
                        """SELECT event_id,kind,amount_cents,evidence_upload_id,
                                  reverses_event_id,state,verified_by
                           FROM lhfm_recovery_events
                           WHERE case_id=%s ORDER BY created_at,event_id""",
                        (case["case_id"],),
                    )
                    rows=cur.fetchall()
        finally:
            db.close()
        realized=sum(int(e["amount_cents"]) for e in rows
                     if e["state"]=="CONFIRMED" and e["kind"]=="REALIZATION")
        reversals=sum(int(e["amount_cents"]) for e in rows
                      if e["state"]=="CONFIRMED" and e["kind"]=="REVERSAL")
        net=realized-reversals
        status=("NONE" if case is None else
                "REALIZED_FULL" if net==difference else
                "REALIZED_PARTIAL" if net>0 else "CLAIMED")
        if annotation and annotation["directive"] in ("DISPUTED","CLOSED"):
            status=annotation["directive"]
        if net<0 or net>difference:
            raise CaseConflict("ledger invariants violated, manual reconciliation required")
        return {
            "audit_id":audit_id,"case_id":case["case_id"] if case else None,
            "case_status":status,
            "case_status_reviewed_by":annotation["finance_actor_id"] if annotation else None,
            "case_status_reason":annotation["reason"] if annotation else None,
            "calculated_variance_net":_eur(difference),
            "billable_recovery_net":"0.00",
            "audited_difference_net":_eur(difference),
            "confirmed_realization_net":_eur(net),
            "fee_rate":f"0.{(int(case['fee_rate_bps']) if case else NEW_CASE_FEE_RATE_BPS) // 100:02d}",
            "fee_proposal_net":_fee_proposal(net, int(case['fee_rate_bps']) if case else NEW_CASE_FEE_RATE_BPS),
            "fee_due_net":"0.00",
            "invoice_created":False,
            "billing_authorized":False,
            "finance_evidence_status":"independent_role_attestation_not_bank_verification",
            "unreviewed_event_count":sum(e["state"]=="REPORTED" for e in rows),
            "events":[{
                "event_id":e["event_id"],"kind":e["kind"],
                "amount_net":_eur(int(e["amount_cents"])),
                "evidence_upload_id":e["evidence_upload_id"],
                "reverses_event_id":e["reverses_event_id"],
                "state":e["state"],"verified_by":e["verified_by"],
            } for e in rows],
        }
