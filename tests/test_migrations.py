"""Operator migration plan: checksum drift, partial DDL and real CI database."""
from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import os
import unittest

from lowhangingfruitme.migrations import (
    MigrationError, load_migrations, split_statements, verify_history,
    migrate_database,
)

SQL = Path(__file__).parent.parent / "sql"


class MigrationSafetyUnitTests(unittest.TestCase):
    def test_all_reviewed_sql_scripts_load(self):
        migrations = load_migrations(SQL)
        self.assertEqual([x.number for x in migrations], list(range(1, 9)))
        self.assertTrue(all(x.statements for x in migrations))

    def test_reject_non_ddl_statements(self):
        with self.assertRaisesRegex(MigrationError, "CREATE/ALTER"):
            split_statements("DELETE FROM customers;")

    def test_reject_empty_and_client_directive(self):
        with self.assertRaises(MigrationError):
            split_statements("-- comment only")
        with self.assertRaises(MigrationError):
            split_statements("DELIMITER $$")

    def test_empty_history_means_all_pending(self):
        scripts = load_migrations(SQL)
        self.assertEqual(verify_history([], scripts), 0)

    def test_valid_prefix_does_not_suggest_downgrade(self):
        scripts = load_migrations(SQL)
        rows = [
            {"migration_id": x.number, "checksum_sha256": x.digest,
             "state": "APPLIED"} for x in scripts[:3]
        ]
        self.assertEqual(verify_history(rows, scripts), 3)

    def test_changed_migration_checksum_is_blocked(self):
        scripts = load_migrations(SQL)
        with self.assertRaisesRegex(MigrationError, "checksum drift"):
            verify_history([{
                "migration_id": 1, "checksum_sha256": "0" * 64,
                "state": "APPLIED",
            }], scripts)

    def test_partial_ddl_is_not_retried(self):
        scripts = load_migrations(SQL)
        with self.assertRaisesRegex(MigrationError, "partially executed"):
            verify_history([{
                "migration_id": 1, "checksum_sha256": scripts[0].digest,
                "state": "IN_PROGRESS",
            }], scripts)

    def test_out_of_order_or_newer_migrations_fail(self):
        scripts = load_migrations(SQL)
        with self.assertRaisesRegex(MigrationError, "gap"):
            verify_history([{
                "migration_id": 2, "checksum_sha256": scripts[1].digest,
                "state": "APPLIED",
            }], scripts)
        with self.assertRaisesRegex(MigrationError, "newer"):
            verify_history([{
                "migration_id": i, "checksum_sha256": "0" * 64,
                "state": "APPLIED",
            } for i in range(1, 10)], scripts)


@unittest.skipUnless(bool(os.environ.get("LHFM_DB_HOST")), "MariaDB CI required")
class MigrationLiveDatabaseTests(unittest.TestCase):
    def test_fresh_ci_schema_has_no_pending_migrations(self):
        from lowhangingfruitme.approval_registry import ApprovalRegistry
        pending = migrate_database(
            ApprovalRegistry.from_environment()._connect,
            SQL, apply=False,
        )
        self.assertEqual(pending, ())
