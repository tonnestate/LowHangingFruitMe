"""CI-only MariaDB schema setup and synthetic reviewer grant.

NEVER run this against production. The migration runner verifies the dedicated
test database and tracks every DDL file/checksum before test data is inserted.
"""
import os
from pathlib import Path
from lowhangingfruitme.approval_registry import ApprovalRegistry
from lowhangingfruitme.migrations import migrate_database

if __name__ == "__main__":
    if os.environ.get("LHFM_DB_NAME") != "lhfm_test":
        raise RuntimeError("CI setup only allowed in lhfm_test")
    registry = ApprovalRegistry.from_environment()
    migrate_database(registry._connect, Path("sql"), apply=True, ci_test_database=True)
    c = registry._connect()
    try:
        with c.cursor() as cursor:
            cursor.execute(
                """INSERT INTO lhfm_reviewer_grants
                   (tenant_id, legal_entity_id, reviewer_id, role, active)
                   VALUES (%s,%s,%s,'contract_reviewer',1)""",
                ("T-SYN-1", "LE-SYN-1", "REVIEWER-SYN-1"),
            )
            cursor.execute(
                """INSERT INTO lhfm_finance_grants
                   (tenant_id, legal_entity_id, finance_actor_id, active)
                   VALUES (%s,%s,%s,1)""",
                ("T-SYN-1", "LE-SYN-1", "FINANCE-SYN-1"),
            )
        c.commit()
    except Exception:
        c.rollback()
        raise
    finally:
        c.close()
