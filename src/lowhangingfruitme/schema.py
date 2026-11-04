"""Strict, read-only MariaDB compatibility gate for the active application code.

Schema DDL is intentionally NOT executed by the web application. MariaDB DDL
causes implicit commits; a migration must instead be applied and verified in
a controlled maintenance procedure before the API is started.
"""
from __future__ import annotations

import os
import sys
from typing import Any, Callable
from .migrations import PINNED_SQL_SHA256

# Required structures across sql/001 .. sql/008. These are the minimum
# objects actually read or written by the current audit/upload/recovery paths.
REQUIRED_TABLES = frozenset({
    "lhfm_reviewer_grants",
    "lhfm_approval_records",
    "lhfm_approval_events",
    "lhfm_api_bundles",
    "lhfm_api_runs",
    "lhfm_uploads",
    "lhfm_finance_grants",
    "lhfm_recovery_cases",
    "lhfm_recovery_events",
    "lhfm_recovery_case_status_events",
    "lhfm_mapping_approvals",
    "lhfm_mapping_approval_events",
    "lhfm_rule_heads",
    "lhfm_rule_revision_events",
    "lhfm_schema_migrations",
})

REQUIRED_COLUMNS: dict[str, frozenset[str]] = {
    "lhfm_schema_migrations": frozenset({"migration_id", "checksum_sha256", "state", "applied_at"}),
    "lhfm_recovery_cases": frozenset({"fee_rate_bps"}),
    "lhfm_approval_records": frozenset({
        "agreement_id", "rule_id", "rule_revision",
        "source_revision_id", "superseded_by",
    }),
    "lhfm_rule_heads": frozenset({
        "tenant_id", "legal_entity_id", "agreement_id",
        "rule_id", "current_approval_id",
    }),
    "lhfm_rule_revision_events": frozenset({
        "approval_id", "tenant_id", "legal_entity_id",
        "actor_id", "event_type", "replaced_by",
    }),
    "lhfm_mapping_approvals": frozenset({
        "bundle_id", "dataset", "source_sha256", "mapping_sha256",
        "receipt_sha256", "approval_id", "state",
    }),
}

REQUIRED_CONSTRAINTS = frozenset({
    ("lhfm_recovery_cases", "chk_case_fee_rate"),
    ("lhfm_rule_heads", "fk_rule_current_approval"),
    ("lhfm_rule_revision_events", "chk_rule_revision_event"),
    ("lhfm_mapping_approvals", "fk_mapping_contract_approval"),
})


class SchemaMismatchError(RuntimeError):
    """Database is incompatible with this build; deny startup, never migrate."""


def find_schema_mismatches(
    tables: list[dict[str, Any]],
    columns: list[dict[str, Any]],
    constraints: list[dict[str, Any]],
) -> list[str]:
    """Pure, testable comparison of MariaDB's metadata with code requirements."""
    table_map = {r["TABLE_NAME"]: r for r in tables}
    column_map = {(r["TABLE_NAME"], r["COLUMN_NAME"]): r for r in columns}
    constraint_set = {
        (r["TABLE_NAME"], r["CONSTRAINT_NAME"]) for r in constraints
    }
    problems: list[str] = []

    for name in sorted(REQUIRED_TABLES):
        table = table_map.get(name)
        if table is None:
            problems.append("missing table " + name)
        elif str(table.get("ENGINE") or "").upper() != "INNODB":
            problems.append("non-InnoDB table " + name)

    for table, names in sorted(REQUIRED_COLUMNS.items()):
        if table not in table_map:
            continue
        for name in sorted(names):
            if (table, name) not in column_map:
                problems.append("missing column " + table + "." + name)

    for table, constraint in sorted(REQUIRED_CONSTRAINTS):
        if table in table_map and (table, constraint) not in constraint_set:
            problems.append("missing constraint " + table + "." + constraint)

    # Migration 007 deliberately gives historical cases a 3% DEFAULT.
    # New cases explicitly store 5%; silently defaulting historical records to
    # 5% is not an acceptable automatic repair.
    rate = column_map.get(("lhfm_recovery_cases", "fee_rate_bps"))
    if rate is not None:
        default = rate.get("COLUMN_DEFAULT")
        if str(default).strip("'") != "300":
            problems.append("unexpected historical fee_rate_bps default (requires 300)")

    return problems


def find_migration_ledger_mismatches(rows: list[dict[str, Any]]) -> list[str]:
    """Reject gaps, unfinished DDL and unknown versions at API startup."""
    if len(rows) != len(PINNED_SQL_SHA256):
        return ["migration ledger does not contain the complete release baseline"]
    errors = []
    for version, row in enumerate(rows, start=1):
        if row.get("migration_id") != version or row.get("state") != "APPLIED":
            errors.append("migration ledger has gap or unfinished version " + str(version))
        checksum = row.get("checksum_sha256")
        if checksum != PINNED_SQL_SHA256[version - 1]:
            errors.append("migration ledger checksum mismatch for " + str(version))
    return errors


def require_operational_schema(connect: Callable[[], Any]) -> None:
    """Deny serving real API requests if schema 001..008 is incomplete/drifted.

    Metadata-only queries with the app's normal DB connection. This function
    has no CREATE, ALTER or data manipulation and is safe to call at startup.
    """
    db = connect()
    try:
        with db.cursor() as cursor:
            cursor.execute(
                "SELECT TABLE_NAME, ENGINE FROM information_schema.TABLES "
                "WHERE TABLE_SCHEMA = DATABASE()"
            )
            tables = list(cursor.fetchall())
            cursor.execute(
                "SELECT TABLE_NAME, COLUMN_NAME, COLUMN_DEFAULT "
                "FROM information_schema.COLUMNS WHERE TABLE_SCHEMA = DATABASE()"
            )
            columns = list(cursor.fetchall())
            cursor.execute(
                "SELECT TABLE_NAME, CONSTRAINT_NAME "
                "FROM information_schema.TABLE_CONSTRAINTS "
                "WHERE TABLE_SCHEMA = DATABASE()"
            )
            constraints = list(cursor.fetchall())
            ledger_rows = []
            if any(row["TABLE_NAME"] == "lhfm_schema_migrations" for row in tables):
                cursor.execute(
                    "SELECT migration_id, checksum_sha256, state "
                    "FROM lhfm_schema_migrations ORDER BY migration_id"
                )
                ledger_rows = list(cursor.fetchall())
    finally:
        db.close()

    problems = find_schema_mismatches(tables, columns, constraints)
    if ledger_rows or any(row["TABLE_NAME"] == "lhfm_schema_migrations" for row in tables):
        problems.extend(find_migration_ledger_mismatches(ledger_rows))
    if problems:
        raise SchemaMismatchError(
            "LowHangingFruitMe database is not compatible with current code: "
            + "; ".join(problems)
            + ". Apply reviewed sql/001..008 migrations to the dedicated "
              "database before starting the API; do not run DDL on startup."
        )


def main() -> int:
    """Explicit read-only operator check: lhfm-schema-check."""
    from .approval_registry import ApprovalRegistry

    try:
        require_operational_schema(ApprovalRegistry.from_environment()._connect)
    except Exception as exc:
        print("SCHEMA_NOT_READY: " + str(exc), file=sys.stderr)
        return 2
    print("SCHEMA_READY: migration ledger, tables, columns and constraints verified")
    return 0


if __name__ == "__main__":
    sys.exit(main())
