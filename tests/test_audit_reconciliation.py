"""Crash-safe audit reconciliation: real MariaDB, no live customer data."""
from __future__ import annotations

import os
import unittest
from uuid import uuid4

from lowhangingfruitme.approval_registry import ApprovalRegistry
from lowhangingfruitme.audit_reconciliation import (
    AuditReconciliationBlocked, reconcile_abandoned_audit,
)

APPROVED = {
    "LHFM_AUDIT_RECONCILIATION_APPROVED": "YES",
    "LHFM_AUDIT_WORKERS_STOPPED": "YES",
}
TENANT = "T-AUDIT-REC-SYN"
ENTITY = "LE-AUDIT-REC-SYN"
OPERATOR = "OPER-REC-SYN"


@unittest.skipUnless(bool(os.getenv("LHFM_DB_HOST")), "real MariaDB required")
class AuditReconciliationTests(unittest.TestCase):
    def setUp(self):
        self.registry = ApprovalRegistry.from_environment()
        self.connect = self.registry._connect
        self.bundle_id = str(uuid4())
        self.ids = []
        self.addCleanup(self.clean)
        db = self.connect()
        try:
            with db.cursor() as c:
                c.execute(
                    "INSERT INTO lhfm_api_bundles"
                    " (bundle_id,tenant_id,legal_entity_id,manifest_json)"
                    " VALUES (%s,%s,%s,%s)",
                    (self.bundle_id,TENANT,ENTITY,"{}"),
                )
            db.commit()
        finally:
            db.close()

    def clean(self):
        db = self.connect()
        try:
            with db.cursor() as c:
                for audit_id in self.ids:
                    c.execute(
                        "DELETE FROM lhfm_audit_reconciliation_events WHERE audit_id=%s",
                        (audit_id,),
                    )
                    c.execute("DELETE FROM lhfm_api_runs WHERE audit_id=%s",(audit_id,))
                c.execute("DELETE FROM lhfm_api_bundles WHERE bundle_id=%s",(self.bundle_id,))
            db.commit()
        finally:
            db.close()

    def reservation(self, *, minutes=90, status="PROCESSING",
                    report_json=None, executed=False, finished=False):
        audit_id = str(uuid4())
        db = self.connect()
        try:
            with db.cursor() as c:
                c.execute(
                    "INSERT INTO lhfm_api_runs"
                    " (audit_id,tenant_id,legal_entity_id,reviewer_id,bundle_id,"
                    " idempotency_key,request_sha256,status,audit_executed,"
                    " report_json,started_at,finished_at)"
                    " VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,"
                    " DATE_SUB(UTC_TIMESTAMP(6),INTERVAL %s MINUTE),"
                    " IF(%s,UTC_TIMESTAMP(6),NULL))",
                    (audit_id,TENANT,ENTITY,"REVIEWER-REC-SYN",self.bundle_id,
                     str(uuid4()),"a"*64,status,int(executed),report_json,
                     minutes,int(finished)),
                )
            db.commit()
        finally:
            db.close()
        self.ids.append(audit_id)
        return audit_id

    def reconcile(self,audit_id,*,apply=False,approvals=None,entity=ENTITY,
            incident_ref="INC-SYN-123"):
        return reconcile_abandoned_audit(
            connect=self.connect,audit_id=audit_id,tenant_id=TENANT,
            legal_entity_id=entity,operator_id=OPERATOR,
            incident_ref=incident_ref,apply=apply,
            approvals=approvals if approvals is not None else {},
        )

    def state(self,audit_id):
        db=self.connect()
        try:
            with db.cursor() as c:
                c.execute(
                    "SELECT status,idempotency_key,report_json FROM lhfm_api_runs"
                    " WHERE audit_id=%s",(audit_id,),
                )
                return c.fetchone()
        finally:
            db.close()

    def events(self,audit_id):
        db=self.connect()
        try:
            with db.cursor() as c:
                c.execute(
                    "SELECT operator_id,incident_ref,prior_state"
                    " FROM lhfm_audit_reconciliation_events WHERE audit_id=%s",
                    (audit_id,),
                )
                return list(c.fetchall())
        finally:
            db.close()

    def test_dry_run_never_changes_state_or_event(self):
        audit_id=self.reservation()
        result=self.reconcile(audit_id)
        self.assertEqual(result["mode"],"dry_run")
        self.assertTrue(result["eligible_after_worker_shutdown"])
        self.assertEqual(self.state(audit_id)["status"],"PROCESSING")
        self.assertEqual(self.events(audit_id),[])

    def test_apply_requires_independent_maintenance_and_stop_confirmation(self):
        audit_id=self.reservation()
        for approvals in ({},
                          {"LHFM_AUDIT_RECONCILIATION_APPROVED":"YES"},
                          {"LHFM_AUDIT_WORKERS_STOPPED":"YES"}):
            with self.subTest(approvals=approvals):
                with self.assertRaisesRegex(AuditReconciliationBlocked,"approval"):
                    self.reconcile(audit_id,apply=True,approvals=approvals)
        self.assertEqual(self.state(audit_id)["status"],"PROCESSING")

    def test_abandoned_run_is_failed_once_with_immutable_event(self):
        audit_id=self.reservation()
        old=self.state(audit_id)["idempotency_key"]
        result=self.reconcile(audit_id,apply=True,approvals=APPROVED)
        self.assertEqual(result["resulting_state"],"FAILED")
        self.assertFalse(result["retry_automatic"])
        self.assertEqual(self.state(audit_id)["idempotency_key"],old)
        self.assertIsNone(self.state(audit_id)["report_json"])
        self.assertEqual(self.events(audit_id),
                         [{"operator_id":OPERATOR,"incident_ref":"INC-SYN-123",
                           "prior_state":"PROCESSING"}])
        with self.assertRaisesRegex(AuditReconciliationBlocked,"only unfinished"):
            self.reconcile(audit_id,apply=True,approvals=APPROVED)
        self.assertEqual(len(self.events(audit_id)),1)

    def test_recent_processing_cannot_be_failed(self):
        audit_id=self.reservation(minutes=1)
        self.assertFalse(self.reconcile(audit_id)["eligible_after_worker_shutdown"])
        with self.assertRaisesRegex(AuditReconciliationBlocked,"too recent"):
            self.reconcile(audit_id,apply=True,approvals=APPROVED)
        self.assertEqual(self.state(audit_id)["status"],"PROCESSING")

    def test_completed_reviewed_failed_and_ambiguous_rows_rejected(self):
        for data in (
            {"status":"COMPLETED","report_json":"{}","executed":True,"finished":True},
            {"status":"NEEDS_REVIEW","report_json":"{}","finished":True},
            {"status":"FAILED","finished":True},
            {"report_json":"{}"},
            {"executed":True},
            {"finished":True},
        ):
            with self.subTest(data=data):
                audit_id=self.reservation(**data)
                with self.assertRaisesRegex(AuditReconciliationBlocked,"only unfinished"):
                    self.reconcile(audit_id,apply=True,approvals=APPROVED)
                self.assertEqual(self.events(audit_id),[])

    def test_scope_and_input_validation_fails_closed(self):
        audit_id=self.reservation()
        with self.assertRaisesRegex(AuditReconciliationBlocked,"not found"):
            self.reconcile(audit_id,apply=True,approvals=APPROVED,entity="OTHER-ENTITY")
        with self.assertRaisesRegex(AuditReconciliationBlocked,"invalid"):
            self.reconcile("../../../etc/passwd")
        with self.assertRaisesRegex(AuditReconciliationBlocked,"incident"):
            self.reconcile(audit_id,incident_ref="\nINVALID")
        self.assertEqual(self.state(audit_id)["status"],"PROCESSING")


if __name__=="__main__":
    unittest.main()
