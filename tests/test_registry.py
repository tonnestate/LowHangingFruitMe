"""MariaDB-backed approval and revocation integration tests (synthetic only)."""
import json
import os
import threading
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
import unittest
from uuid import uuid4

from lowhangingfruitme.approval import issue_approval
from lowhangingfruitme.approval_registry import ApprovalRegistry

RULE = json.loads((Path(__file__).parent / "fixtures" / "rule.json").read_text())
KEY = b"synthetic-registry-test-key-must-remain-private"
DOCUMENT_SHA = sha256(b"synthetic contract revision").hexdigest()
SCOPE = {"tenant_id": "T-SYN-1", "legal_entity_id": "LE-SYN-1"}


@unittest.skipUnless(bool(os.environ.get("LHFM_DB_HOST")), "real MariaDB service required")
class MariaDBRegistryTests(unittest.TestCase):
    def setUp(self):
        self.registry = ApprovalRegistry.from_environment()
        self.receipt = issue_approval(
            RULE, key=KEY, **SCOPE, reviewer_id="REVIEWER-SYN-1",
            approval_id="REGTEST-" + uuid4().hex,
            source_revision_id="REV-SYNTHETIC", document_sha256=DOCUMENT_SHA,
            approved_at=datetime.now(timezone.utc),
        )

    def register(self, actor="REVIEWER-SYN-1"):
        self.registry.register(
            self.receipt, rule=RULE, key=KEY,
            document_sha256=DOCUMENT_SHA, **SCOPE,
            authenticated_actor_id=actor,
        )

    def guard(self):
        return self.registry.guard(
            self.receipt, rule=RULE, key=KEY,
            document_sha256=DOCUMENT_SHA, **SCOPE,
        )

    def test_registered_approval_allows_guard(self):
        self.register()
        with self.guard() as record:
            self.assertEqual(record["revocation_status"], "ACTIVE_LOCKED_AT_DISPATCH")

    def test_unknown_signed_approval_is_rejected(self):
        with self.assertRaisesRegex(PermissionError, "missing or revoked"):
            with self.guard():
                pass

    def test_actor_mismatch_denied(self):
        with self.assertRaisesRegex(PermissionError, "reviewer differs"):
            self.register(actor="UNRELATED-ACTOR")

    def test_duplicate_approval_id_denied(self):
        self.register()
        with self.assertRaises(Exception):
            self.register()
        with self.guard():
            pass

    def test_wrong_tenant_cannot_revoke(self):
        self.register()
        with self.assertRaisesRegex(ValueError, "not found"):
            self.registry.revoke(
                self.receipt["approval_id"], tenant_id="OTHER-TENANT",
                legal_entity_id=SCOPE["legal_entity_id"],
                authenticated_actor_id="REVIEWER-SYN-1",
            )
        with self.guard():
            pass

    def test_revoke_is_atomic_and_idempotent(self):
        self.register()
        args = {**SCOPE, "authenticated_actor_id": "REVIEWER-SYN-1"}
        self.assertTrue(self.registry.revoke(self.receipt["approval_id"], **args))
        self.assertFalse(self.registry.revoke(self.receipt["approval_id"], **args))
        with self.assertRaisesRegex(PermissionError, "revoked"):
            with self.guard():
                pass

    def test_concurrent_revoke_cannot_commit_during_guard(self):
        self.register()
        started = threading.Event()
        completed = threading.Event()
        errors = []

        def revoke():
            started.set()
            try:
                self.registry.revoke(
                    self.receipt["approval_id"], **SCOPE,
                    authenticated_actor_id="REVIEWER-SYN-1",
                )
            except Exception as exc:
                errors.append(exc)
            finally:
                completed.set()

        with self.guard():
            thread = threading.Thread(target=revoke, daemon=True)
            thread.start()
            self.assertTrue(started.wait(timeout=2))
            self.assertFalse(completed.wait(timeout=0.25))
        self.assertTrue(completed.wait(timeout=5))
        thread.join(timeout=2)
        self.assertEqual(errors, [])
        with self.assertRaises(PermissionError):
            with self.guard():
                pass


if __name__ == "__main__":
    unittest.main()
