"""Controlled, checksum-verified MariaDB schema migrations. Never run at API startup.

MariaDB DDL implicitly commits. A committed IN_PROGRESS marker deliberately
blocks retries after partial DDL, requiring operator investigation/restore.
Only explicitly authorized maintenance jobs may apply migrations.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
import os
import re
import sys
from typing import Any, Callable

SQL_FILES = (
    "001_approval_registry.sql",
    "002_audit_api.sql",
    "003_private_uploads.sql",
    "004_recovery_ledger.sql",
    "005_recovery_case_status.sql",
    "006_mapping_approvals.sql",
    "007_recovery_fee_policy.sql",
    "008_rule_revisions.sql",
    "009_contract_candidates.sql",
)
# Immutable release baseline: SHA-256 of the exact, reviewed UTF-8 SQL source.
# New migrations must be appended and explicitly reviewed; historical hashes
# must never be silently recomputed from a modified deployment directory.
PINNED_SQL_SHA256 = (
    "3cd76eff979feb1a21d1ad3fb516331cae808c85a6dfe8271d4c38685360d710",
    "5841187eca693aead583ff90b508023633620d7f3da9034debffce055b024353",
    "3544e9efa0a084e88069c670119785380fbbd963ed2eded2f5bfdc08e63e38b7",
    "35693bd16a49c43ae14bd7e4b82408afa7047c066ff9e9cc5974f903cc25eeff",
    "02376f8b658947ce1426908f3318491f87aa12457840debc54c28722899af1c6",
    "fea50bcb403d3011f9915719c900e03497c7bbe13fa6343251ff33ae77007770",
    "d37ee6752e286674ac5d1d0f31bbc28d5641f3f5dd8755844f5cc29d3cfb6fee",
    "bfdf71d88f5908a9492aab1edaee16799c486cbcdb9635c2e17d2685bcd8a036",
    "912cb1b4e3037c008d4a17b32c5e01a81a7a36262f835485024403fb0256d640",
)

TRACKING_DDL = """
CREATE TABLE lhfm_schema_migrations (
  migration_id SMALLINT UNSIGNED NOT NULL,
  checksum_sha256 CHAR(64) NOT NULL,
  state VARCHAR(16) NOT NULL,
  started_at DATETIME(6) NOT NULL DEFAULT UTC_TIMESTAMP(6),
  applied_at DATETIME(6) NULL,
  PRIMARY KEY (migration_id),
  CONSTRAINT chk_lhfm_migration_state CHECK (state IN ('IN_PROGRESS','APPLIED'))
) ENGINE=InnoDB
"""


class MigrationError(RuntimeError):
    """Unsafe or inconsistent migration state. Do not auto-retry DDL."""


@dataclass(frozen=True)
class Migration:
    number: int
    name: str
    digest: str
    statements: tuple[str, ...]


def split_statements(content: str) -> tuple[str, ...]:
    """Bounded SQL/DDL files of this project only; never parse arbitrary SQL."""
    lines = [line for line in content.splitlines()
             if line.strip() and not line.lstrip().startswith("--")]
    body = "\n".join(lines)
    if re.search(r"(?im)^\s*(?:delimiter|source|\\\.)\b", body):
        raise MigrationError("unsupported SQL client directive")
    chunks = tuple(statement.strip() for statement in body.split(";")
                   if statement.strip())
    if not chunks:
        raise MigrationError("empty migration script")
    if any(not re.match(r"(?is)^(CREATE|ALTER)\s+", statement)
           for statement in chunks):
        raise MigrationError("only reviewed CREATE/ALTER DDL is permitted")
    return chunks


def load_migrations(sql_dir: Path) -> tuple[Migration, ...]:
    """Load only immutable reviewed SQL; reject changed deployment scripts."""
    directory = Path(sql_dir)
    if directory.is_symlink() or not directory.is_dir():
        raise MigrationError("SQL source directory missing or symlinked")
    result = []
    for number, name in enumerate(SQL_FILES, start=1):
        path = directory / name
        if path.is_symlink() or not path.is_file() or path.stat().st_size > 128 * 1024:
            raise MigrationError("SQL migration missing, symlinked or oversized: " + name)
        raw = path.read_bytes()
        try:
            content = raw.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise MigrationError("migration must be UTF-8: " + name) from exc
        digest = sha256(raw).hexdigest()
        if digest != PINNED_SQL_SHA256[number - 1]:
            raise MigrationError("migration source checksum drift at " + name)
        result.append(Migration(number, name, digest,
                                split_statements(content)))
    return tuple(result)


def verify_history(rows: list[dict[str, Any]], scripts: tuple[Migration, ...]) -> int:
    """Check exact ordered prefix of installed migrations, including hashes."""
    if len(rows) > len(scripts):
        raise MigrationError("database schema is newer than this application")
    for index, row in enumerate(rows):
        expected = scripts[index]
        if row["migration_id"] != expected.number:
            raise MigrationError("migration ledger contains a gap or unknown migration")
        if row["checksum_sha256"] != expected.digest:
            raise MigrationError("migration checksum drift at " + expected.name)
        if row["state"] != "APPLIED":
            raise MigrationError(
                "partially executed migration " + expected.name
                + "; manual backup/DDL reconciliation required"
            )
    return len(rows)


def migrate_database(
    connect: Callable[[], Any], sql_dir: Path, *,
    apply: bool, backup_confirmed: bool = False,
    ci_test_database: bool = False,
) -> tuple[str, ...]:
    """Return pending names in plan mode; apply only with explicit authority.

    No automatic adoption of legacy tables. Existing installations without a
    ledger require separate DBA validation; guessing their DDL history is unsafe.
    """
    scripts = load_migrations(sql_dir)
    db = connect()
    locked = False
    try:
        with db.cursor() as cur:
            cur.execute("SELECT DATABASE() AS db_name")
            row = cur.fetchone()
            database = row["db_name"] if row else None
            if not database or database.lower() in (
                "mysql", "information_schema", "performance_schema", "sys"
            ):
                raise MigrationError("dedicated application database required")
            if apply and not (ci_test_database and database == "lhfm_test"):
                if not backup_confirmed or os.environ.get("LHFM_MIGRATION_APPROVED") != "YES":
                    raise MigrationError(
                        "operator backup confirmation and LHFM_MIGRATION_APPROVED=YES required"
                    )
            if ci_test_database and database != "lhfm_test":
                raise MigrationError("CI bootstrap is allowed only in lhfm_test")
            lock_name = "lhfm:migrate:" + sha256(database.encode()).hexdigest()[:32]
            cur.execute("SELECT GET_LOCK(%s, 20) AS acquired", (lock_name,))
            lock = cur.fetchone()
            if not lock or lock["acquired"] != 1:
                raise MigrationError("migration advisory lock unavailable")
            locked = True
            cur.execute(
                "SELECT TABLE_NAME FROM information_schema.TABLES "
                "WHERE TABLE_SCHEMA=DATABASE()"
            )
            present = {row["TABLE_NAME"] for row in cur.fetchall()}
            if "lhfm_schema_migrations" not in present:
                if any(name.startswith("lhfm_") for name in present):
                    raise MigrationError(
                        "untracked existing LHFM tables; do not silently adopt or overwrite"
                    )
                if not apply:
                    return tuple(script.name for script in scripts)
                cur.execute(TRACKING_DDL)
                db.commit()
            cur.execute(
                "SELECT migration_id, checksum_sha256, state "
                "FROM lhfm_schema_migrations ORDER BY migration_id"
            )
            applied_count = verify_history(list(cur.fetchall()), scripts)
            pending = scripts[applied_count:]
            if not apply:
                return tuple(script.name for script in pending)
            for script in pending:
                # Persist the in-progress marker BEFORE any non-transactional DDL.
                cur.execute(
                    "INSERT INTO lhfm_schema_migrations "
                    "(migration_id, checksum_sha256, state) VALUES (%s,%s,'IN_PROGRESS')",
                    (script.number, script.digest),
                )
                db.commit()
                for statement in script.statements:
                    cur.execute(statement)
                cur.execute(
                    "UPDATE lhfm_schema_migrations SET state='APPLIED',"
                    "applied_at=UTC_TIMESTAMP(6) "
                    "WHERE migration_id=%s AND checksum_sha256=%s "
                    "AND state='IN_PROGRESS'",
                    (script.number, script.digest),
                )
                if cur.rowcount != 1:
                    raise MigrationError("schema ledger update was not atomic")
                db.commit()
            return tuple(script.name for script in pending)
    except Exception:
        db.rollback()
        raise
    finally:
        if locked:
            try:
                with db.cursor() as cursor:
                    cursor.execute("SELECT RELEASE_LOCK(%s)", (lock_name,))
            finally:
                db.close()
        else:
            db.close()


def main() -> int:
    parser = argparse.ArgumentParser(description="Controlled LHFM MariaDB migrations")
    parser.add_argument("--sql-dir", type=Path, required=True)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--backup-confirmed", action="store_true")
    args = parser.parse_args()
    from .approval_registry import ApprovalRegistry
    try:
        pending = migrate_database(
            ApprovalRegistry.from_environment()._connect,
            args.sql_dir, apply=args.apply,
            backup_confirmed=args.backup_confirmed,
        )
        if args.apply:
            from .schema import require_operational_schema
            require_operational_schema(ApprovalRegistry.from_environment()._connect)
            print("SCHEMA_APPLIED:", ", ".join(pending) if pending else "no changes")
        else:
            print("SCHEMA_PENDING:", ", ".join(pending) if pending else "none")
        return 0
    except Exception as exc:
        print("MIGRATION_BLOCKED: " + str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
