"""Read-only startup migration gate: synthetic negative cases + real CI MariaDB."""
from __future__ import annotations

import os
import unittest

from lowhangingfruitme.migrations import PINNED_SQL_SHA256
from lowhangingfruitme.schema import (
    REQUIRED_TABLES, REQUIRED_COLUMNS, REQUIRED_CONSTRAINTS,
    SchemaMismatchError, find_schema_mismatches, require_operational_schema,
    find_migration_ledger_mismatches,
)


def catalog():
    tables = [{"TABLE_NAME": name, "ENGINE": "InnoDB"} for name in REQUIRED_TABLES]
    columns = [
        {"TABLE_NAME": table, "COLUMN_NAME": name,
         "COLUMN_DEFAULT": "300" if (table, name) == (
             "lhfm_recovery_cases", "fee_rate_bps"
         ) else None}
        for table, names in REQUIRED_COLUMNS.items() for name in names
    ]
    constraints = [
        {"TABLE_NAME": table, "CONSTRAINT_NAME": name}
        for table, name in REQUIRED_CONSTRAINTS
    ]
    return tables, columns, constraints


class SchemaCompatibilityUnitTests(unittest.TestCase):
    def test_current_contract_passes(self):
        self.assertEqual(find_schema_mismatches(*catalog()), [])

    def test_missing_migration_007_column_is_rejected(self):
        tables, columns, constraints = catalog()
        columns = [r for r in columns if r["COLUMN_NAME"] != "fee_rate_bps"]
        self.assertIn(
            "missing column lhfm_recovery_cases.fee_rate_bps",
            find_schema_mismatches(tables, columns, constraints),
        )

    def test_missing_migration_008_table_is_rejected(self):
        tables, columns, constraints = catalog()
        tables = [r for r in tables if r["TABLE_NAME"] != "lhfm_rule_heads"]
        self.assertIn(
            "missing table lhfm_rule_heads",
            find_schema_mismatches(tables, columns, constraints),
        )

    def test_missing_revision_column_is_rejected(self):
        tables, columns, constraints = catalog()
        columns = [
            r for r in columns
            if (r["TABLE_NAME"], r["COLUMN_NAME"])
            != ("lhfm_approval_records", "source_revision_id")
        ]
        self.assertIn(
            "missing column lhfm_approval_records.source_revision_id",
            find_schema_mismatches(tables, columns, constraints),
        )

    def test_missing_fee_constraint_is_rejected(self):
        tables, columns, constraints = catalog()
        constraints = [
            r for r in constraints
            if r["CONSTRAINT_NAME"] != "chk_case_fee_rate"
        ]
        self.assertIn(
            "missing constraint lhfm_recovery_cases.chk_case_fee_rate",
            find_schema_mismatches(tables, columns, constraints),
        )

    def test_fee_rate_default_drift_is_rejected(self):
        tables, columns, constraints = catalog()
        for row in columns:
            if row["COLUMN_NAME"] == "fee_rate_bps":
                row["COLUMN_DEFAULT"] = "500"
        self.assertTrue(any(
            "historical fee_rate_bps default" in item
            for item in find_schema_mismatches(tables, columns, constraints)
        ))

    def test_non_transactional_engine_is_rejected(self):
        tables, columns, constraints = catalog()
        tables[0]["ENGINE"] = "MyISAM"
        self.assertTrue(any(
            "non-InnoDB table" in item
            for item in find_schema_mismatches(tables, columns, constraints)
        ))

    def test_schema_ledger_rejects_missing_and_incomplete_migrations(self):
        rows = [
            {"migration_id": n, "checksum_sha256": PINNED_SQL_SHA256[n - 1], "state": "APPLIED"}
            for n in range(1, 11)
        ]
        self.assertEqual(find_migration_ledger_mismatches(rows), [])
        self.assertTrue(find_migration_ledger_mismatches(rows[:-1]))
        rows[0]["checksum_sha256"] = "a" * 64
        self.assertTrue(any("checksum mismatch" in x for x in
                            find_migration_ledger_mismatches(rows)))
        rows[0]["checksum_sha256"] = PINNED_SQL_SHA256[0]
        rows[4]["state"] = "IN_PROGRESS"
        self.assertTrue(find_migration_ledger_mismatches(rows))

    def test_read_only_verifier_closes_connection_and_fails_closed(self):
        tables, columns, constraints = catalog()
        tables.clear()

        class Cursor:
            def __init__(self):
                self.index = 0
            def __enter__(self):
                return self
            def __exit__(self, *args):
                return False
            def execute(self, query):
                self.index += 1
                self.current = [tables, columns, constraints, []][self.index-1]
            def fetchall(self):
                return self.current

        class Connection:
            closed = False
            def cursor(self):
                return Cursor()
            def close(self):
                self.closed = True

        db = Connection()
        with self.assertRaisesRegex(SchemaMismatchError, "missing table"):
            require_operational_schema(lambda: db)
        self.assertTrue(db.closed)


@unittest.skipUnless(bool(os.environ.get("LHFM_DB_HOST")), "CI MariaDB required")
class LiveSchemaCompatibilityTests(unittest.TestCase):
    def test_ci_database_after_migrations_is_compatible(self):
        from lowhangingfruitme.approval_registry import ApprovalRegistry
        require_operational_schema(ApprovalRegistry.from_environment()._connect)
