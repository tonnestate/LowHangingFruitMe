"""TEST-ONLY factory: never deploy as an approval issuance endpoint.

The key is randomly generated in GitHub CI and retained only as an environment
variable. The named reviewer is synthetic, not authenticated; production
issuance must use server-side RBAC and audit logging.
"""
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import sys

from lowhangingfruitme.approval import issue_approval, key_from_environment

if __name__ == "__main__":
    rule_path, contract_path, output_path = map(Path, sys.argv[1:4])
    rule = json.loads(rule_path.read_text(encoding="utf-8"))
    receipt = issue_approval(
        rule, key=key_from_environment(),
        tenant_id="T-SYN-1", legal_entity_id="LE-SYN-1",
        reviewer_id="REVIEWER-SYN-1", approval_id="APPROVAL-CI-1",
        source_revision_id="REV-SYN-1",
        document_sha256=sha256(contract_path.read_bytes()).hexdigest(),
        approved_at=datetime.now(timezone.utc),
    )
    output_path.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
