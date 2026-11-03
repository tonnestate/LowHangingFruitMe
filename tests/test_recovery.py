"""Two-actor 3% recovery ledger acceptance against real isolated MariaDB.

Synthetic reviewers and PDF evidence; no assertion of real bank reconciliation.
"""
from __future__ import annotations

from uuid import uuid4
from fastapi.testclient import TestClient

from test_promotion import ReviewedPipelineTests
from lowhangingfruitme.api.http import create_app
from lowhangingfruitme.api.recovery import RecoveryLedger, _cents, _fee_proposal


PDF=lambda label: (b"%PDF-1.7\n% synthetic finance proof label: " + label.encode()+b"\n")


class RecoveryPipelineTests(ReviewedPipelineTests):
    def setUp(self):
        super().setUp()
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
        self.assertEqual(ledger["fee_proposal_net"],"30.00")
        self.assertEqual(ledger["fee_due_net"],"0.00")
        self.assertFalse(ledger["invoice_created"])
        r2,_=self.add_event(audit,"1500.00")
        self.assertEqual(r2.status_code,201,r2.text)
        self.assertEqual(self.review(r2.json()["event_id"]).status_code,200)
        ledger=self.ledger(audit).json()
        self.assertEqual(ledger["confirmed_realization_net"],"2500.00")
        self.assertEqual(ledger["fee_proposal_net"],"75.00")
        self.assertFalse(ledger["billing_authorized"])

    def test_storno_reduces_net_and_3pct_fee(self):
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
        self.assertEqual(result["fee_proposal_net"],"45.00")
        other,_=self.add_event(audit,"1600.00",kind="REVERSAL",reverses=original)
        self.assertEqual(other.status_code,201,other.text)
        rejected=self.review(other.json()["event_id"])
        self.assertEqual(rejected.status_code,409)
        self.assertEqual(self.ledger(audit).json()["fee_proposal_net"],"45.00")

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
                    ("T-SYN-1","LE-SYN-1","REVIEWER-SYN-1"),
                )
            db.commit()
        finally:
            db.close()
        self.assertEqual(self.review(event,sub="REVIEWER-SYN-1").status_code,403)
        self.assertEqual(self.ledger(audit).json()["fee_proposal_net"],"0.00")

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
        self.assertEqual(self.ledger(audit).json()["fee_proposal_net"],"18.00")


class RecoveryCentsTests(ReviewedPipelineTests):
    def test_strict_money_and_half_up_remainder(self):
        self.assertEqual(_cents("0.01"),1)
        self.assertEqual(_fee_proposal(50),"0.02")
        self.assertEqual(_fee_proposal(1000),"0.30")
        for raw in ("-1.00","1","1.1","1.234","NaN","1e5","00.01","0.00"):
            with self.assertRaises(ValueError):
                _cents(raw)
