"""Operator-only housekeeping for ABANDONED upload staging, never customer data.

Only PENDING or RECEIVING intents expired for >=24 hours are eligible.
A stopped upload writer must be confirmed out of band before applying.
No CLEAN/REJECTED upload, approved contract candidate, financial document,
or finished source file is ever deleted. No HTTP endpoint calls this code.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone, timedelta
import json
import os
from pathlib import Path
import stat
import sys
from typing import Any, Callable
from uuid import UUID

from .api.uploads import FORMATS, MAX_UPLOAD
from .approval_registry import ApprovalRegistry
from .schema import require_operational_schema

GRACE_HOURS = 24
MAX_BATCH = 100


class HousekeepingBlocked(RuntimeError):
    """Unsafe or ambiguous old upload: operator intervention required."""


def _private_root(root: Path) -> Path:
    root = Path(root)
    if not root.is_absolute():
        raise HousekeepingBlocked("private staging root must be absolute")
    if os.geteuid() == 0:
        raise HousekeepingBlocked("housekeeping must not execute as root")
    for part in (root, *root.parents):
        if part.is_symlink():
            raise HousekeepingBlocked("private staging root must not contain symlinks")
    try:
        details = root.stat()
    except OSError as exc:
        raise HousekeepingBlocked("private staging root unavailable") from exc
    if (not stat.S_ISDIR(details.st_mode)
            or stat.S_IMODE(details.st_mode) != 0o700
            or details.st_uid != os.geteuid()):
        raise HousekeepingBlocked("private staging root not owned by operator")
    return root.resolve(strict=True)


def _candidate_paths(root: Path, row: dict[str, Any], cutoff_ns: int) -> tuple[tuple[Path, os.stat_result], ...] | None:
    """Check inode/type/age before any status mutation. None = recent writer."""
    upload_id = row["upload_id"]
    try:
        if not isinstance(upload_id, str) or str(UUID(upload_id)) != upload_id:
            raise ValueError("noncanonical ID")
    except (ValueError, AttributeError) as exc:
        raise HousekeepingBlocked("noncanonical upload ID in database") from exc
    kind = row["kind"]
    if kind not in FORMATS:
        raise HousekeepingBlocked("unknown upload format in database")
    suffix = FORMATS[kind][0]
    # A final file can exist if a worker crashed between the filesystem
    # promotion and the CLEAN status commit. This is NOT an orphan temp file.
    final = root / (upload_id + suffix)
    if final.is_symlink() or final.exists():
        raise HousekeepingBlocked("ambiguous final upload requires manual reconciliation")

    first = root / (upload_id + ".part")
    inspected = root / (upload_id + ".inspect" + suffix)
    existing = []
    for path in (first, inspected):
        try:
            info = path.lstat()
        except FileNotFoundError:
            continue
        if (not stat.S_ISREG(info.st_mode) or info.st_uid != os.geteuid()
                or stat.S_IMODE(info.st_mode) & 0o077
                or info.st_size > MAX_UPLOAD or info.st_nlink not in (1, 2)):
            raise HousekeepingBlocked("unsafe partial upload inode")
        if info.st_mtime_ns >= cutoff_ns:
            return None
        existing.append((path, info))
    # .inspect is a hard-link to .part during format checking. Never unlink
    # an inode with another unaccounted-for link outside these two names.
    if any(info.st_nlink == 2 for _, info in existing):
        if (len(existing) != 2 or existing[0][1].st_ino != existing[1][1].st_ino
                or any(info.st_nlink != 2 for _, info in existing)):
            raise HousekeepingBlocked("unaccounted hard link to staged content")
    if row["state"] == "PENDING" and existing:
        raise HousekeepingBlocked("pending upload unexpectedly contains partial data")
    return tuple(existing)


def prune_stale_uploads(
    *, connect: Callable[[], Any], upload_root: Path, apply: bool = False,
    limit: int = MAX_BATCH,
    approvals: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Bounded and idempotent conditional transition to REJECTED.

    Files are removed BEFORE commit while upload rows remain locked. On a
    crash, DB rollback leaves an expired row for later retry. On success,
    an immutable SQL-011 housekeeping event records the original state
    and number of partial files removed. This is not GDPR erasure.
    """
    if type(limit) is not int or not 1 <= limit <= MAX_BATCH:
        raise HousekeepingBlocked("housekeeping batch must be between 1 and 100")
    env = os.environ if approvals is None else approvals
    if apply and (env.get("LHFM_UPLOAD_HOUSEKEEPING_APPROVED") != "YES"
                  or env.get("LHFM_UPLOAD_WRITES_STOPPED") != "YES"):
        raise HousekeepingBlocked("operator approval and upload write stop required")
    root = _private_root(upload_root)
    cutoff_ns = (datetime.now(timezone.utc) - timedelta(hours=GRACE_HOURS)).timestamp() * 1_000_000_000
    db = connect()
    try:
        with db.cursor() as cursor:
            statement = (
                "SELECT upload_id,kind,state FROM lhfm_uploads "
                "WHERE state IN ('PENDING','RECEIVING') "
                "AND expires_at < DATE_SUB(UTC_TIMESTAMP(6), INTERVAL 24 HOUR) "
                "ORDER BY expires_at,upload_id LIMIT %s"
            )
            if apply:
                statement += " FOR UPDATE"
            cursor.execute(statement, (limit,))
            rows = list(cursor.fetchall())
            candidates = []
            skipped_recent = 0
            for row in rows:
                files = _candidate_paths(root, row, int(cutoff_ns))
                if files is None:
                    skipped_recent += 1
                else:
                    candidates.append((row, files))
            if apply:
                for row, files in candidates:
                    cursor.execute(
                        "UPDATE lhfm_uploads SET state='REJECTED',"
                        "finished_at=UTC_TIMESTAMP(6) "
                        "WHERE upload_id=%s AND state=%s AND "
                        "expires_at < DATE_SUB(UTC_TIMESTAMP(6), INTERVAL 24 HOUR)",
                        (row["upload_id"], row["state"]),
                    )
                    if cursor.rowcount != 1:
                        raise HousekeepingBlocked("stale upload state changed during cleanup")
                    # Revalidate no path was swapped after the earlier lstat;
                    # the operator must have stopped API uploads entirely.
                    for path, before in files:
                        info = path.lstat()
                        if (not stat.S_ISREG(info.st_mode)
                                or info.st_uid != os.geteuid()
                                or stat.S_IMODE(info.st_mode) & 0o077
                                or (info.st_dev, info.st_ino, info.st_size,
                                    info.st_nlink, info.st_mtime_ns)
                                != (before.st_dev, before.st_ino,
                                    before.st_size, before.st_nlink,
                                    before.st_mtime_ns)
                                or info.st_mtime_ns >= int(cutoff_ns)):
                            raise HousekeepingBlocked("partial upload mutated during cleanup")
                        path.unlink()
                    cursor.execute(
                        "INSERT INTO lhfm_upload_housekeeping_events "
                        "(upload_id, prior_state, removed_partials) "
                        "VALUES (%s,%s,%s)",
                        (row["upload_id"], row["state"], len(files)),
                    )
                db.commit()
            else:
                db.rollback()
            return {
                "mode": "applied" if apply else "dry_run",
                "stale_rows_scanned": len(rows),
                "stale_intents": len(candidates),
                "recent_partial_files_skipped": skipped_recent,
                "partial_files": sum(len(files) for _, files in candidates),
                "max_batch": limit,
                "customer_clean_files_touched": 0,
            }
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Offline stale-upload cleanup (dry-run by default)"
    )
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--limit", type=int, default=MAX_BATCH)
    options = parser.parse_args()
    try:
        if (os.environ.get("LHFM_DB_HOST") != "127.0.0.1"
                or os.environ.get("LHFM_DB_USER", "").lower() in ("root","admin","mysql")
                or os.environ.get("LHFM_DB_NAME", "").startswith("lhfm_restore_")):
            raise HousekeepingBlocked("dedicated local nonprivileged database required")
        registry = ApprovalRegistry.from_environment()
        require_operational_schema(registry._connect)
        result = prune_stale_uploads(
            connect=registry._connect, upload_root=Path(os.environ["LHFM_UPLOAD_ROOT"]),
            apply=options.apply, limit=options.limit,
        )
    except Exception:
        print("LHFM_UPLOAD_HOUSEKEEPING_BLOCKED", file=sys.stderr)
        return 2
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
