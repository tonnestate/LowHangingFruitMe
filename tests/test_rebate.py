"""Synthetic reproducible tests for spec docs/API_AND_DATA.md, section 9."""
from copy import deepcopy
from decimal import Decimal
import json
from pathlib import Path
import unittest

from lowhangingfruitme import audit

BASE = json.loads((Path(__file__).parent / "fixtures" / "flat_rebate.json").read_text(encoding="utf-8"))


def settlement(external_id="CREDIT-2", amount="1000.00", **changes):
    row = deepcopy(BASE["settlements"][0])
    row.update(external_id=external_id, amount_net=amount)
    row.update(changes)
    return row


class RebateEngineTests(unittest.TestCase):
    def test_f01_flat_rate_and_return_and_credit(self):
        result = audit(BASE)
        self.assertEqual(result["status"], "EVIDENCED")
        self.assertEqual(result["eligible_base_net"], "200000.00")
        self.assertEqual(result["expected_bonus_net"], "4000.00")
        self.assertEqual(result["recorded_bonus_net"], "1500.00")
        self.assertEqual(result["difference_net"], "2500.00")
        self.assertEqual(result["fee_due_net"], "0.00")
        self.assertFalse(result["legal_claim_confirmed"])

    def test_f02_retroactive_and_marginal_are_not_interchangeable(self):
        for kind, expected in (("RETROACTIVE_FULL_BASE", "2000.00"), ("MARGINAL_PER_TIER", "400.00")):
            with self.subTest(kind=kind):
                payload = deepcopy(BASE)
                payload["transactions"] = [payload["transactions"][0]]
                payload["transactions"][0]["amount_net"] = "100000.00"
                payload["settlements"] = []
                payload["rule"].pop("rate")
                payload["rule"]["kind"] = kind
                payload["rule"]["tiers"] = [{"threshold":"80000.00", "rate":"0.02"}]
                self.assertEqual(audit(payload)["expected_bonus_net"], expected)

    def test_fixed_reward(self):
        payload = deepcopy(BASE)
        payload["rule"].pop("rate")
        payload["rule"]["kind"] = "FIXED_THRESHOLD_REWARD"
        payload["rule"]["tiers"] = [{"threshold":"150000", "reward":"500"}]
        self.assertEqual(audit(payload)["expected_bonus_net"], "500.00")

    def test_missing_threshold_semantics_is_rejected(self):
        payload = deepcopy(BASE)
        payload["rule"]["kind"] = "MARGINAL_PER_TIER"
        with self.assertRaises(ValueError):
            audit(payload)

    def test_f05_duplicate_input_is_idempotent(self):
        payload = deepcopy(BASE)
        payload["transactions"].append(deepcopy(payload["transactions"][0]))
        payload["settlements"].append(deepcopy(payload["settlements"][0]))
        self.assertEqual(audit(payload)["difference_net"], "2500.00")
        self.assertEqual(audit(payload)["input_snapshot_sha256"], audit(BASE)["input_snapshot_sha256"])

    def test_duplicate_identity_conflicting_amount_rejected(self):
        payload = deepcopy(BASE)
        wrong = deepcopy(payload["transactions"][0])
        wrong["amount_net"] = "90000.00"
        payload["transactions"].append(wrong)
        with self.assertRaisesRegex(ValueError, "conflicting transaction"):
            audit(payload)

    def test_f07_incomplete_period_never_evidenced(self):
        payload = deepcopy(BASE)
        payload["completeness"]["transactions_complete"] = False
        result = audit(payload)
        self.assertEqual(result["status"], "REVIEW_REQUIRED")
        self.assertIn("TRANSACTIONS_INCOMPLETE", result["warnings"])

    def test_unallocated_gutschrift_not_silently_assigned(self):
        payload = deepcopy(BASE)
        row = settlement(agreement_id=None, period_start=None, period_end=None)
        payload["settlements"].append(row)
        result = audit(payload)
        self.assertEqual(result["recorded_bonus_net"], "1500.00")
        self.assertEqual(result["status"], "REVIEW_REQUIRED")
        self.assertIn("UNALLOCATED_SETTLEMENT", result["warnings"])

    def test_cross_supplier_is_excluded(self):
        payload = deepcopy(BASE)
        row = deepcopy(payload["transactions"][0])
        row.update(external_id="INV-2", supplier_id="SUP-2", amount_net="900000.00")
        payload["transactions"].append(row)
        self.assertEqual(audit(payload)["eligible_base_net"], "200000.00")

    def test_mixed_currency_refuses_automatic_calculation(self):
        payload = deepcopy(BASE)
        row = deepcopy(payload["transactions"][0])
        row.update(external_id="INV-USD", currency="USD")
        payload["transactions"].append(row)
        result = audit(payload)
        self.assertEqual(result["status"], "NOT_CALCULABLE")
        self.assertIsNone(result["expected_bonus_net"])

    def test_negative_credit_reversal_netting(self):
        payload = deepcopy(BASE)
        payload["settlements"].append(settlement(external_id="REV-1", kind="REVERSAL", amount_net="-500.00"))
        result = audit(payload)
        self.assertEqual(result["recorded_bonus_net"], "1000.00")
        self.assertEqual(result["difference_net"], "3000.00")

    def test_unapproved_rule_blocks_evidenced(self):
        payload = deepcopy(BASE)
        payload["rule"]["approved"] = False
        self.assertEqual(audit(payload)["status"], "REVIEW_REQUIRED")

    def test_rule_requires_citation_and_evidence_on_transactions(self):
        payload = deepcopy(BASE)
        payload["rule"]["evidence_refs"] = []
        self.assertIn("MISSING_SOURCE_EVIDENCE", audit(payload)["warnings"])

    def test_f06_order_independence_and_hash(self):
        payload = deepcopy(BASE)
        payload["transactions"].reverse()
        self.assertEqual(audit(BASE), audit(payload))

    def test_float_precision_is_forbidden(self):
        payload = deepcopy(BASE)
        payload["transactions"][0]["amount_net"] = 210000.0
        with self.assertRaisesRegex(ValueError, "never a float"):
            audit(payload)

    def test_nonfinite_is_rejected(self):
        payload = deepcopy(BASE)
        payload["rule"]["rate"] = "NaN"
        with self.assertRaisesRegex(ValueError, "finite"):
            audit(payload)

    def test_rate_rounding_half_up(self):
        payload = deepcopy(BASE)
        payload["transactions"] = [payload["transactions"][0]]
        payload["transactions"][0]["amount_net"] = "1.00"
        payload["rule"]["rate"] = "0.005"
        payload["settlements"] = []
        self.assertEqual(audit(payload)["expected_bonus_net"], "0.01")

    def test_ambiguous_credit_without_period_does_not_count(self):
        payload = deepcopy(BASE)
        payload["settlements"].append(settlement(external_id="CREDIT-4", period_start=None, period_end=None))
        self.assertIn("UNALLOCATED_SETTLEMENT", audit(payload)["warnings"])

    def test_conflicting_tiers_rejected(self):
        payload = deepcopy(BASE)
        payload["rule"].pop("rate")
        payload["rule"]["kind"] = "RETROACTIVE_FULL_BASE"
        payload["rule"]["tiers"] = [{"threshold":"0", "rate":"0.01"}, {"threshold":"0", "rate":"0.02"}]
        with self.assertRaisesRegex(ValueError, "strictly increasing"):
            audit(payload)


if __name__ == "__main__":
    unittest.main()
