"""Persistent MariaDB approval registry and dispatch-time revocation guard.

A registered HMAC receipt is *not* proof that a named actor has authenticated.
The caller must be a trusted service that has already authenticated the actor.
The DB grants are authorization records, not a login replacement.

The transaction-level SELECT ... FOR UPDATE guard MUST wrap the computation,
so a concurrent revoke cannot commit between the final check and calculation.
"""
from __future__ import annotations

from contextlib import contextmanager
from hashlib import sha256
import hmac
import json
import os
from typing import Any, Iterator

from .approval import verify_approval, _json_bytes, _nonempty


class ApprovalRegistry:
    """Owns a single MariaDB connection per operation; never reuse across threads."""

    def __init__(self, connect: Any):
        if not callable(connect):
            raise TypeError("connect must be a no-argument DB connection factory")
        self._connect = connect

    @classmethod
    def from_environment(cls) -> "ApprovalRegistry":
        """DB credentials supplied by a trusted runtime, never customer input."""
        import pymysql

        required = ("LHFM_DB_HOST", "LHFM_DB_USER", "LHFM_DB_PASSWORD", "LHFM_DB_NAME")
        missing = [name for name in required if not os.environ.get(name)]
        if missing:
            raise RuntimeError("missing registry database configuration: " + ", ".join(missing))
        port = int(os.environ.get("LHFM_DB_PORT", "3306"))
        if not 1 <= port <= 65535:
            raise ValueError("invalid database port")

        def connect():
            return pymysql.connect(
                host=os.environ["LHFM_DB_HOST"], port=port,
                user=os.environ["LHFM_DB_USER"],
                password=os.environ["LHFM_DB_PASSWORD"],
                database=os.environ["LHFM_DB_NAME"],
                charset="utf8mb4", autocommit=False,
                connect_timeout=5, read_timeout=20, write_timeout=20,
                cursorclass=pymysql.cursors.DictCursor,
            )

        return cls(connect)

    @staticmethod
    def _require_actor(value: str) -> str:
        return _nonempty(value, "authenticated_actor_id")

    def require_scoped_reviewer(
        self, *, tenant_id: str, legal_entity_id: str, actor_id: str,
    ) -> None:
        """Preflight scoped authorization; repeat under guard at dispatch."""
        actor = self._require_actor(actor_id)
        connection = self._connect()
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    """SELECT role, active FROM lhfm_reviewer_grants
                       WHERE tenant_id=%s AND legal_entity_id=%s
                         AND reviewer_id=%s""",
                    (tenant_id, legal_entity_id, actor),
                )
                grant = cursor.fetchone()
                if not grant or grant["role"] != "contract_reviewer" or not grant["active"]:
                    raise PermissionError("actor lacks an active tenant/entity grant")
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    @staticmethod
    def _lineage(rule: dict[str, Any]) -> tuple[str, str, str]:
        """Contract + rule ID are the unambiguous key across signed revisions."""
        if not isinstance(rule, dict):
            raise ValueError("contract rule must be an object")
        values = tuple(_nonempty(rule.get(k), k) for k in
                       ("agreement_id", "rule_id", "revision"))
        if any(len(value) > 128 for value in values):
            raise ValueError("contract lineage identifier exceeds storage limit")
        return values

    def register(self, receipt: dict[str, Any], *, rule: dict[str, Any],
                 key: bytes, document_sha256: str,
                 tenant_id: str, legal_entity_id: str,
                 authenticated_actor_id: str) -> None:
        """Atomically approve latest sourced revision and supersede its predecessor.

        This operation is only called after upstream authentication. A receipt
        and approved rule never grant authority by themselves.
        """
        actor = self._require_actor(authenticated_actor_id)
        agreement_id, rule_id, revision = self._lineage(rule)
        verified = verify_approval(
            receipt, rule, key=key, tenant_id=tenant_id,
            legal_entity_id=legal_entity_id, document_sha256=document_sha256,
        )
        if not hmac.compare_digest(actor, verified["reviewer_id"]):
            raise PermissionError("receipt reviewer differs from authenticated actor")
        source_revision_id = _nonempty(verified["source_revision_id"], "source_revision_id")
        if len(source_revision_id) > 128:
            raise ValueError("source revision identifier exceeds storage limit")
        digest = sha256(_json_bytes(receipt)).hexdigest()
        connection = self._connect()
        try:
            with connection.cursor() as cursor:
                # Always lock the lineage head BEFORE the predecessor approval;
                # guard() takes the same order so a replacement cannot race an
                # active audit or commit while that audit is running.
                cursor.execute(
                    """INSERT INTO lhfm_rule_heads
                       (tenant_id, legal_entity_id, agreement_id, rule_id,
                        current_approval_id)
                       VALUES (%s,%s,%s,%s,NULL)
                       ON DUPLICATE KEY UPDATE current_approval_id=current_approval_id""",
                    (tenant_id, legal_entity_id, agreement_id, rule_id),
                )
                cursor.execute(
                    """SELECT current_approval_id FROM lhfm_rule_heads
                       WHERE tenant_id=%s AND legal_entity_id=%s
                         AND agreement_id=%s AND rule_id=%s FOR UPDATE""",
                    (tenant_id, legal_entity_id, agreement_id, rule_id),
                )
                head = cursor.fetchone()
                if head is None:
                    raise RuntimeError("lineage head cannot be locked")
                previous_id = head["current_approval_id"]
                if previous_id == receipt["approval_id"]:
                    raise ValueError("approval already registered for this rule")
                previous = None
                if previous_id:
                    cursor.execute(
                        """SELECT approval_id, state, agreement_id, rule_id
                           FROM lhfm_approval_records
                           WHERE approval_id=%s AND tenant_id=%s
                             AND legal_entity_id=%s FOR UPDATE""",
                        (previous_id, tenant_id, legal_entity_id),
                    )
                    previous = cursor.fetchone()
                    if (not previous or previous["agreement_id"] != agreement_id
                            or previous["rule_id"] != rule_id
                            or previous["state"] not in ("ACTIVE", "REVOKED")):
                        raise RuntimeError("corrupted rule lineage, manual recovery required")
                cursor.execute(
                    """SELECT role, active FROM lhfm_reviewer_grants
                       WHERE tenant_id=%s AND legal_entity_id=%s AND reviewer_id=%s
                       FOR UPDATE""",
                    (tenant_id, legal_entity_id, actor),
                )
                grant = cursor.fetchone()
                if not grant or grant["role"] != "contract_reviewer" or not grant["active"]:
                    raise PermissionError("reviewer does not have an active scoped grant")
                cursor.execute(
                    """INSERT INTO lhfm_approval_records
                       (approval_id, tenant_id, legal_entity_id, reviewer_id,
                        rule_sha256, document_sha256, receipt_sha256, state,
                        agreement_id, rule_id, rule_revision, source_revision_id)
                       VALUES (%s,%s,%s,%s,%s,%s,%s,'ACTIVE',%s,%s,%s,%s)""",
                    (receipt["approval_id"], tenant_id, legal_entity_id, actor,
                     verified["rule_sha256"], verified["document_sha256"], digest,
                     agreement_id, rule_id, revision, source_revision_id),
                )
                if previous and previous["state"] == "ACTIVE":
                    cursor.execute(
                        """UPDATE lhfm_approval_records SET state='REVOKED',
                           revoked_by=%s, revoked_at=UTC_TIMESTAMP(6),
                           superseded_by=%s
                           WHERE approval_id=%s AND state='ACTIVE'""",
                        (actor, receipt["approval_id"], previous_id),
                    )
                    if cursor.rowcount != 1:
                        raise RuntimeError("concurrent supersession state change")
                    cursor.execute(
                        """INSERT INTO lhfm_approval_events
                           (approval_id, tenant_id, legal_entity_id, actor_id, event_type)
                           VALUES (%s,%s,%s,%s,'REVOKED')""",
                        (previous_id, tenant_id, legal_entity_id, actor),
                    )
                    cursor.execute(
                        """INSERT INTO lhfm_rule_revision_events
                           (approval_id, tenant_id, legal_entity_id, actor_id,
                            event_type, replaced_by)
                           VALUES (%s,%s,%s,%s,'SUPERSEDED',%s)""",
                        (previous_id, tenant_id, legal_entity_id, actor,
                         receipt["approval_id"]),
                    )
                cursor.execute(
                    """UPDATE lhfm_rule_heads SET current_approval_id=%s
                       WHERE tenant_id=%s AND legal_entity_id=%s
                         AND agreement_id=%s AND rule_id=%s""",
                    (receipt["approval_id"], tenant_id, legal_entity_id,
                     agreement_id, rule_id),
                )
                if cursor.rowcount != 1:
                    raise RuntimeError("lineage head transition failed")
                cursor.execute(
                    """INSERT INTO lhfm_approval_events
                       (approval_id, tenant_id, legal_entity_id, actor_id, event_type)
                       VALUES (%s,%s,%s,%s,'ISSUED')""",
                    (receipt["approval_id"], tenant_id, legal_entity_id, actor),
                )
                cursor.execute(
                    """INSERT INTO lhfm_rule_revision_events
                       (approval_id, tenant_id, legal_entity_id, actor_id, event_type)
                       VALUES (%s,%s,%s,%s,'APPROVED')""",
                    (receipt["approval_id"], tenant_id, legal_entity_id, actor),
                )
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def revoke(self, approval_id: str, *, tenant_id: str,
               legal_entity_id: str, authenticated_actor_id: str) -> bool:
        """Atomic revoke by an active reviewer of the same entity.

        Revocation is idempotent. Never authorize it with a user-provided role
        string; only the stored role grant is used.
        """
        actor = self._require_actor(authenticated_actor_id)
        approval_id = _nonempty(approval_id, "approval_id")
        connection = self._connect()
        try:
            with connection.cursor() as cursor:
                # Approval row first, then reviewer grant: same lock order as
                # audit guard. Reversing it would permit a real InnoDB deadlock.
                cursor.execute(
                    """SELECT state FROM lhfm_approval_records
                       WHERE approval_id=%s AND tenant_id=%s AND legal_entity_id=%s
                       FOR UPDATE""",
                    (approval_id, tenant_id, legal_entity_id),
                )
                row = cursor.fetchone()
                if row is None:
                    raise ValueError("approval not found in authenticated scope")
                cursor.execute(
                    """SELECT role, active FROM lhfm_reviewer_grants
                       WHERE tenant_id=%s AND legal_entity_id=%s AND reviewer_id=%s
                       FOR UPDATE""",
                    (tenant_id, legal_entity_id, actor),
                )
                role = cursor.fetchone()
                if not role or role["role"] != "contract_reviewer" or not role["active"]:
                    raise PermissionError("actor cannot revoke in this tenant/entity")
                if row["state"] == "REVOKED":
                    connection.commit()
                    return False
                if row["state"] != "ACTIVE":
                    raise ValueError("unexpected approval state")
                cursor.execute(
                    """UPDATE lhfm_approval_records SET state='REVOKED',
                       revoked_by=%s, revoked_at=UTC_TIMESTAMP(6)
                       WHERE approval_id=%s AND tenant_id=%s
                       AND legal_entity_id=%s AND state='ACTIVE'""",
                    (actor, approval_id, tenant_id, legal_entity_id),
                )
                if cursor.rowcount != 1:
                    raise RuntimeError("concurrent approval state change")
                cursor.execute(
                    """INSERT INTO lhfm_approval_events
                       (approval_id, tenant_id, legal_entity_id, actor_id, event_type)
                       VALUES (%s,%s,%s,%s,'REVOKED')""",
                    (approval_id, tenant_id, legal_entity_id, actor),
                )
                cursor.execute(
                    """INSERT INTO lhfm_rule_revision_events
                       (approval_id, tenant_id, legal_entity_id, actor_id, event_type)
                       VALUES (%s,%s,%s,%s,'REVOKED')""",
                    (approval_id, tenant_id, legal_entity_id, actor),
                )
            connection.commit()
            return True
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    @contextmanager
    def guard(self, receipt: dict[str, Any], *, rule: dict[str, Any],
              key: bytes, document_sha256: str, tenant_id: str,
              legal_entity_id: str,
              acting_reviewer_id: str | None = None) -> Iterator[dict[str, str]]:
        """Lock the current contract revision throughout calculation.

        No new approval/supersession can commit while an audit holds the head
        lock; after release the old signed bundle is permanently non-current.
        """
        agreement_id, rule_id, revision = self._lineage(rule)
        verified = verify_approval(
            receipt, rule, key=key, tenant_id=tenant_id,
            legal_entity_id=legal_entity_id, document_sha256=document_sha256,
        )
        if acting_reviewer_id is not None and not hmac.compare_digest(
            self._require_actor(acting_reviewer_id), verified["reviewer_id"]
        ):
            raise PermissionError("authenticated audit actor differs from approved reviewer")
        digest = sha256(_json_bytes(receipt)).hexdigest()
        connection = self._connect()
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    """SELECT current_approval_id FROM lhfm_rule_heads
                       WHERE tenant_id=%s AND legal_entity_id=%s
                         AND agreement_id=%s AND rule_id=%s FOR UPDATE""",
                    (tenant_id, legal_entity_id, agreement_id, rule_id),
                )
                head = cursor.fetchone()
                if (not head or not head["current_approval_id"]
                        or not hmac.compare_digest(
                            str(head["current_approval_id"]), verified["approval_id"])):
                    raise PermissionError("contract rule is superseded or has no reviewed lineage")
                cursor.execute(
                    """SELECT reviewer_id, rule_sha256, document_sha256,
                              receipt_sha256, source_revision_id, rule_revision,
                              agreement_id, rule_id, state
                       FROM lhfm_approval_records
                       WHERE approval_id=%s AND tenant_id=%s
                         AND legal_entity_id=%s FOR UPDATE""",
                    (receipt["approval_id"], tenant_id, legal_entity_id),
                )
                record = cursor.fetchone()
                if record is None or record["state"] != "ACTIVE":
                    raise PermissionError("approval missing or revoked at audit dispatch")
                for name, expected in (
                    ("reviewer_id", verified["reviewer_id"]),
                    ("rule_sha256", verified["rule_sha256"]),
                    ("document_sha256", verified["document_sha256"]),
                    ("receipt_sha256", digest),
                    ("source_revision_id", verified["source_revision_id"]),
                    ("rule_revision", revision),
                    ("agreement_id", agreement_id),
                    ("rule_id", rule_id),
                ):
                    if not isinstance(record.get(name), str) or not hmac.compare_digest(
                        record[name], expected
                    ):
                        raise PermissionError("stored contract revision differs: " + name)
                cursor.execute(
                    """SELECT role, active FROM lhfm_reviewer_grants
                       WHERE tenant_id=%s AND legal_entity_id=%s
                         AND reviewer_id=%s FOR UPDATE""",
                    (tenant_id, legal_entity_id, record["reviewer_id"]),
                )
                grant = cursor.fetchone()
                if not grant or grant["role"] != "contract_reviewer" or not grant["active"]:
                    raise PermissionError("reviewer grant revoked before audit dispatch")
                yield {**verified, "revocation_status": "ACTIVE_LOCKED_AT_DISPATCH",
                       "reviewer_grant": "ACTIVE_AT_DISPATCH",
                       "rule_lifecycle": "CURRENT_APPROVED_REVISION"}
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()
