"""Fail-closed signature and scope tests, entirely synthetic."""
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json
import os
from pathlib import Path
import unittest
from unittest.mock import patch

from lowhangingfruitme.approval import (
    issue_approval, key_from_environment, rule_sha256, verify_approval,
)

RULE = json.loads((Path(__file__).parent / "fixtures" / "rule.json").read_text())
KEY = b"synthetic-approval-key-test-only-32"
DOCUMENT_HASH = sha256(b"contract bytes for unit test").hexdigest()


def signed(rule=RULE, **kwargs):
    return issue_approval(
        rule, key=KEY, tenant_id="T-SYN-1", legal_entity_id="LE-SYN-1",
        reviewer_id="REVIEWER-001", reviewer_role="contract_reviewer",
        approval_id="APPROVAL-001", source_revision_id="REV-001",
        document_sha256=DOCUMENT_HASH,
        approved_at=datetime.now(timezone.utc), **kwargs,
    )


def verified(receipt, rule=RULE, **kwargs):
    return verify_approval(receipt, rule, key=KEY, tenant_id="T-SYN-1",
                           legal_entity_id="LE-SYN-1",
                           document_sha256=DOCUMENT_HASH, **kwargs)


class ApprovalTests(unittest.TestCase):
    def test_verifies_real_hmac_and_explicit_reviewer(self):
        record = signed()
        proof = verified(record)
        self.assertEqual(proof["reviewer_id"], "REVIEWER-001")
        self.assertEqual(proof["approval_integrity"], "HMAC_SHA256_VERIFIED")
        self.assertEqual(proof["reviewer_identity_externally_authenticated"],
                         "NOT_VERIFIED_BY_THIS_MODULE")

    def test_rule_amount_change_invalidates_receipt(self):
        rule = deepcopy(RULE)
        rule["rate"] = "0.08"
        with self.assertRaisesRegex(ValueError, "mismatch"):
            verified(signed(), rule=rule)

    def test_rule_revision_change_invalidates_receipt(self):
        rule = deepcopy(RULE)
        rule["revision"] = "2"
        with self.assertRaisesRegex(ValueError, "mismatch"):
            verified(signed(), rule=rule)

    def test_clause_reference_change_invalidates_receipt(self):
        rule = deepcopy(RULE)
        rule["evidence_refs"][0] = "agreement.pdf#page=3"
        with self.assertRaisesRegex(ValueError, "mismatch"):
            verified(signed(), rule=rule)

    def test_signature_tampering_rejected(self):
        receipt = signed()
        receipt["reviewer_id"] = "ANOTHER_REVIEWER"
        with self.assertRaisesRegex(ValueError, "signature"):
            verified(receipt)

    def test_wrong_key_rejected(self):
        with self.assertRaisesRegex(ValueError, "signature"):
            verify_approval(signed(), RULE, key=b"different-synthetic-key-more-than-32",
                            tenant_id="T-SYN-1", legal_entity_id="LE-SYN-1",
                            document_sha256=DOCUMENT_HASH)

    def test_wrong_document_hash_rejected(self):
        with self.assertRaisesRegex(ValueError, "digest mismatch"):
            verify_approval(signed(), RULE, key=KEY,
                            tenant_id="T-SYN-1", legal_entity_id="LE-SYN-1",
                            document_sha256="a" * 64)

    def test_wrong_tenant_rejected(self):
        with self.assertRaisesRegex(ValueError, "mismatch"):
            verify_approval(signed(), RULE, key=KEY,
                            tenant_id="OTHER-TENANT", legal_entity_id="LE-SYN-1",
                            document_sha256=DOCUMENT_HASH)

    def test_wrong_company_rejected(self):
        with self.assertRaisesRegex(ValueError, "mismatch"):
            verify_approval(signed(), RULE, key=KEY,
                            tenant_id="T-SYN-1", legal_entity_id="OTHER-ENTITY",
                            document_sha256=DOCUMENT_HASH)

    def test_unapproved_rule_cannot_be_signed(self):
        rule = deepcopy(RULE)
        rule["approved"] = False
        with self.assertRaisesRegex(ValueError, "non-approved"):
            signed(rule)

    def test_missing_evidence_cannot_be_signed(self):
        rule = deepcopy(RULE)
        rule["evidence_refs"] = []
        with self.assertRaisesRegex(ValueError, "source evidence"):
            signed(rule)

    def test_weak_keys_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "32 secret bytes"):
            issue_approval(RULE, key=b"weak", tenant_id="T", legal_entity_id="LE",
                           reviewer_id="R", approval_id="A", source_revision_id="REV",
                           document_sha256=DOCUMENT_HASH,
                           approved_at=datetime.now(timezone.utc))

    def test_future_date_rejected(self):
        with self.assertRaisesRegex(ValueError, "future"):
            issue_approval(
                RULE, key=KEY, tenant_id="T", legal_entity_id="LE",
                reviewer_id="R", approval_id="A", source_revision_id="REV",
                document_sha256=DOCUMENT_HASH,
                approved_at=datetime.now(timezone.utc) + timedelta(days=1),
            )

    def test_missing_key_does_not_enable_approval(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(RuntimeError, "missing or invalid"):
                key_from_environment()

    def test_extra_field_is_rejected(self):
        receipt = signed()
        receipt["dangerous"] = "payload"
        with self.assertRaisesRegex(ValueError, "unexpected fields"):
            verified(receipt)


if __name__ == "__main__":
    unittest.main()
