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
            sql = "\n".join(
                Path(path).read_text(encoding="utf-8")
                for path in ("sql/001_approval_registry.sql", "sql/002_audit_api.sql", "sql/003_private_uploads.sql", "sql/004_recovery_ledger.sql", "sql/005_recovery_case_status.sql", "sql/006_mapping_approvals.sql")
            )
            statements = "\n".join(
                line for line in sql.splitlines()
                if line.strip() and not line.lstrip().startswith("--")
            )
            for statement in statements.split(";"):
                if statement.strip():
                    cursor.execute(statement.strip())
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
