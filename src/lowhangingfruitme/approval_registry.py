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

    def register(self, receipt: dict[str, Any], *, rule: dict[str, Any],
                 key: bytes, document_sha256: str,
                 tenant_id: str, legal_entity_id: str,
                 authenticated_actor_id: str) -> None:
        """Persist approval only for an active reviewer grant.

        IMPORTANT: authenticated_actor_id is an assertion of a TRUSTED caller,
        not validated against a login provider by this library.
        """
        actor = self._require_actor(authenticated_actor_id)
        verified = verify_approval(
            receipt, rule, key=key, tenant_id=tenant_id,
            legal_entity_id=legal_entity_id, document_sha256=document_sha256,
        )
        if not hmac.compare_digest(actor, verified["reviewer_id"]):
            raise PermissionError("receipt reviewer differs from authenticated actor")
        digest = sha256(_json_bytes(receipt)).hexdigest()
        connection = self._connect()
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    """SELECT role, active FROM lhfm_reviewer_grants
                       WHERE tenant_id=%s AND legal_entity_id=%s AND reviewer_id=%s
                       FOR UPDATE""",
                    (tenant_id, legal_entity_id, actor),
                )
                role = cursor.fetchone()
                if not role or role["role"] != "contract_reviewer" or not role["active"]:
                    raise PermissionError("reviewer does not have an active scoped grant")
                cursor.execute(
                    """INSERT INTO lhfm_approval_records
                       (approval_id, tenant_id, legal_entity_id, reviewer_id,
                        rule_sha256, document_sha256, receipt_sha256, state)
                       VALUES (%s,%s,%s,%s,%s,%s,%s,'ACTIVE')""",
                    (receipt["approval_id"], tenant_id, legal_entity_id, actor,
                     verified["rule_sha256"], verified["document_sha256"], digest),
                )
                cursor.execute(
                    """INSERT INTO lhfm_approval_events
                       (approval_id, tenant_id, legal_entity_id, actor_id, event_type)
                       VALUES (%s,%s,%s,%s,'ISSUED')""",
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
                cursor.execute(
                    """SELECT role, active FROM lhfm_reviewer_grants
                       WHERE tenant_id=%s AND legal_entity_id=%s AND reviewer_id=%s
                       FOR UPDATE""",
                    (tenant_id, legal_entity_id, actor),
                )
                role = cursor.fetchone()
                if not role or role["role"] != "contract_reviewer" or not role["active"]:
                    raise PermissionError("actor cannot revoke in this tenant/entity")
                cursor.execute(
                    """SELECT state FROM lhfm_approval_records
                       WHERE approval_id=%s AND tenant_id=%s AND legal_entity_id=%s
                       FOR UPDATE""",
                    (approval_id, tenant_id, legal_entity_id),
                )
                row = cursor.fetchone()
                if row is None:
                    raise ValueError("approval not found in authenticated scope")
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
              legal_entity_id: str) -> Iterator[dict[str, str]]:
        """Hold an InnoDB row lock while the actual calculation executes.

        This guarantees the revoke transaction cannot commit during this guard.
        It does not make ERP snapshot import itself atomic; source files must
        be immutable/snapshotted by the trusted caller.
        """
        verified = verify_approval(
            receipt, rule, key=key, tenant_id=tenant_id,
            legal_entity_id=legal_entity_id, document_sha256=document_sha256,
        )
        digest = sha256(_json_bytes(receipt)).hexdigest()
        connection = self._connect()
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    """SELECT reviewer_id, rule_sha256, document_sha256,
                              receipt_sha256, state
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
                ):
                    if not hmac.compare_digest(record[name], expected):
                        raise PermissionError("stored approval content differs: " + name)
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
                       "reviewer_grant": "ACTIVE_AT_DISPATCH"}
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()
