"""Billing handoff full MariaDB/API checks; all records and operators synthetic.

No real invoice, tax authority, legal opinion, bank receipt or customer
acceptance is created by these tests.
"""
from __future__ import annotations

from hashlib import sha256
from uuid import uuid4

from fastapi.testclient import TestClient

from test_recovery import RecoveryPipelineTests
from lowhangingfruitme.api.http import create_app
from lowhangingfruitme.api.billing import BillingHandoffService


class BillingHandoffTests(RecoveryPipelineTests):
    def setUp(self):
        super().setUp()
        self.billing=BillingHandoffService(connect=self.registry._connect)
        self.client=TestClient(create_app(
            service=self.service,store=self.store,uploads=self.uploads,
            promotion=self.promotion,recovery=self.recovery,billing=self.billing,
        ))
        self.addCleanup(self.client.close)
        db=self.registry._connect()
        try:
            with db.cursor() as cur:
                for actor in ("BILLING-SYN-1","BILLING-SYN-2"):
                    cur.execute(
                        """INSERT INTO lhfm_billing_grants
                           (tenant_id,legal_entity_id,billing_actor_id,active)
                           VALUES (%s,%s,%s,1)""",
                        (self.tenant,self.entity,actor),
                    )
            db.commit()
        finally:
            db.close()

    def billing_headers(self,actor="BILLING-SYN-1",scope="lhfm:billing:prepare"):
        return self.headers(sub=actor,scope=scope)

    def provision_terms(self,fee_rate_bps=500):
        db=self.registry._connect()
        try:
            with db.cursor() as cur:
                cur.execute(
                    """INSERT INTO lhfm_commercial_terms
                       (tenant_id,legal_entity_id,agreement_id,
                        accepted_terms_sha256,acceptance_evidence_ref,
                        legal_clearance_sha256,legal_clearance_ref,
                        fee_rate_bps,active,verified_by,accepted_at,checked_at)
                       VALUES (%s,%s,%s,%s,%s,%s,%s,%s,1,%s,
                               UTC_TIMESTAMP(6),UTC_TIMESTAMP(6))""",
                    (
                        self.tenant,self.entity,"AGR-1",
                        sha256(b"synthetic company-accepted terms").hexdigest(),
                        "SYNTHETIC-CUSTOMER-ACCEPTANCE",
                        sha256(b"synthetic legal review").hexdigest(),
                        "SYNTHETIC-LEGAL-CLEARANCE",
                        fee_rate_bps,"OPERATOR-SYN-ONLY",
                    ),
                )
            db.commit()
        finally:
            db.close()

    def prepare(self,audit,actor="BILLING-SYN-1",scope="lhfm:billing:prepare",tenant=None):
        return self.client.post(
            f"/v1/audits/{audit}/billing-packets",
            json={"tenant_id":tenant or self.tenant,"legal_entity_id":self.entity},
            headers=self.billing_headers(actor=actor,scope=scope),
        )

    def packet(self,pid,actor="BILLING-SYN-1",tenant=None):
        return self.client.get(
            f"/v1/billing-packets/{pid}",
            params={"tenant_id":tenant or self.tenant,"legal_entity_id":self.entity},
            headers=self.billing_headers(actor=actor,scope="lhfm:billing:read"),
        )

    def release(self,pid,actor="BILLING-SYN-2",scope="lhfm:billing:release"):
        return self.client.post(
            f"/v1/billing-packets/{pid}/release",
            json={**self.scope(),"confirm_commercial_terms_review":True},
            headers=self.billing_headers(actor=actor,scope=scope),
        )

    def void(self,pid,actor="BILLING-SYN-2",ref="SYN-CREDIT-NOTE-1"):
        return self.client.post(
            f"/v1/billing-packets/{pid}/void",
            json={**self.scope(),"reason":"Verified synthetic correction",
                  "external_correction_ref":ref},
            headers=self.billing_headers(actor=actor,scope="lhfm:billing:void"),
        )

    def test_no_invoice_without_real_provisioned_fee_terms(self):
        audit=self.audit_id()
        event,_=self.add_event(audit,"1000.00")
        self.assertEqual(event.status_code,201,event.text)
        self.assertEqual(self.review(event.json()["event_id"]).status_code,200)
        blocked=self.prepare(audit)
        self.assertEqual(blocked.status_code,409,blocked.text)
        self.assertEqual(self.ledger(audit).json()["fee_due_net"],"0.00")

    def test_different_rates_and_noncurrent_terms_rejected(self):
        audit=self.audit_id()
        event,_=self.add_event(audit,"1000.00")
        self.assertEqual(self.review(event.json()["event_id"]).status_code,200)
        self.provision_terms(fee_rate_bps=300)
        result=self.prepare(audit)
        self.assertEqual(result.status_code,409,result.text)

    def test_release_requires_two_billing_actors_and_freezes_verified_fee(self):
        audit=self.audit_id()
        self.provision_terms()
        r,_=self.add_event(audit,"1000.00")
        self.assertEqual(r.status_code,201,r.text)
        self.assertEqual(self.review(r.json()["event_id"]).status_code,200)
        start=self.prepare(audit)
        self.assertEqual(start.status_code,201,start.text)
        pid=start.json()["packet_id"]
        self.assertEqual(self.prepare(audit).json()["packet_id"],pid)
        detail=self.packet(pid)
        self.assertEqual(detail.status_code,200,detail.text)
        self.assertEqual(detail.json()["fee_net"],"50.00")
        self.assertEqual(detail.json()["net_realization"],"1000.00")
        self.assertEqual(detail.json()["state"],"PREPARED")
        self.assertEqual(self.release(pid,actor="BILLING-SYN-1").status_code,403)
        self.assertEqual(self.release(pid,scope="lhfm:billing:prepare").status_code,401)
        self.assertEqual(self.packet(pid,actor="IMPERSONATOR").status_code,403)
        self.assertEqual(self.packet(pid,tenant="CROSS-TENANT").status_code,403)
        release=self.release(pid)
        self.assertEqual(release.status_code,200,release.text)
        self.assertEqual(release.json()["status"],"RELEASED")
        self.assertFalse(release.json()["invoice_created"])
        self.assertTrue(release.json()["requires_external_invoice"])
        self.assertEqual(self.release(pid).status_code,409)
        self.assertEqual(self.packet(pid).json()["state"],"RELEASED")
        self.assertFalse(self.packet(pid).json()["stale"])
        self.assertEqual(self.ledger(audit).json()["fee_due_net"],"0.00")

    def test_storno_after_release_requires_documented_external_correction(self):
        audit=self.audit_id()
        self.provision_terms()
        first,_=self.add_event(audit,"1800.00")
        eid=first.json()["event_id"]
        self.assertEqual(self.review(eid).status_code,200)
        prep=self.prepare(audit)
        self.assertEqual(prep.status_code,201,prep.text)
        pid=prep.json()["packet_id"]
        self.assertEqual(self.release(pid).status_code,200)
        reversal,_=self.add_event(audit,"300.00",kind="REVERSAL",reverses=eid)
        self.assertEqual(reversal.status_code,201,reversal.text)
        self.assertEqual(self.review(reversal.json()["event_id"]).status_code,200)
        detail=self.packet(pid)
        self.assertTrue(detail.json()["stale"])
        self.assertTrue(detail.json()["requires_external_correction"])
        self.assertEqual(self.prepare(audit).status_code,409)
        self.assertEqual(self.void(pid,actor="BILLING-SYN-1").status_code,403)
        self.assertEqual(self.void(pid,ref="").status_code,422)
        void=self.void(pid,ref="SYN-CREDIT-NOTE-PROCESSED")
        self.assertEqual(void.status_code,200,void.text)
        self.assertEqual(self.packet(pid).json()["state"],"VOIDED")
        next_packet=self.prepare(audit)
        self.assertEqual(next_packet.status_code,201,next_packet.text)
        pid2=next_packet.json()["packet_id"]
        self.assertNotEqual(pid,pid2)
        self.assertEqual(self.packet(pid2).json()["fee_net"],"75.00")

    def test_financial_changes_between_prepare_and_release_refuse_replay(self):
        audit=self.audit_id()
        self.provision_terms()
        first,_=self.add_event(audit,"1200.00")
        self.assertEqual(self.review(first.json()["event_id"]).status_code,200)
        prepared=self.prepare(audit)
        self.assertEqual(prepared.status_code,201,prepared.text)
        pid=prepared.json()["packet_id"]
        second,_=self.add_event(audit,"100.00")
        self.assertEqual(second.status_code,201,second.text)
        self.assertEqual(self.review(second.json()["event_id"]).status_code,200)
        self.assertEqual(self.release(pid).status_code,409)
        self.assertTrue(self.packet(pid).json()["stale"])

    def test_unreviewed_source_evidence_cannot_be_prepared(self):
        audit=self.audit_id()
        self.provision_terms()
        event,_=self.add_event(audit,"1000.00")
        self.assertEqual(event.status_code,201)
        self.assertEqual(self.prepare(audit).status_code,409)
        self.assertEqual(self.review(event.json()["event_id"]).status_code,200)
        self.assertEqual(self.prepare(audit).status_code,201)

    def test_rejected_billing_grant_is_rechecked(self):
        audit=self.audit_id()
        self.provision_terms()
        event,_=self.add_event(audit,"1000.00")
        self.review(event.json()["event_id"])
        prep=self.prepare(audit)
        pid=prep.json()["packet_id"]
        db=self.registry._connect()
        try:
            with db.cursor() as cur:
                cur.execute(
                    """UPDATE lhfm_billing_grants SET active=0
                       WHERE tenant_id=%s AND legal_entity_id=%s
                         AND billing_actor_id='BILLING-SYN-2'""",
                    (self.tenant,self.entity),
                )
            db.commit()
        finally:
            db.close()
        self.assertEqual(self.release(pid).status_code,403)
        self.assertEqual(self.packet(pid,actor="BILLING-SYN-2").status_code,403)

    def test_amended_commercial_terms_require_new_proposal_and_release(self):
        audit=self.audit_id()
        self.provision_terms()
        r,_=self.add_event(audit,"1000.00")
        self.assertEqual(self.review(r.json()["event_id"]).status_code,200)
        earlier=self.prepare(audit)
        self.assertEqual(earlier.status_code,201,earlier.text)
        old=earlier.json()["packet_id"]
        db=self.registry._connect()
        try:
            with db.cursor() as cur:
                cur.execute(
                    """UPDATE lhfm_commercial_terms SET accepted_terms_sha256=%s
                       WHERE tenant_id=%s AND legal_entity_id=%s
                       AND agreement_id='AGR-1'""",
                    (sha256(b"second synthetic customer approval").hexdigest(),
                     self.tenant,self.entity),
                )
            db.commit()
        finally:
            db.close()
        self.assertTrue(self.packet(old).json()["stale"])
        self.assertEqual(self.release(old).status_code,409)
        current=self.prepare(audit)
        self.assertEqual(current.status_code,201,current.text)
        self.assertNotEqual(old,current.json()["packet_id"])
        self.assertEqual(self.release(current.json()["packet_id"]).status_code,200)

    def test_terms_revocation_flags_previous_released_invoice_handoff(self):
        audit=self.audit_id()
        self.provision_terms()
        r,_=self.add_event(audit,"400.00")
        self.assertEqual(self.review(r.json()["event_id"]).status_code,200)
        pid=self.prepare(audit).json()["packet_id"]
        self.assertEqual(self.release(pid).status_code,200)
        db=self.registry._connect()
        try:
            with db.cursor() as cur:
                cur.execute(
                    """UPDATE lhfm_commercial_terms SET active=0
                       WHERE tenant_id=%s AND legal_entity_id=%s
                       AND agreement_id='AGR-1'""",
                    (self.tenant,self.entity),
                )
            db.commit()
        finally:
            db.close()
        detail=self.packet(pid)
        self.assertEqual(detail.status_code,200)
        self.assertTrue(detail.json()["stale"])
        self.assertTrue(detail.json()["requires_external_correction"])
        self.assertEqual(self.prepare(audit).status_code,409)

    def test_historical_three_percent_fee_case_remains_at_three_percent(self):
        audit=self.audit_id()
        event,_=self.add_event(audit,"1000.00")
        self.assertEqual(self.review(event.json()["event_id"]).status_code,200)
        db=self.registry._connect()
        try:
            with db.cursor() as cur:
                cur.execute(
                    """UPDATE lhfm_recovery_cases SET fee_rate_bps=300
                       WHERE audit_id=%s AND tenant_id=%s AND legal_entity_id=%s""",
                    (audit,self.tenant,self.entity),
                )
            db.commit()
        finally:
            db.close()
        self.provision_terms(fee_rate_bps=300)
        proposal=self.prepare(audit)
        self.assertEqual(proposal.status_code,201,proposal.text)
        pid=proposal.json()["packet_id"]
        self.assertEqual(self.packet(pid).json()["fee_rate_bps"],300)
        self.assertEqual(self.packet(pid).json()["fee_net"],"30.00")
        result=self.release(pid)
        self.assertEqual(result.status_code,200,result.text)
        self.assertEqual(result.json()["fee_net"],"30.00")
        self.assertFalse(result.json()["invoice_created"])
