"""CI-only MariaDB schema setup and synthetic reviewer grant.

NEVER run this against production; future provisioning requires an authenticated
privileged operator and independently auditable identity verification.
"""
import os
from pathlib import Path
from lowhangingfruitme.approval_registry import ApprovalRegistry

if __name__ == "__main__":
    if os.environ.get("LHFM_DB_NAME") != "lhfm_test":
        raise RuntimeError("CI setup only allowed in lhfm_test")
    c = ApprovalRegistry.from_environment()._connect()
    try:
        with c.cursor() as cursor:
            sql = Path("sql/001_approval_registry.sql").read_text(encoding="utf-8")
            for statement in sql.split(";"):
                # Remove comment-only lines before dispatching each statement
                statement = "\n".join(
                    line for line in statement.splitlines()
                    if line.strip() and not line.lstrip().startswith("--")
                ).strip()
                if statement:
                    cursor.execute(statement)
            cursor.execute(
                """INSERT INTO lhfm_reviewer_grants
                   (tenant_id, legal_entity_id, reviewer_id, role, active)
                   VALUES (%s,%s,%s,'contract_reviewer',1)""",
                ("T-SYN-1", "LE-SYN-1", "REVIEWER-SYN-1"),
            )
        c.commit()
    except Exception:
        c.rollback()
        raise
    finally:
        c.close()
