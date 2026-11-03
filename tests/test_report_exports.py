"""Customer PDF/XLSX/JSON acceptance through the real authenticated audit API.

Uses only synthetic finance fixtures and independent reviewer confirmation.
"""
from __future__ import annotations

from copy import deepcopy
from io import BytesIO
import json
from uuid import uuid4

from openpyxl import load_workbook

from test_recovery import RecoveryPipelineTests
from lowhangingfruitme.api.reports import customer_case, render_export, ReportNotReady


class CustomerReportTests(RecoveryPipelineTests):
    def download(self, audit_id, fmt="json", headers=None, tenant=None):
        return self.client.get(
            f"/v1/audits/{audit_id}/report.{fmt}",
            params={"tenant_id":tenant or self.tenant,
                    "legal_entity_id":self.entity},
            headers=headers if headers is not None else self.headers(
                scope="lhfm:audit:execute lhfm:recovery:read"),
        )

    def test_json_report_preserves_source_hashes_and_nonbillable_amounts(self):
        audit=self.audit_id()
        response=self.download(audit)
        self.assertEqual(response.status_code,200,response.text)
        self.assertIn("attachment;",response.headers["content-disposition"])
        case=response.json()
        self.assertEqual(case["calculated_variance_net"],"2500.00")
        self.assertEqual(case["recovery"]["fee_proposal_net"],"0.00")
        self.assertEqual(case["recovery"]["billable_recovery_net"],"0.00")
        self.assertEqual(case["recovery"]["fee_due_net"],"0.00")
        self.assertEqual(case["recovery"]["fee_rate"],"0.03")
        self.assertEqual(case["audit_id"],audit)
        self.assertEqual(len(case["source_provenance"]["transactions"]["original_sha256"]),64)
        self.assertEqual(len(case["source_provenance"]["settlements"]["original_sha256"]),64)
        self.assertEqual(len(case["lineage_sha256"]),64)
        self.assertIn("REVIEWER-SYN-1",self.token())
        self.assertNotIn("approval_receipt",response.text)
        self.assertNotIn("receipt_sha256",response.text)
        self.assertNotIn("private_path",response.text)

    def test_manual_independent_realization_visible_but_not_invoiced(self):
        audit=self.audit_id()
        r,_=self.add_event(audit,"1000.00")
        self.assertEqual(r.status_code,201,r.text)
        self.assertEqual(self.review(r.json()["event_id"]).status_code,200)
        case=self.download(audit).json()
        self.assertEqual(case["calculated_variance_net"],"2500.00")
        self.assertEqual(case["recovery"]["confirmed_realization_net"],"1000.00")
        self.assertEqual(case["recovery"]["fee_proposal_net"],"30.00")
        self.assertEqual(case["recovery"]["fee_due_net"],"0.00")
        self.assertEqual(case["recovery"]["events"][0]["state"],"CONFIRMED")

    def test_pdf_download_is_real_binary_document(self):
        audit=self.audit_id()
        response=self.download(audit,"pdf")
        self.assertEqual(response.status_code,200,response.text[:250])
        self.assertEqual(response.headers["content-type"],"application/pdf")
        self.assertTrue(response.content.startswith(b"%PDF-"))
        self.assertTrue(response.content.rstrip().endswith(b"%%EOF"))
        self.assertGreater(len(response.content),1100)

    def test_xlsx_download_contains_evidence_and_money_fields(self):
        audit=self.audit_id()
        response=self.download(audit,"xlsx")
        self.assertEqual(response.status_code,200,response.text[:250])
        book=load_workbook(BytesIO(response.content),read_only=True)
        try:
            self.assertIn("Differenzfall",book.sheetnames)
            self.assertIn("Quellen",book.sheetnames)
            self.assertIn("Evidenz",book.sheetnames)
            values={row[0]:row[1] for row in book["Differenzfall"].iter_rows(values_only=True)}
            self.assertEqual(values["Rechnerische Differenz EUR"],"2500.00")
            self.assertEqual(values["Honorarvorschlag 3 Prozent EUR"],"0.00")
            self.assertEqual(values["Faelliges Honorar EUR"],"0.00")
            self.assertEqual(book["Quellen"].max_row,4)
        finally:
            book.close()

    def test_cross_tenant_and_missing_scopes_are_denied(self):
        audit=self.audit_id()
        self.assertEqual(self.download(audit,headers={}).status_code,401)
        self.assertEqual(
            self.download(audit,headers=self.headers(scope="lhfm:audit:execute")).status_code,
            403,
        )
        self.assertEqual(self.download(audit,tenant="T-FOREIGN").status_code,403)
        self.assertEqual(
            self.download(audit,headers=self.headers(
                sub="UNRELATED",scope="lhfm:audit:execute lhfm:recovery:read")
            ).status_code,403,
        )

    def test_audit_needing_review_cannot_be_exported_as_evidenced(self):
        tx,se,co=self.inputs()
        body=self.body(tx,se,co)
        body["controls"]=None
        bundle=self.post(body)
        self.assertEqual(bundle.status_code,201,bundle.text)
        started=self.client.post(
            "/v1/audits",json={**self.scope(),"bundle_id":bundle.json()["bundle_id"]},
            headers={**self.headers(),"Idempotency-Key":str(uuid4())},
        )
        self.assertEqual(started.status_code,201,started.text)
        self.assertEqual(started.json()["status"],"NEEDS_REVIEW")
        self.assertEqual(self.download(started.json()["audit_id"]).status_code,409)

    def test_export_escapes_spreadsheet_formulas_in_external_identifiers(self):
        audited=self.audit_id()
        run=self.store.get_run(audit_id=audited,tenant_id=self.tenant,
                               legal_entity_id=self.entity,reviewer_id="REVIEWER-SYN-1")
        ledger=self.recovery.ledger(
            audit_id=audited,tenant_id=self.tenant,
            legal_entity_id=self.entity,reviewer_id="REVIEWER-SYN-1",
        )
        case=customer_case(run,ledger)
        case["supplier_id"]='=HYPERLINK("https://malicious.test","click")'
        content,_=render_export(case,"xlsx")
        book=load_workbook(BytesIO(content),read_only=True)
        try:
            cell=book["Differenzfall"]["B4"]
            self.assertEqual(cell.data_type,"s")
            self.assertTrue(cell.value.startswith("'=HYPERLINK"))
        finally:
            book.close()


if __name__=="__main__":
    import unittest
    unittest.main()
