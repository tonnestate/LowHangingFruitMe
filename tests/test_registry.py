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
        with self.assertRaisesRegex(PermissionError, "superseded or has no reviewed lineage"):
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

    def test_new_contract_revision_supersedes_old_in_same_scope(self):
        self.register()
        old_id = self.receipt["approval_id"]
        revised = {**RULE, "revision": "2", "rate": "0.03"}
        new_document = sha256(b"synthetic replacement contract").hexdigest()
        successor = issue_approval(
            revised, key=KEY, **SCOPE, reviewer_id="REVIEWER-SYN-1",
            approval_id="REGTEST-" + uuid4().hex,
            source_revision_id="REV-SECOND", document_sha256=new_document,
            approved_at=datetime.now(timezone.utc),
        )
        self.registry.register(
            successor, rule=revised, key=KEY, document_sha256=new_document,
            **SCOPE, authenticated_actor_id="REVIEWER-SYN-1",
        )
        with self.assertRaisesRegex(PermissionError, "superseded"):
            with self.guard():
                pass
        with self.registry.guard(
            successor, rule=revised, key=KEY,
            document_sha256=new_document, **SCOPE,
            acting_reviewer_id="REVIEWER-SYN-1",
        ) as verified:
            self.assertEqual(verified["rule_lifecycle"], "CURRENT_APPROVED_REVISION")
        db = self.registry._connect()
        try:
            with db.cursor() as cur:
                cur.execute(
                    """SELECT state, superseded_by FROM lhfm_approval_records
                       WHERE approval_id=%s""", (old_id,),
                )
                old = cur.fetchone()
                self.assertEqual(old["state"], "REVOKED")
                self.assertEqual(old["superseded_by"], successor["approval_id"])
                cur.execute(
                    """SELECT event_type FROM lhfm_rule_revision_events
                       WHERE approval_id=%s ORDER BY event_id""",
                    (old_id,),
                )
                self.assertEqual(
                    [event["event_type"] for event in cur.fetchall()],
                    ["APPROVED", "SUPERSEDED"],
                )
        finally:
            db.close()
        self.assertTrue(self.registry.revoke(
            successor["approval_id"], **SCOPE,
            authenticated_actor_id="REVIEWER-SYN-1",
        ))
        with self.assertRaises(PermissionError):
            with self.registry.guard(
                successor, rule=revised, key=KEY,
                document_sha256=new_document, **SCOPE,
            ):
                pass

    def test_supersession_waits_for_current_audit_guard(self):
        self.register()
        started = threading.Event()
        completed = threading.Event()
        errors = []

        def replace_rule():
            revised = {**RULE, "revision": "2"}
            replacement = issue_approval(
                revised, key=KEY, **SCOPE, reviewer_id="REVIEWER-SYN-1",
                approval_id="REGTEST-" + uuid4().hex,
                source_revision_id="REV-SECOND",
                document_sha256=DOCUMENT_SHA,
                approved_at=datetime.now(timezone.utc),
            )
            started.set()
            try:
                self.registry.register(
                    replacement, rule=revised, key=KEY,
                    document_sha256=DOCUMENT_SHA, **SCOPE,
                    authenticated_actor_id="REVIEWER-SYN-1",
                )
            except Exception as exc:
                errors.append(exc)
            finally:
                completed.set()

        with self.guard():
            thread = threading.Thread(target=replace_rule, daemon=True)
            thread.start()
            self.assertTrue(started.wait(timeout=2))
            self.assertFalse(completed.wait(timeout=0.25))
        self.assertTrue(completed.wait(timeout=5))
        thread.join(timeout=2)
        self.assertEqual(errors, [])
        with self.assertRaises(PermissionError):
            with self.guard():
                pass


    def test_revoke_waits_for_lineage_head_lock(self):
        """Revocation must not overtake a concurrent rule-head operation."""
        self.register()
        locked = threading.Event()
        attempted = threading.Event()
        finished = threading.Event()
        errors = []
        results = []

        db = self.registry._connect()
        def revoke_while_head_is_locked():
            attempted.set()
            try:
                results.append(self.registry.revoke(
                    self.receipt["approval_id"], **SCOPE,
                    authenticated_actor_id="REVIEWER-SYN-1",
                ))
            except Exception as exc:
                errors.append(exc)
            finally:
                finished.set()

        try:
            with db.cursor() as cur:
                cur.execute(
                    """SELECT current_approval_id FROM lhfm_rule_heads
                       WHERE tenant_id=%s AND legal_entity_id=%s
                         AND agreement_id=%s AND rule_id=%s FOR UPDATE""",
                    (SCOPE["tenant_id"], SCOPE["legal_entity_id"],
                     RULE["agreement_id"], RULE["rule_id"]),
                )
                self.assertEqual(
                    cur.fetchone()["current_approval_id"],
                    self.receipt["approval_id"],
                )
                locked.set()
                thread = threading.Thread(
                    target=revoke_while_head_is_locked, daemon=True,
                )
                thread.start()
                self.assertTrue(attempted.wait(timeout=2))
                # The approval row is not locked here: an implementation
                # that wrongly starts with the approval lock would succeed.
                self.assertFalse(finished.wait(timeout=0.3))
            db.commit()
            self.assertTrue(finished.wait(timeout=5), "possible lock deadlock")
            thread.join(timeout=2)
            self.assertEqual(errors, [])
            self.assertEqual(results, [True])
        finally:
            db.rollback()
            db.close()

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
