"""Frictionless-based CSV import tests with real library, no mocked success path."""
import csv
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import tempfile
import os
from uuid import uuid4
import unittest

from lowhangingfruitme.intake import COLUMNS, audit_from_csv, import_csv
from datetime import datetime, timezone
from hashlib import sha256
from lowhangingfruitme.approval import issue_approval
from lowhangingfruitme.approval_registry import ApprovalRegistry

FIXTURE = json.loads((Path(__file__).parent / "fixtures" / "flat_rebate.json").read_text(encoding="utf-8"))
HAS_FRICTIONLESS = importlib.util.find_spec("frictionless") is not None
CONTROLS = json.loads((Path(__file__).parent / "fixtures" / "source_controls.json").read_text(encoding="utf-8"))


def csv_row(entry, fields):
    return {field: ("true" if entry["posted"] else "false") if field == "posted" else
            entry.get(field, "") or "" for field in fields}


@unittest.skipUnless(HAS_FRICTIONLESS and bool(os.environ.get("LHFM_DB_HOST")), "Frictionless and MariaDB required")
class RealFrictionlessImportTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.contract = self.root / "contract.txt"
        self.contract.write_text("SYNTHETIC R1 AGREEMENT: 2 percent bonus for 2025", encoding="utf-8")
        self.proof_kwargs = {
            "approval_receipt": issue_approval(
                FIXTURE["rule"], key=b"test-approval-key-" * 3,
                tenant_id="T-SYN-1", legal_entity_id="LE-SYN-1",
                reviewer_id="REVIEWER-SYN-1", approval_id="APPROVAL-SYN-" + uuid4().hex,
                source_revision_id="REV-SYN-1",
                document_sha256=sha256(self.contract.read_bytes()).hexdigest(),
                approved_at=datetime.now(timezone.utc),
            ),
            "approval_key": b"test-approval-key-" * 3,
            "approval_scope": {"tenant_id": "T-SYN-1", "legal_entity_id": "LE-SYN-1"},
            "contract_source_path": self.contract,
        }
        self.registry = ApprovalRegistry.from_environment()
        self.proof_kwargs["approval_registry"] = self.registry
        self.registry.register(
            self.proof_kwargs["approval_receipt"],
            rule=FIXTURE["rule"], key=self.proof_kwargs["approval_key"],
            document_sha256=sha256(self.contract.read_bytes()).hexdigest(),
            tenant_id="T-SYN-1", legal_entity_id="LE-SYN-1",
            authenticated_actor_id="REVIEWER-SYN-1",
        )
        self.rule = self.root / "rule.json"
        self.rule.write_text(json.dumps(FIXTURE["rule"]), encoding="utf-8")
        self.purchase = self.root / "transactions.csv"
        self.credit = self.root / "settlements.csv"
        self.write_rows("transactions", self.purchase, FIXTURE["transactions"])
        self.write_rows("settlements", self.credit, FIXTURE["settlements"])

    def write_rows(self, kind, path, entries):
        with path.open("w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=COLUMNS[kind])
            writer.writeheader()
            writer.writerows(csv_row(entry, COLUMNS[kind]) for entry in entries)

    def run_audit(self, completeness=None):
        return audit_from_csv(
            self.rule, self.purchase, self.credit, source_system="erp",
            **self.proof_kwargs, controls=deepcopy(CONTROLS), completeness=completeness or {
                "transactions_complete": True,
                "settlements_complete": True,
                "agreements_complete": True,
            },
        )

    def test_import_real_frictionless_and_full_kernel_path(self):
        report = self.run_audit()
        self.assertEqual(report["status"], "EVIDENCED")
        self.assertTrue(report["audit_executed"])
        self.assertTrue(report["readiness"]["audit_admissible"])
        self.assertEqual(report["approval_verification"]["approval_integrity"], "HMAC_SHA256_VERIFIED")
        self.assertEqual(report["approval_verification"]["revocation_status"], "ACTIVE_LOCKED_AT_DISPATCH")
        self.assertEqual(report["eligible_base_net"], "200000.00")
        self.assertEqual(report["recorded_bonus_net"], "1500.00")
        self.assertEqual(report["difference_net"], "2500.00")
        self.assertEqual(report["fee_due_net"], "0.00")
        self.assertEqual(report["imports"][0]["validation"], "frictionless+kernel")
        self.assertEqual(report["imports"][0]["row_count"], 2)
        self.assertEqual(report["imports"][1]["row_count"], 1)
        self.assertEqual(report["completeness_source"], "operator_assertion_not_independently_verified")

    def test_csv_source_reference_includes_file_hash_and_line(self):
        data = import_csv(self.purchase, "transactions", source_system="erp")
        self.assertTrue(data["entries"][0]["evidence_refs"][0].startswith(
            "sha256:" + data["file_sha256"] + "#row=2"))
        self.assertEqual(data["entries"][1]["evidence_refs"][0].split("#row=")[1], "3")

    def test_incomplete_data_not_implied_complete_by_clean_csv(self):
        report = self.run_audit({
            "transactions_complete": False,
            "settlements_complete": False,
            "agreements_complete": False,
        })
        self.assertEqual(report["status"], "REVIEW_REQUIRED")
        self.assertIn("SOURCE_COMPLETENESS_NOT_ATTESTED", report["warnings"])

    def test_wrong_csv_headers_rejected(self):
        self.purchase.write_text("bad,header\n1,2\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "header mismatch"):
            self.run_audit()

    def test_duplicate_header_rejected(self):
        self.purchase.write_text("external_id,external_id\n1,2\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "duplicate"):
            self.run_audit()

    def test_invalid_amount_rejected_without_repair(self):
        txns = deepcopy(FIXTURE["transactions"])
        txns[0]["amount_net"] = "12.000,99"
        self.write_rows("transactions", self.purchase, txns)
        with self.assertRaisesRegex(ValueError, "invalid decimal"):
            self.run_audit()

    def test_reversal_wrong_sign_rejected(self):
        credits = deepcopy(FIXTURE["settlements"])
        credits[0]["kind"] = "REVERSAL"
        self.write_rows("settlements", self.credit, credits)
        with self.assertRaisesRegex(ValueError, "negative amount"):
            self.run_audit()

    def test_duplicate_identity_rejected(self):
        txns = deepcopy(FIXTURE["transactions"])
        txns.append(deepcopy(txns[0]))
        self.write_rows("transactions", self.purchase, txns)
        with self.assertRaisesRegex(ValueError, "duplicate external identity"):
            self.run_audit()

    def test_boolean_string_rejected(self):
        txns = deepcopy(FIXTURE["transactions"])
        txns[0]["posted"] = "YES"
        self.write_rows("transactions", self.purchase, txns)
        # This helper converts truthy values to "true"; write a raw value.
        text = self.purchase.read_text(encoding="utf-8").replace(",true,INVOICE", ",YES,INVOICE", 1)
        self.purchase.write_text(text, encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "posted must be true/false"):
            self.run_audit()

    def test_partial_settlement_without_period_is_not_matched(self):
        credits = deepcopy(FIXTURE["settlements"])
        credits[0]["period_start"] = ""
        credits[0]["period_end"] = ""
        self.write_rows("settlements", self.credit, credits)
        report = self.run_audit()
        self.assertFalse(report["audit_executed"])
        self.assertIsNone(report["recorded_bonus_net"])
        self.assertIn("UNALLOCATED_OR_OUTSIDE_SCOPE", report["warnings"])

    def test_no_control_totals_produce_diagnostics_not_claim(self):
        report = audit_from_csv(
            self.rule, self.purchase, self.credit, source_system="erp",
            **self.proof_kwargs, completeness={"transactions_complete": True,
                          "settlements_complete": True,
                          "agreements_complete": True},
        )
        self.assertFalse(report["audit_executed"])
        self.assertEqual(report["status"], "REVIEW_REQUIRED")
        self.assertIsNone(report["difference_net"])
        self.assertIn("SOURCE_CONTROLS_MISSING", report["warnings"])

    def test_reconciliation_mismatch_prevents_calculation(self):
        controls = deepcopy(CONTROLS)
        controls["transactions"]["net_total"] = "999999.00"
        report = audit_from_csv(
            self.rule, self.purchase, self.credit, source_system="erp",
            **self.proof_kwargs, controls=controls,
            completeness={"transactions_complete": True,
                          "settlements_complete": True,
                          "agreements_complete": True},
        )
        self.assertFalse(report["audit_executed"])
        self.assertEqual(report["status"], "NOT_CALCULABLE")
        self.assertIsNone(report["expected_bonus_net"])
        self.assertIsNone(report["difference_net"])
        self.assertEqual(report["fee_due_net"], "0.00")
        self.assertIn("NET_TOTAL_MISMATCH", report["warnings"])

    def test_revoked_registered_receipt_blocks_audit(self):
        self.assertTrue(self.registry.revoke(
            self.proof_kwargs["approval_receipt"]["approval_id"],
            tenant_id="T-SYN-1", legal_entity_id="LE-SYN-1",
            authenticated_actor_id="REVIEWER-SYN-1"))
        report = self.run_audit()
        self.assertFalse(report["audit_executed"])
        self.assertIsNone(report["difference_net"])
        self.assertIn("APPROVAL_NOT_ACTIVE_AT_DISPATCH", report["warnings"])

    def test_unregistered_context_blocks_even_signed_receipt(self):
        proof = dict(self.proof_kwargs)
        del proof["approval_registry"]
        report = audit_from_csv(
            self.rule, self.purchase, self.credit, source_system="erp",
            controls=deepcopy(CONTROLS), **proof,
            completeness={"transactions_complete": True,
                          "settlements_complete": True, "agreements_complete": True},
        )
        self.assertFalse(report["audit_executed"])
        self.assertIn("APPROVAL_REGISTRY_UNAVAILABLE", report["warnings"])

    def test_forged_true_flag_without_receipt_cannot_run_audit(self):
        report = audit_from_csv(
            self.rule, self.purchase, self.credit, source_system="erp",
            completeness={"transactions_complete": True, "settlements_complete": True,
                          "agreements_complete": True},
            controls=deepcopy(CONTROLS),
        )
        self.assertFalse(report["audit_executed"])
        self.assertIsNone(report["difference_net"])
        self.assertIn("APPROVAL_RECEIPT_MISSING", report["warnings"])

    def test_changed_contract_file_prevents_calculation(self):
        self.contract.write_text("REPLACED CONTRACT CONTENT", encoding="utf-8")
        report = self.run_audit()
        self.assertFalse(report["audit_executed"])
        self.assertIn("APPROVAL_INVALID", report["warnings"])

    def test_tampered_signed_rate_does_not_pass(self):
        json_rule = json.loads(self.rule.read_text(encoding="utf-8"))
        json_rule["rate"] = "0.03"
        self.rule.write_text(json.dumps(json_rule), encoding="utf-8")
        report = self.run_audit()
        self.assertFalse(report["audit_executed"])
        self.assertIn("APPROVAL_INVALID", report["warnings"])

    def test_wrong_tenant_cannot_reuse_receipt(self):
        self.proof_kwargs["approval_scope"] = {
            "tenant_id": "OTHER-TENANT", "legal_entity_id": "LE-SYN-1",
        }
        report = self.run_audit()
        self.assertFalse(report["audit_executed"])
        self.assertIn("APPROVAL_INVALID", report["warnings"])

    def test_false_completeness_structure_rejected(self):
        with self.assertRaisesRegex(ValueError, "explicit boolean"):
            self.run_audit({"transactions_complete": True})


if __name__ == "__main__":
    unittest.main()
