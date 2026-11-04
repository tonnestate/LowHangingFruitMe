"""Real MariaDB contract for bounded expired upload cleanup; no customer files."""
from __future__ import annotations

from hashlib import sha256
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import time
import unittest
from unittest.mock import patch
from uuid import uuid4

from lowhangingfruitme.approval_registry import ApprovalRegistry
from lowhangingfruitme.upload_housekeeping import (
    HousekeepingBlocked, prune_stale_uploads,
)

SCOPED = ("T-HOUSEKEEPING-SYN", "LE-HOUSEKEEPING-SYN", "REVIEWER-HOUSEKEEPING-SYN")
CONFIRMED = {
    "LHFM_UPLOAD_HOUSEKEEPING_APPROVED": "YES",
    "LHFM_UPLOAD_WRITES_STOPPED": "YES",
}


@unittest.skipUnless(
    bool(os.environ.get("LHFM_DB_HOST")) and os.geteuid() != 0,
    "real MariaDB and unprivileged test process required",
)
class StaleUploadHousekeepingTests(unittest.TestCase):
    def setUp(self):
        temp = TemporaryDirectory(prefix="lhfm-housekeeping-test-")
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name) / "uploads"
        self.root.mkdir(mode=0o700)
        self.registry = ApprovalRegistry.from_environment()
        self.conn = self.registry._connect
        self.upload_ids: list[str] = []
        self.addCleanup(self._clean_rows)

    def _clean_rows(self):
        if not self.upload_ids:
            return
        db = self.conn()
        try:
            with db.cursor() as cursor:
                for upload_id in self.upload_ids:
                    cursor.execute(
                        "DELETE FROM lhfm_upload_housekeeping_events WHERE upload_id=%s",
                        (upload_id,),
                    )
                    cursor.execute(
                        "DELETE FROM lhfm_uploads WHERE upload_id=%s",
                        (upload_id,),
                    )
            db.commit()
        finally:
            db.close()

    def _upload(self, *, state="RECEIVING", expired_hours=48) -> str:
        upload_id = str(uuid4())
        payload = b"synthetic-incomplete-test-only"
        db = self.conn()
        try:
            with db.cursor() as cursor:
                cursor.execute(
                    """INSERT INTO lhfm_uploads
                       (upload_id,tenant_id,legal_entity_id,reviewer_id,kind,
                        expected_size,expected_sha256,state,expires_at)
                       VALUES (%s,%s,%s,%s,'ERP_CSV',%s,%s,%s,
                           DATE_SUB(UTC_TIMESTAMP(6), INTERVAL %s HOUR))""",
                    (upload_id, *SCOPED, len(payload),
                     sha256(payload).hexdigest(), state, expired_hours),
                )
            db.commit()
            self.upload_ids.append(upload_id)
        finally:
            db.close()
        return upload_id

    def _partial(self, upload_id: str, *, age_hours=48, inspect=False) -> Path:
        path = self.root / (upload_id + ".part")
        path.write_bytes(b"synthetic-aborted-partial-only")
        path.chmod(0o600)
        old = time.time() - age_hours * 3600
        os.utime(path, times=(old, old))
        if inspect:
            (self.root / (upload_id + ".inspect.csv")).hardlink_to(path)
        return path

    def _state(self, upload_id: str) -> str:
        db = self.conn()
        try:
            with db.cursor() as cursor:
                cursor.execute("SELECT state FROM lhfm_uploads WHERE upload_id=%s",
                               (upload_id,))
                return cursor.fetchone()["state"]
        finally:
            db.close()

    def _events(self, upload_id: str):
        db = self.conn()
        try:
            with db.cursor() as cursor:
                cursor.execute(
                    "SELECT prior_state,removed_partials FROM "
                    "lhfm_upload_housekeeping_events WHERE upload_id=%s",
                    (upload_id,),
                )
                return list(cursor.fetchall())
        finally:
            db.close()

    def _run(self, *, apply=False, limit=100, approvals=None):
        return prune_stale_uploads(
            connect=self.conn, upload_root=self.root, apply=apply,
            limit=limit, approvals=approvals or {},
        )

    def test_dry_run_is_read_only_and_never_unlinks(self):
        old = self._upload()
        part = self._partial(old)
        result = self._run()
        self.assertEqual(result["mode"], "dry_run")
        self.assertEqual(result["stale_intents"], 1)
        self.assertEqual(result["partial_files"], 1)
        self.assertTrue(part.is_file())
        self.assertEqual(self._state(old), "RECEIVING")
        self.assertEqual(self._events(old), [])

    def test_unapproved_apply_fails_before_loading_database_rows(self):
        old = self._upload()
        part = self._partial(old)
        for grant in (
            {}, {"LHFM_UPLOAD_HOUSEKEEPING_APPROVED": "YES"},
            {"LHFM_UPLOAD_WRITES_STOPPED": "YES"},
        ):
            with self.subTest(grant=grant):
                with self.assertRaisesRegex(HousekeepingBlocked, "operator approval"):
                    self._run(apply=True, approvals=grant)
        self.assertTrue(part.exists())
        self.assertEqual(self._state(old), "RECEIVING")

    def test_apply_rejects_expired_intent_and_writes_immutable_event(self):
        receiving = self._upload()
        pending = self._upload(state="PENDING")
        part = self._partial(receiving, inspect=True)
        inspected = self.root / (receiving + ".inspect.csv")
        result = self._run(apply=True, approvals=CONFIRMED)
        self.assertEqual(result["mode"], "applied")
        self.assertEqual(result["stale_intents"], 2)
        self.assertEqual(result["partial_files"], 2)
        self.assertFalse(part.exists())
        self.assertFalse(inspected.exists())
        self.assertEqual(self._state(receiving), "REJECTED")
        self.assertEqual(self._state(pending), "REJECTED")
        self.assertEqual(
            [(v["prior_state"], v["removed_partials"]) for v in self._events(receiving)],
            [("RECEIVING", 2)],
        )
        self.assertEqual(
            [(v["prior_state"], v["removed_partials"]) for v in self._events(pending)],
            [("PENDING", 0)],
        )
        replay = self._run(apply=True, approvals=CONFIRMED)
        self.assertEqual(replay["stale_intents"], 0)
        self.assertEqual(self._events(receiving)[0]["removed_partials"], 2)

    def test_clean_rejected_and_recent_uploads_are_never_touched(self):
        clean = self._upload(state="CLEAN")
        rejected = self._upload(state="REJECTED")
        recent = self._upload(expired_hours=1)
        for upload_id in (clean, rejected, recent):
            (self.root / (upload_id + ".csv")).write_bytes(b"protected-content")
        result = self._run(apply=True, approvals=CONFIRMED)
        self.assertEqual(result["stale_intents"], 0)
        for upload_id, state in ((clean,"CLEAN"),(rejected,"REJECTED"),(recent,"RECEIVING")):
            self.assertEqual(self._state(upload_id), state)
            self.assertTrue((self.root / (upload_id + ".csv")).exists())
            self.assertEqual(self._events(upload_id), [])

    def test_recently_written_partial_is_skipped_even_on_expired_row(self):
        old = self._upload()
        part = self._partial(old, age_hours=0)
        result = self._run(apply=True, approvals=CONFIRMED)
        self.assertEqual(result["stale_intents"], 0)
        self.assertEqual(result["recent_partial_files_skipped"], 1)
        self.assertEqual(self._state(old), "RECEIVING")
        self.assertTrue(part.exists())

    def test_final_file_is_ambiguous_and_requires_manual_reconciliation(self):
        old = self._upload()
        part = self._partial(old)
        final = self.root / (old + ".csv")
        final.write_bytes(b"possibly-validated-before-worker-crash")
        with self.assertRaisesRegex(HousekeepingBlocked, "ambiguous final"):
            self._run(apply=True, approvals=CONFIRMED)
        self.assertTrue(final.exists())
        self.assertTrue(part.exists())
        self.assertEqual(self._state(old), "RECEIVING")

    def test_symlink_partial_and_unaccounted_hardlink_are_denied(self):
        old = self._upload()
        path = self.root / (old + ".part")
        path.symlink_to("/etc/passwd")
        with self.assertRaisesRegex(HousekeepingBlocked, "unsafe partial"):
            self._run(apply=True, approvals=CONFIRMED)
        self.assertEqual(self._state(old), "RECEIVING")
        path.unlink()
        original = self._partial(old)
        other = self.root / "synthetic-hardlink"
        other.hardlink_to(original)
        with self.assertRaisesRegex(HousekeepingBlocked, "unaccounted hard link"):
            self._run(apply=True, approvals=CONFIRMED)
        self.assertTrue(original.exists())
        self.assertTrue(other.exists())
        self.assertEqual(self._state(old), "RECEIVING")

    def test_private_root_requires_mode_0700(self):
        self.root.chmod(0o755)
        with self.assertRaisesRegex(HousekeepingBlocked, "not owned"):
            self._run()
        self.root.chmod(0o700)

    def test_bounded_batch_and_idempotent_retry(self):
        first = self._upload(state="PENDING")
        second = self._upload(state="PENDING")
        third = self._upload(state="PENDING")
        result = self._run(apply=True, approvals=CONFIRMED, limit=2)
        self.assertEqual(result["stale_intents"], 2)
        self.assertEqual([self._state(n) for n in (first,second,third)].count("REJECTED"),2)
        result2 = self._run(apply=True, approvals=CONFIRMED, limit=2)
        self.assertEqual(result2["stale_intents"],1)
        self.assertEqual([self._state(n) for n in (first,second,third)].count("REJECTED"),3)
        with self.assertRaisesRegex(HousekeepingBlocked, "between 1 and 100"):
            self._run(limit=0)
        with self.assertRaisesRegex(HousekeepingBlocked, "between 1 and 100"):
            self._run(limit=101)


if __name__ == "__main__":
    unittest.main()
