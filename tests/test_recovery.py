"""Two-actor 5% recovery ledger acceptance against real isolated MariaDB.

Synthetic reviewers and PDF evidence; no assertion of real bank reconciliation.
"""
from __future__ import annotations

from uuid import uuid4
from pathlib import Path
from tempfile import TemporaryDirectory
import socket
import threading
from fastapi.testclient import TestClient

from test_promotion import ReviewedPipelineTests
from lowhangingfruitme.api.http import create_app
from lowhangingfruitme.api.uploads import ClamAVScanner
from lowhangingfruitme.api.recovery import RecoveryLedger, _cents, _fee_proposal


PDF=lambda label: (b"%PDF-1.7\n% synthetic finance proof label: " + label.encode()+b"\n")


class RecoveryPipelineTests(ReviewedPipelineTests):
    def test_readyz_checks_real_socket_protocol_and_schema(self):
        with TemporaryDirectory() as temp:
            path = Path(temp) / "clamd.sock"
            server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            server.bind(str(path))
            server.listen(1)
            observed = []

            def serve():
                try:
                    conn, _ = server.accept()
                    with conn:
                        observed.append(conn.recv(64))
                        conn.sendall(b"PONG\0")
                finally:
                    server.close()

            thread = threading.Thread(target=serve, daemon=True)
            thread.start()
            self.uploads.scanner = ClamAVScanner(path, timeout=2)
            response = self.client.get("/readyz")
            thread.join(timeout=2)
            self.assertEqual(response.status_code, 200, response.text)
            self.assertEqual(response.json(), {"status": "ready"})
            self.assertEqual(observed, [b"zPING\0"])
        response = self.client.get("/readyz")
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()["detail"]["code"], "NOT_READY")

    def scope(self):
        return {"tenant_id": self.tenant, "legal_entity_id": self.entity}

    def setUp(self):
        super().setUp()
        # Each test has its own claim namespace, preserving the production
        # unique-claim guard without weakening or deleting its DB constraint.
        self.tenant="T-REC-"+uuid4().hex[:16]
        self.entity="LE-SYN-1"
        db=self.registry._connect()
        try:
            with db.cursor() as cur:
                cur.execute(
                    """INSERT INTO lhfm_reviewer_grants
                       (tenant_id,legal_entity_id,reviewer_id,role,active)
                       VALUES (%s,%s,%s,'contract_reviewer',1)""",
                    (self.tenant,self.entity,"REVIEWER-SYN-1"),
                )
                cur.execute(
                    """INSERT INTO lhfm_finance_grants
                       (tenant_id,legal_entity_id,finance_actor_id,active)
                       VALUES (%s,%s,%s,1)""",
                    (self.tenant,self.entity,"FINANCE-SYN-1"),
                )
            db.commit()
        finally:
            db.close()
        self.recovery=RecoveryLedger(
            registry=self.registry,store=self.store,uploads=self.uploads,
        )
        self.client=TestClient(create_app(
            service=self.service,store=self.store,uploads=self.uploads,
            promotion=self.promotion,recovery=self.recovery,
        ))
        self.addCleanup(self.client.close)

    def token(self,**overrides):
        overrides.setdefault(
            "scope",
            "lhfm:upload:write lhfm:approval:write lhfm:audit:execute "
            "lhfm:recovery:record lhfm:recovery:read",
        )
        return super().token(**overrides)

    def finance_headers(self,sub="FINANCE-SYN-1",scope="lhfm:recovery:verify"):
        return self.headers(sub=sub,scope=scope)

    def audit_id(self):
        tx,se,co=self.inputs()
        bundle=self.post(self.body(tx,se,co))
        self.assertEqual(bundle.status_code,201,bundle.text)
        r=self.client.post(
            "/v1/audits",
            json={**self.scope(),"bundle_id":bundle.json()["bundle_id"]},
            headers={**self.headers(),"Idempotency-Key":str(uuid4())},
        )
        self.assertEqual(r.status_code,201,r.text)
        self.assertEqual(r.json()["status"],"COMPLETED")
        return r.json()["audit_id"]

    def add_event(self,audit_id,amount="1000.00",kind="REALIZATION",
                  evidence=None,reverses=None,key=None, token=None):
        ref=evidence or self.upload(PDF(uuid4().hex),"RECOVERY_PDF")
        body={**self.scope(),"kind":kind,"amount_net":amount,
              "evidence_upload_id":ref,"reverses_event_id":reverses}
        r=self.client.post(
            f"/v1/audits/{audit_id}/recovery-events",
            json=body,
            headers={"Authorization":"Bearer "+(token or self.token()),
                     "Idempotency-Key":key or str(uuid4())},
        )
        return r,ref

    def review(self,event_id,decision="CONFIRM",sub="FINANCE-SYN-1",
               scope="lhfm:recovery:verify",verified=True,tenant=None):
        return self.client.post(
            f"/v1/recovery-events/{event_id}/review",
            json={"tenant_id":tenant or self.scope()["tenant_id"],
                  "legal_entity_id":self.scope()["legal_entity_id"],
                  "decision":decision,"confirm_evidence_review":verified},
            headers=self.finance_headers(sub=sub,scope=scope),
        )

    def ledger(self,audit_id,scope=None):
        return self.client.get(
            f"/v1/audits/{audit_id}/fee-ledger",
            params=self.scope(),
            headers=self.headers(scope=scope or "lhfm:recovery:read"),
        )

    def test_explicit_case_lifecycle_none_claimed_partial_full(self):
        audit=self.audit_id()
        self.assertEqual(self.ledger(audit).json()["case_status"],"NONE")
        r,_=self.add_event(audit,"1000.00")
        self.assertEqual(r.status_code,201,r.text)
        self.assertEqual(self.ledger(audit).json()["case_status"],"CLAIMED")
        self.assertEqual(self.review(r.json()["event_id"]).status_code,200)
        self.assertEqual(self.ledger(audit).json()["case_status"],"REALIZED_PARTIAL")
        full,_=self.add_event(audit,"1500.00")
        self.assertEqual(full.status_code,201,full.text)
        self.assertEqual(self.review(full.json()["event_id"]).status_code,200)
        self.assertEqual(self.ledger(audit).json()["case_status"],"REALIZED_FULL")
        self.assertEqual(self.ledger(audit).json()["calculated_variance_net"],"2500.00")
        self.assertEqual(self.ledger(audit).json()["billable_recovery_net"],"0.00")

    def test_finance_can_dispute_close_and_reopen_with_event_history(self):
        audit=self.audit_id()
        received,_=self.add_event(audit,"1000.00")
        self.assertEqual(received.status_code,201,received.text)
        endpoint=f"/v1/audits/{audit}/case-status"
        body={**self.scope(),"directive":"DISPUTED",
              "reason":"Synthetic supplier disputes settlement"}
        self.assertEqual(self.client.post(endpoint,json=body,
                         headers=self.finance_headers()).status_code,201)
        self.assertEqual(self.ledger(audit).json()["case_status"],"DISPUTED")
        body["directive"]="CLOSED"
        invalid=self.client.post(endpoint,json=body,headers=self.finance_headers())
        self.assertEqual(invalid.status_code,409,invalid.text)
        self.assertEqual(self.review(received.json()["event_id"]).status_code,200)
        allowed=self.client.post(endpoint,json=body,headers=self.finance_headers())
        self.assertEqual(allowed.status_code,201,allowed.text)
        self.assertEqual(self.ledger(audit).json()["case_status"],"CLOSED")
        closed,_=self.add_event(audit,"100.00")
        self.assertEqual(closed.status_code,409,closed.text)
        body["directive"]="OPEN"
        self.assertEqual(self.client.post(endpoint,json=body,
                         headers=self.finance_headers()).status_code,201)
        self.assertEqual(self.ledger(audit).json()["case_status"],"REALIZED_PARTIAL")

    def test_case_transition_requires_distinct_finance_grant_and_scope(self):
        audit=self.audit_id()
        r,_=self.add_event(audit,"100.00")
        self.assertEqual(r.status_code,201,r.text)
        endpoint=f"/v1/audits/{audit}/case-status"
        payload={**self.scope(),"directive":"DISPUTED","reason":"Pilot disagreement"}
        self.assertEqual(self.client.post(endpoint,json=payload,
                         headers=self.headers()).status_code,403)
        self.assertEqual(self.client.post(endpoint,json=payload,
                         headers=self.finance_headers(sub="REVIEWER-SYN-1")).status_code,403)
        payload["tenant_id"]="OTHER"
        result=self.client.post(endpoint,json=payload,
                                headers=self.finance_headers())
        self.assertIn(result.status_code,(403,404))
        self.assertEqual(self.ledger(audit).json()["case_status"],"CLAIMED")

    def test_fee_from_separately_confirmed_economic_receipt_not_audit_difference(self):
        audit=self.audit_id()
        initial=self.ledger(audit)
        self.assertEqual(initial.status_code,200,initial.text)
        self.assertEqual(initial.json()["audited_difference_net"],"2500.00")
        self.assertEqual(initial.json()["fee_proposal_net"],"0.00")
        r,_=self.add_event(audit,"1000.00")
        self.assertEqual(r.status_code,201,r.text)
        event=r.json()["event_id"]
        self.assertEqual(r.json()["status"],"REPORTED")
        self.assertEqual(self.ledger(audit).json()["fee_proposal_net"],"0.00")
        verified=self.review(event)
        self.assertEqual(verified.status_code,200,verified.text)
        self.assertEqual(verified.json()["status"],"CONFIRMED")
        ledger=self.ledger(audit).json()
        self.assertEqual(ledger["confirmed_realization_net"],"1000.00")
        self.assertEqual(ledger["fee_proposal_net"],"50.00")
        self.assertEqual(ledger["fee_rate"],"0.05")
        self.assertEqual(ledger["fee_due_net"],"0.00")
        self.assertFalse(ledger["invoice_created"])
        r2,_=self.add_event(audit,"1500.00")
        self.assertEqual(r2.status_code,201,r2.text)
        self.assertEqual(self.review(r2.json()["event_id"]).status_code,200)
        ledger=self.ledger(audit).json()
        self.assertEqual(ledger["confirmed_realization_net"],"2500.00")
        self.assertEqual(ledger["fee_proposal_net"],"125.00")
        self.assertFalse(ledger["billing_authorized"])

    def test_storno_reduces_net_and_5pct_fee(self):
        audit=self.audit_id()
        realized,_=self.add_event(audit,"2000.00")
        self.assertEqual(realized.status_code,201,realized.text)
        original=realized.json()["event_id"]
        self.assertEqual(self.review(original).status_code,200)
        rev,_=self.add_event(audit,"500.00",kind="REVERSAL",reverses=original)
        self.assertEqual(rev.status_code,201,rev.text)
        self.assertEqual(self.review(rev.json()["event_id"]).status_code,200)
        result=self.ledger(audit).json()
        self.assertEqual(result["confirmed_realization_net"],"1500.00")
        self.assertEqual(result["fee_proposal_net"],"75.00")
        other,_=self.add_event(audit,"1600.00",kind="REVERSAL",reverses=original)
        self.assertEqual(other.status_code,201,other.text)
        rejected=self.review(other.json()["event_id"])
        self.assertEqual(rejected.status_code,409)
        self.assertEqual(self.ledger(audit).json()["fee_proposal_net"],"75.00")

    def test_finance_verifier_must_be_independent_and_authorized(self):
        audit=self.audit_id()
        r,_=self.add_event(audit,"1000.00")
        event=r.json()["event_id"]
        self.assertEqual(self.review(event,sub="FORGED").status_code,403)
        self.assertEqual(self.review(event,scope="lhfm:audit:execute").status_code,403)
        self.assertEqual(self.review(event,sub="REVIEWER-SYN-1").status_code,403)
        # Even if finance rights are also later granted to the original
        # reporter, this event remains subject to independent review.
        db=self.registry._connect()
        try:
            with db.cursor() as c:
                c.execute("""INSERT INTO lhfm_finance_grants
                    (tenant_id,legal_entity_id,finance_actor_id,active)
                    VALUES (%s,%s,%s,1)""",
                    (self.tenant,self.entity,"REVIEWER-SYN-1"),
                )
            db.commit()
        finally:
            db.close()
        self.assertEqual(self.review(event,sub="REVIEWER-SYN-1").status_code,403)
        self.assertEqual(self.ledger(audit).json()["fee_proposal_net"],"0.00")

    def test_existing_3_percent_case_preserves_its_fee_policy(self):
        audit=self.audit_id()
        r,_=self.add_event(audit,"1000.00")
        self.assertEqual(r.status_code,201,r.text)
        self.assertEqual(self.review(r.json()["event_id"]).status_code,200)
        # Simulate a pre-migration case after SQL 007 backfilled 300 bps.
        db=self.registry._connect()
        try:
            with db.cursor() as cur:
                cur.execute(
                    """UPDATE lhfm_recovery_cases SET fee_rate_bps=300
                       WHERE audit_id=%s AND tenant_id=%s""",
                    (audit,self.tenant),
                )
            db.commit()
        finally:
            db.close()
        old=self.ledger(audit).json()
        self.assertEqual(old["fee_rate"],"0.03")
        self.assertEqual(old["fee_proposal_net"],"30.00")
        self.assertEqual(old["fee_due_net"],"0.00")

    def test_no_duplicate_evidence_and_idempotent_replay(self):
        audit=self.audit_id()
        key=str(uuid4())
        r,evidence=self.add_event(audit,"1000.00",key=key)
        self.assertEqual(r.status_code,201,r.text)
        repeated,_=self.add_event(audit,"1000.00",key=key,evidence=evidence)
        self.assertEqual(repeated.status_code,201,repeated.text)
        self.assertEqual(repeated.json()["event_id"],r.json()["event_id"])
        conflict,_=self.add_event(audit,"1200.00",key=key,evidence=evidence)
        self.assertEqual(conflict.status_code,409)
        other,_=self.add_event(audit,"1000.00",evidence=evidence)
        self.assertEqual(other.status_code,409)

    def test_reported_amount_over_audited_difference_cannot_be_confirmed(self):
        audit=self.audit_id()
        r,_=self.add_event(audit,"2500.01")
        self.assertEqual(r.status_code,201,r.text)
        self.assertEqual(self.review(r.json()["event_id"]).status_code,409)
        result=self.ledger(audit).json()
        self.assertEqual(result["unreviewed_event_count"],1)
        self.assertEqual(result["fee_proposal_net"],"0.00")

    def test_rejected_event_remains_nonbillable_and_cannot_be_reopened(self):
        audit=self.audit_id()
        r,_=self.add_event(audit,"500.00")
        event=r.json()["event_id"]
        rejected=self.review(event,decision="REJECT")
        self.assertEqual(rejected.status_code,200,rejected.text)
        self.assertEqual(rejected.json()["status"],"REJECTED")
        self.assertEqual(self.review(event).status_code,409)
        self.assertEqual(self.ledger(audit).json()["fee_proposal_net"],"0.00")

    def test_failed_audit_does_not_allow_recovery(self):
        raw=str(uuid4())
        r,_=self.add_event(raw,"1000.00")
        self.assertEqual(r.status_code,404)

    def test_finance_review_is_idempotent_and_not_cross_tenant(self):
        audit=self.audit_id()
        r,_=self.add_event(audit,"600.00")
        event=r.json()["event_id"]
        first=self.review(event)
        self.assertEqual(first.status_code,200,first.text)
        second=self.review(event)
        self.assertEqual(second.status_code,200,second.text)
        self.assertTrue(second.json()["idempotent"])
        self.assertEqual(self.review(event,tenant="WRONG").status_code,403)
        self.assertEqual(self.ledger(audit).json()["fee_proposal_net"],"30.00")


class RecoveryCentsTests(ReviewedPipelineTests):
    def test_strict_money_and_half_up_remainder(self):
        self.assertEqual(_cents("0.01"),1)
        self.assertEqual(_fee_proposal(50),"0.03")
        self.assertEqual(_fee_proposal(1000),"0.50")
        self.assertEqual(_fee_proposal(1000,300),"0.30")
        for raw in ("-1.00","1","1.1","1.234","NaN","1e5","00.01","0.00"):
            with self.assertRaises(ValueError):
                _cents(raw)
