"""Two-person billing handoff from confirmed evidence; never auto-invoice.

The service prepares a bound, immutable fee evidence packet, not a demand for
payment. A separate authorized billing actor may release the exact still-current
snapshot to an external invoice issuer. Later reversals mark the release STALE,
requiring documented manual credit-note reconciliation before a new release.
No user-provided flag can replace out-of-band customer acceptance/legal review.
"""
from __future__ import annotations

from hashlib import sha256
import json
import re
from typing import Any, Callable
from uuid import uuid4

from .recovery import CaseConflict, _eur
from .store import BundleNotFound

_HEX64 = re.compile(r"^[0-9a-f]{64}$")


def _digest(value: Any) -> str:
    return sha256(json.dumps(value,sort_keys=True,separators=(",",":"),
                             ensure_ascii=False,allow_nan=False).encode()).hexdigest()


def _proposal_cents(amount: int, rate: int) -> int:
    if rate not in (300,500) or amount < 0:
        raise CaseConflict("unrecognized billing rate or negative realization")
    return (amount * rate + 5000)//10000


class BillingHandoffService:
    def __init__(self, *, connect: Callable[[],Any]) -> None:
        self._connect=connect

    @staticmethod
    def _grant(cur: Any, *, tenant_id: str, legal_entity_id: str,
               actor_id: str) -> None:
        cur.execute(
            """SELECT active FROM lhfm_billing_grants
               WHERE tenant_id=%s AND legal_entity_id=%s AND billing_actor_id=%s
               FOR UPDATE""",
            (tenant_id,legal_entity_id,actor_id),
        )
        grant=cur.fetchone()
        if not grant or not grant["active"]:
            raise PermissionError("active independent billing grant required")

    @staticmethod
    def _case(cur: Any, *, audit_id: str, tenant_id: str,
              legal_entity_id: str) -> dict[str,Any]:
        cur.execute(
            """SELECT c.case_id,c.difference_cents,c.fee_rate_bps,
                      r.status,r.audit_executed,r.report_json
               FROM lhfm_recovery_cases c
               JOIN lhfm_api_runs r ON r.audit_id=c.audit_id
               WHERE c.audit_id=%s AND c.tenant_id=%s AND c.legal_entity_id=%s
               FOR UPDATE""",
            (audit_id,tenant_id,legal_entity_id),
        )
        row=cur.fetchone()
        if not row:
            raise BundleNotFound("no matching recovery case")
        if row["status"]!="COMPLETED" or row["audit_executed"]!=1:
            raise CaseConflict("underlying audit is not completed")
        report=json.loads(row["report_json"])
        if (report.get("status")!="EVIDENCED"
                or report.get("currency")!="EUR"
                or not report.get("readiness",{}).get("audit_admissible")
                or not report.get("agreement_id")):
            raise CaseConflict("audited agreement not independently evidenced")
        row["agreement_id"]=report["agreement_id"]
        return row

    @staticmethod
    def _terms(cur: Any, *, tenant_id: str,legal_entity_id: str,
               agreement_id: str, fee_rate_bps: int) -> dict[str,Any]:
        cur.execute(
            """SELECT accepted_terms_sha256,acceptance_evidence_ref,
                      legal_clearance_sha256,legal_clearance_ref,
                      fee_rate_bps,active,verified_by
               FROM lhfm_commercial_terms
               WHERE tenant_id=%s AND legal_entity_id=%s AND agreement_id=%s
               FOR UPDATE""",
            (tenant_id,legal_entity_id,agreement_id),
        )
        row=cur.fetchone()
        if not row or not row["active"]:
            raise CaseConflict("customer-accepted and legally cleared fee terms unavailable")
        if int(row["fee_rate_bps"])!=fee_rate_bps:
            raise CaseConflict("commercial terms rate differs from locked case rate")
        if (not _HEX64.fullmatch(row["accepted_terms_sha256"])
                or not _HEX64.fullmatch(row["legal_clearance_sha256"])
                or not all(isinstance(row[x],str) and row[x].strip() for x in
                           ("acceptance_evidence_ref","legal_clearance_ref","verified_by"))):
            raise CaseConflict("commercial terms provenance is incomplete")
        return row

    @staticmethod
    def _snapshot(cur: Any,case: dict[str,Any]) -> dict[str,Any]:
        cid=case["case_id"]
        cur.execute(
            """SELECT event_id,kind,amount_cents,evidence_upload_id,
                      reverses_event_id,state,reporter_id,verified_by
               FROM lhfm_recovery_events WHERE case_id=%s
               ORDER BY created_at,event_id FOR UPDATE""",
            (cid,),
        )
        entries=list(cur.fetchall())
        if not entries or any(e["state"]=="REPORTED" for e in entries):
            raise CaseConflict("unreviewed or absent recovery evidence")
        cur.execute(
            """SELECT event_id,directive,reason FROM lhfm_recovery_case_status_events
               WHERE case_id=%s ORDER BY event_id DESC LIMIT 1 FOR UPDATE""",
            (cid,),
        )
        status=cur.fetchone()
        if status and status["directive"] in ("DISPUTED","CLOSED"):
            raise CaseConflict("disputed or closed case is not invoice-ready")
        realized={}
        reversals={}
        evidence=[]
        for e in entries:
            item={k:(int(v) if k=="amount_cents" else v) for k,v in e.items()}
            evidence.append(item)
            if e["state"]=="CONFIRMED":
                if not e["verified_by"] or e["verified_by"]==e["reporter_id"]:
                    raise CaseConflict("recovery confirmation separation violated")
                if e["kind"]=="REALIZATION":
                    realized[e["event_id"]]=int(e["amount_cents"])
                elif e["kind"]=="REVERSAL":
                    key=e["reverses_event_id"]
                    reversals[key]=reversals.get(key,0)+int(e["amount_cents"])
                else:
                    raise CaseConflict("unknown confirmed recovery type")
        if any(k not in realized or v>realized[k] for k,v in reversals.items()):
            raise CaseConflict("unmatched or excess recovery reversal")
        net=sum(realized.values())-sum(reversals.values())
        if not 0<net<=int(case["difference_cents"]):
            raise CaseConflict("no positive bounded realized recovery")
        content={
            "case_id":cid, "agreement_id":case["agreement_id"],
            "audit_difference_cents":int(case["difference_cents"]),
            "fee_rate_bps":int(case["fee_rate_bps"]),
            "events":evidence,
            "case_status":status,
        }
        return {"digest":_digest(content),"content":content,
                "net":net,"fee":_proposal_cents(net,int(case["fee_rate_bps"]))}

    @staticmethod
    def _record_event(cur: Any, *, packet_id: str, tenant_id: str,
                      legal_entity_id: str, actor_id: str, kind: str,
                      reason: str | None = None) -> None:
        cur.execute(
            """INSERT INTO lhfm_billing_packet_events
               (packet_id,tenant_id,legal_entity_id,billing_actor_id,event_type,reason)
               VALUES (%s,%s,%s,%s,%s,%s)""",
            (packet_id,tenant_id,legal_entity_id,actor_id,kind,reason),
        )

    def prepare(self, *, audit_id: str,tenant_id: str,
                legal_entity_id: str,actor_id: str) -> dict[str,Any]:
        db=self._connect()
        try:
            with db.cursor() as cur:
                case=self._case(cur,audit_id=audit_id,tenant_id=tenant_id,
                                legal_entity_id=legal_entity_id)
                self._grant(cur,tenant_id=tenant_id,legal_entity_id=legal_entity_id,
                            actor_id=actor_id)
                terms=self._terms(cur,tenant_id=tenant_id,
                                  legal_entity_id=legal_entity_id,
                                  agreement_id=case["agreement_id"],
                                  fee_rate_bps=int(case["fee_rate_bps"]))
                snapshot=self._snapshot(cur,case)
                cur.execute(
                    """SELECT packet_id,state FROM lhfm_billing_packets
                       WHERE case_id=%s AND ledger_sha256=%s FOR UPDATE""",
                    (case["case_id"],snapshot["digest"]),
                )
                existing=cur.fetchone()
                if existing:
                    if existing["state"]=="VOIDED":
                        raise CaseConflict("voided snapshot cannot be reissued")
                    db.commit()
                    return {"packet_id":existing["packet_id"],"status":existing["state"],
                            "idempotent":True,"invoice_created":False}
                cur.execute(
                    """SELECT packet_id FROM lhfm_billing_packets
                       WHERE case_id=%s AND state='RELEASED' LIMIT 1 FOR UPDATE""",
                    (case["case_id"],),
                )
                if cur.fetchone():
                    raise CaseConflict("previous release requires accounting reconciliation")
                packet_id=str(uuid4())
                cur.execute(
                    """INSERT INTO lhfm_billing_packets
                       (packet_id,case_id,tenant_id,legal_entity_id,agreement_id,
                        created_by,net_realization_cents,fee_cents,fee_rate_bps,
                        accepted_terms_sha256,legal_clearance_sha256,
                        ledger_sha256,evidence_json,state)
                       VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'PREPARED')""",
                    (packet_id,case["case_id"],tenant_id,legal_entity_id,
                     case["agreement_id"],actor_id,snapshot["net"],snapshot["fee"],
                     int(case["fee_rate_bps"]),terms["accepted_terms_sha256"],
                     terms["legal_clearance_sha256"],snapshot["digest"],
                     json.dumps(snapshot["content"],separators=(",",":"),allow_nan=False)),
                )
                self._record_event(cur,packet_id=packet_id,tenant_id=tenant_id,
                                   legal_entity_id=legal_entity_id,
                                   actor_id=actor_id,kind="PREPARED")
            db.commit()
            return {"packet_id":packet_id,"status":"PREPARED","idempotent":False,
                    "invoice_created":False}
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    def release(self, *,packet_id: str,tenant_id: str,
                legal_entity_id: str,actor_id: str) -> dict[str,Any]:
        db=self._connect()
        try:
            with db.cursor() as cur:
                cur.execute(
                    """SELECT audit_id FROM lhfm_recovery_cases
                       WHERE case_id=(SELECT case_id FROM lhfm_billing_packets
                                      WHERE packet_id=%s AND tenant_id=%s
                                      AND legal_entity_id=%s)""",
                    (packet_id,tenant_id,legal_entity_id),
                )
                case_ref=cur.fetchone()
                if not case_ref: raise BundleNotFound("billing packet not found")
                case=self._case(cur,audit_id=case_ref["audit_id"],
                                tenant_id=tenant_id,legal_entity_id=legal_entity_id)
                cur.execute(
                    """SELECT * FROM lhfm_billing_packets
                       WHERE packet_id=%s AND case_id=%s AND tenant_id=%s
                         AND legal_entity_id=%s FOR UPDATE""",
                    (packet_id,case["case_id"],tenant_id,legal_entity_id),
                )
                packet=cur.fetchone()
                if not packet: raise BundleNotFound("billing packet not found")
                if packet["state"]!="PREPARED":
                    raise CaseConflict("billing packet cannot be released twice")
                if packet["created_by"]==actor_id:
                    raise PermissionError("preparer cannot release own billing packet")
                self._grant(cur,tenant_id=tenant_id,legal_entity_id=legal_entity_id,
                            actor_id=actor_id)
                terms=self._terms(cur,tenant_id=tenant_id,
                                  legal_entity_id=legal_entity_id,
                                  agreement_id=case["agreement_id"],
                                  fee_rate_bps=int(case["fee_rate_bps"]))
                snapshot=self._snapshot(cur,case)
                if (snapshot["digest"]!=packet["ledger_sha256"]
                        or snapshot["net"]!=int(packet["net_realization_cents"])
                        or snapshot["fee"]!=int(packet["fee_cents"])
                        or packet["accepted_terms_sha256"]!=terms["accepted_terms_sha256"]
                        or packet["legal_clearance_sha256"]!=terms["legal_clearance_sha256"]):
                    raise CaseConflict("fee packet stale: new realization, reversal or terms")
                cur.execute(
                    """SELECT packet_id FROM lhfm_billing_packets
                       WHERE case_id=%s AND state='RELEASED'
                       AND packet_id<>%s LIMIT 1 FOR UPDATE""",
                    (case["case_id"],packet_id),
                )
                if cur.fetchone():
                    raise CaseConflict("another accounting release is outstanding")
                cur.execute(
                    """UPDATE lhfm_billing_packets SET state='RELEASED',
                       released_by=%s,released_at=UTC_TIMESTAMP(6)
                       WHERE packet_id=%s AND state='PREPARED'""",
                    (actor_id,packet_id),
                )
                if cur.rowcount!=1:raise CaseConflict("concurrent fee packet release")
                self._record_event(cur,packet_id=packet_id,tenant_id=tenant_id,
                                   legal_entity_id=legal_entity_id,
                                   actor_id=actor_id,kind="RELEASED")
            db.commit()
            return {"packet_id":packet_id,"status":"RELEASED",
                    "fee_net":_eur(snapshot["fee"]),"invoice_created":False,
                    "requires_external_invoice":True}
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    def get(self, *,packet_id: str,tenant_id: str,
            legal_entity_id: str,actor_id: str) -> dict[str,Any]:
        db=self._connect()
        try:
            with db.cursor() as cur:
                self._grant(cur,tenant_id=tenant_id,legal_entity_id=legal_entity_id,
                            actor_id=actor_id)
                cur.execute(
                    """SELECT packet_id,case_id,agreement_id,state,
                              net_realization_cents,fee_cents,fee_rate_bps,
                              ledger_sha256,accepted_terms_sha256,legal_clearance_sha256,
                              evidence_json,created_by,released_by,voided_by,
                              external_correction_ref
                       FROM lhfm_billing_packets WHERE packet_id=%s
                         AND tenant_id=%s AND legal_entity_id=%s""",
                    (packet_id,tenant_id,legal_entity_id),
                )
                packet=cur.fetchone()
                if not packet:raise BundleNotFound("billing packet not found")
                cur.execute(
                    """SELECT audit_id FROM lhfm_recovery_cases WHERE case_id=%s""",
                    (packet["case_id"],),
                )
                audit_ref=cur.fetchone()
                case=self._case(cur,audit_id=audit_ref["audit_id"],
                                tenant_id=tenant_id,legal_entity_id=legal_entity_id)
                # Staleness must be visible even for a historically released packet.
                try:
                    snapshot=self._snapshot(cur,case)
                    stale=(snapshot["digest"]!=packet["ledger_sha256"])
                except CaseConflict:
                    stale=True
                cur.execute(
                    """SELECT event_type,billing_actor_id,reason,recorded_at
                       FROM lhfm_billing_packet_events WHERE packet_id=%s
                       ORDER BY event_id""",
                    (packet_id,),
                )
                events=cur.fetchall()
            return {
                "packet_id":packet_id,"state":packet["state"],
                "case_id":packet["case_id"],"agreement_id":packet["agreement_id"],
                "net_realization":_eur(int(packet["net_realization_cents"])),
                "fee_net":_eur(int(packet["fee_cents"])),
                "fee_rate_bps":int(packet["fee_rate_bps"]),
                "ledger_sha256":packet["ledger_sha256"],
                "terms_sha256":packet["accepted_terms_sha256"],
                "legal_clearance_sha256":packet["legal_clearance_sha256"],
                "evidence":json.loads(packet["evidence_json"]),
                "prepared_by":packet["created_by"],"released_by":packet["released_by"],
                "voided_by":packet["voided_by"],
                "external_correction_ref":packet["external_correction_ref"],
                "events":[{"event_type":e["event_type"],"actor":e["billing_actor_id"],
                           "reason":e["reason"],"recorded_at":e["recorded_at"].isoformat()}
                          for e in events],
                "stale":stale,"requires_external_correction":(
                    packet["state"]=="RELEASED" and stale),
                "invoice_created":False,"fee_due_net":"0.00",
                "external_invoice_required":packet["state"]=="RELEASED",
            }
        finally:
            db.close()

    def void(self, *,packet_id: str,tenant_id: str,legal_entity_id: str,
             actor_id: str,reason: str,external_correction_ref: str) -> dict[str,Any]:
        if (not isinstance(reason,str) or not reason.strip() or len(reason)>200
                or not isinstance(external_correction_ref,str)
                or not external_correction_ref.strip() or len(external_correction_ref)>200):
            raise ValueError("manual accounting correction evidence required")
        db=self._connect()
        try:
            with db.cursor() as cur:
                cur.execute(
                    """SELECT audit_id FROM lhfm_recovery_cases
                       WHERE case_id=(SELECT case_id FROM lhfm_billing_packets
                                      WHERE packet_id=%s AND tenant_id=%s
                                        AND legal_entity_id=%s)""",
                    (packet_id,tenant_id,legal_entity_id),
                )
                case_ref=cur.fetchone()
                if not case_ref:raise BundleNotFound("billing packet not found")
                case=self._case(cur,audit_id=case_ref["audit_id"],
                                tenant_id=tenant_id,legal_entity_id=legal_entity_id)
                self._grant(cur,tenant_id=tenant_id,
                            legal_entity_id=legal_entity_id,actor_id=actor_id)
                cur.execute(
                    """SELECT state,created_by FROM lhfm_billing_packets
                       WHERE packet_id=%s AND case_id=%s FOR UPDATE""",
                    (packet_id,case["case_id"]),
                )
                pkt=cur.fetchone()
                if not pkt or pkt["state"]!="RELEASED":
                    raise CaseConflict("only released accounting handoffs can be voided")
                if actor_id==pkt["created_by"]:
                    raise PermissionError("preparer cannot void own billing packet")
                cur.execute(
                    """UPDATE lhfm_billing_packets SET state='VOIDED',voided_by=%s,
                       void_reason=%s,external_correction_ref=%s,
                       voided_at=UTC_TIMESTAMP(6)
                       WHERE packet_id=%s AND state='RELEASED'""",
                    (actor_id,reason.strip(),external_correction_ref.strip(),packet_id),
                )
                if cur.rowcount!=1:raise CaseConflict("concurrent packet void")
                self._record_event(cur,packet_id=packet_id,tenant_id=tenant_id,
                                   legal_entity_id=legal_entity_id,
                                   actor_id=actor_id,kind="VOIDED",reason=reason.strip())
            db.commit()
            return {"packet_id":packet_id,"status":"VOIDED",
                    "external_correction_ref":external_correction_ref.strip(),
                    "invoice_created":False}
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()
