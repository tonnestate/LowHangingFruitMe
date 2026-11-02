"""Independent readiness gate contract tests, all using synthetic data."""
from copy import deepcopy
import json
from pathlib import Path
import unittest

from lowhangingfruitme.readiness import assess_readiness

BASE = json.loads((Path(__file__).parent / "fixtures" / "flat_rebate.json").read_text())
CONTROLS = json.loads((Path(__file__).parent / "fixtures" / "source_controls.json").read_text())


def assess(base=None, controls=CONTROLS):
    payload = deepcopy(BASE if base is None else base)
    return assess_readiness(payload["rule"], payload["transactions"],
                            payload["settlements"], payload["completeness"], controls)


class ReadinessTests(unittest.TestCase):
    def test_ready_when_two_separately_asserted_control_totals_match(self):
        result = assess()
        self.assertEqual(result["status"], "READY_FOR_AUDIT")
        self.assertTrue(result["audit_admissible"])
        self.assertFalse(result["external_ledger_completeness_proven"])
        self.assertEqual(result["reconciliation"]["transactions"]["actual_net_total"], "200000.00")

    def test_controls_missing_produces_limited_not_automatically_evidenced(self):
        result = assess(controls=None)
        self.assertEqual(result["status"], "LIMITED")
        self.assertFalse(result["audit_admissible"])
        self.assertIn("SOURCE_CONTROLS_MISSING", [i["code"] for i in result["issues"]])

    def test_one_amount_mismatch_blocks_audit(self):
        controls = deepcopy(CONTROLS)
        controls["transactions"]["net_total"] = "200000.01"
        result = assess(controls=controls)
        self.assertEqual(result["status"], "NOT_READY")
        self.assertIn("NET_TOTAL_MISMATCH", [i["code"] for i in result["issues"]])

    def test_source_count_mismatch_blocks(self):
        controls = deepcopy(CONTROLS)
        controls["settlements"]["row_count"] = 2
        self.assertIn("ROW_COUNT_MISMATCH", [i["code"] for i in assess(controls=controls)["issues"]])

    def test_unapproved_rule_blocks_even_with_matching_control_totals(self):
        payload = deepcopy(BASE)
        payload["rule"]["approved"] = False
        self.assertEqual(assess(payload)["status"], "NOT_READY")

    def test_missing_contract_source_blocks(self):
        payload = deepcopy(BASE)
        payload["rule"]["evidence_refs"] = []
        self.assertEqual(assess(payload)["status"], "NOT_READY")

    def test_unallocated_credit_blocks(self):
        payload = deepcopy(BASE)
        payload["settlements"][0]["agreement_id"] = None
        self.assertIn("UNALLOCATED_OR_OUTSIDE_SCOPE", [i["code"] for i in assess(payload)["issues"]])

    def test_other_supplier_rejected_without_silent_merge(self):
        payload = deepcopy(BASE)
        payload["transactions"][0]["supplier_id"] = "SUP-2"
        self.assertIn("MIXED_SUPPLIER_OR_CURRENCY", [i["code"] for i in assess(payload)["issues"]])

    def test_correction_outside_year_blocks(self):
        payload = deepcopy(BASE)
        payload["transactions"][0]["date"] = "2026-01-01"
        self.assertIn("UNALLOCATED_OR_OUTSIDE_SCOPE", [i["code"] for i in assess(payload)["issues"]])

    def test_no_purchases_blocks(self):
        payload = deepcopy(BASE)
        payload["transactions"] = []
        self.assertIn("NO_PURCHASE_ROWS", [i["code"] for i in assess(payload)["issues"]])

    def test_false_customer_completeness_flag_downgrades_not_overrides_controls(self):
        payload = deepcopy(BASE)
        payload["completeness"]["transactions_complete"] = False
        self.assertEqual(assess(payload)["status"], "LIMITED")

    def test_invalid_control_amount_and_types_rejected(self):
        controls = deepcopy(CONTROLS)
        controls["transactions"]["net_total"] = 200000.0
        with self.assertRaisesRegex(ValueError, "never a float"):
            assess(controls=controls)
        controls = deepcopy(CONTROLS)
        controls["transactions"]["row_count"] = True
        with self.assertRaisesRegex(ValueError, "nonnegative integer"):
            assess(controls=controls)

    def test_attested_source_report_scope_must_match_contract(self):
        controls = deepcopy(CONTROLS)
        controls["period_end"] = "2024-12-31"
        self.assertIn("CONTROL_SCOPE_MISMATCH", [i["code"] for i in assess(controls=controls)["issues"]])

    def test_deterministic_hash_and_no_percentage_fiction(self):
        self.assertEqual(assess()["gate_snapshot_sha256"], assess()["gate_snapshot_sha256"])
        self.assertIsNone(assess()["automated_percentage_score"])

    def test_unposted_purchase_blocks(self):
        payload = deepcopy(BASE)
        payload["transactions"][0]["posted"] = False
        self.assertIn("UNPOSTED_INPUT_ROWS", [i["code"] for i in assess(payload)["issues"]])


if __name__ == "__main__":
    unittest.main()
