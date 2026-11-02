"""Authenticated approval operations for a future private HTTP boundary.

The public adapter must pass the raw *access token* to this service, NOT a
user_id or tenant role claimed by an HTTP client. Token verification is strict
(RFC9068 at+jwt), followed by scope and DB role checks. There is no login or
network API in this package.
"""
from __future__ import annotations

from hashlib import sha256
import json
import os
from pathlib import Path
from typing import Any

from .approval import key_from_environment
from .approval_registry import ApprovalRegistry
from .auth import AccessTokenVerifier, VerifiedPrincipal
from .intake import audit_from_csv


class AuthenticatedApprovalService:
    def __init__(
        self, *, verifier: AccessTokenVerifier,
        registry: ApprovalRegistry, approval_key: bytes,
    ) -> None:
        self.verifier = verifier
        self.registry = registry
        self.approval_key = approval_key

    @classmethod
    def from_environment(cls) -> "AuthenticatedApprovalService":
        required = ("LHFM_OIDC_ISSUER", "LHFM_OIDC_AUDIENCE",
                    "LHFM_OIDC_JWKS_FILE", "LHFM_OIDC_ALLOWED_CLIENT_IDS")
        if any(not os.environ.get(k) for k in required):
            raise RuntimeError("trusted OIDC issuer/audience/public JWKS/client configuration required")
        verifier = AccessTokenVerifier.from_trusted_file(
            issuer=os.environ["LHFM_OIDC_ISSUER"],
            audience=os.environ["LHFM_OIDC_AUDIENCE"],
            jwks_path=os.environ["LHFM_OIDC_JWKS_FILE"],
            allowed_client_ids=tuple(
                x.strip() for x in os.environ["LHFM_OIDC_ALLOWED_CLIENT_IDS"].split(",")
            ),
        )
        return cls(
            verifier=verifier, registry=ApprovalRegistry.from_environment(),
            approval_key=key_from_environment(),
        )

    def _verified_actor(
        self, access_token: str, *, scope: str, tenant_id: str,
        legal_entity_id: str,
    ) -> VerifiedPrincipal:
        actor = self.verifier.verify(access_token)
        actor.require_scope(scope)
        self.registry.require_scoped_reviewer(
            tenant_id=tenant_id, legal_entity_id=legal_entity_id,
            actor_id=actor.subject,
        )
        return actor

    def register(
        self, access_token: str, *, receipt: dict[str, Any],
        rule: dict[str, Any], document_sha256: str,
        tenant_id: str, legal_entity_id: str,
    ) -> None:
        actor = self._verified_actor(
            access_token, scope="lhfm:approval:write",
            tenant_id=tenant_id, legal_entity_id=legal_entity_id,
        )
        if receipt.get("reviewer_id") != actor.subject:
            raise PermissionError("authenticated signer differs from receipt reviewer")
        self.registry.register(
            receipt, rule=rule, key=self.approval_key,
            document_sha256=document_sha256,
            tenant_id=tenant_id, legal_entity_id=legal_entity_id,
            authenticated_actor_id=actor.subject,
        )

    def revoke(
        self, access_token: str, *, approval_id: str,
        tenant_id: str, legal_entity_id: str,
    ) -> bool:
        actor = self._verified_actor(
            access_token, scope="lhfm:approval:revoke",
            tenant_id=tenant_id, legal_entity_id=legal_entity_id,
        )
        return self.registry.revoke(
            approval_id, tenant_id=tenant_id,
            legal_entity_id=legal_entity_id,
            authenticated_actor_id=actor.subject,
        )

    def audit_csv(
        self, access_token: str, *,
        rule_path: str | Path,
        transactions_path: str | Path,
        settlements_path: str | Path,
        contract_source_path: str | Path,
        approval_receipt: dict[str, Any],
        source_system: str,
        controls: dict[str, Any],
        completeness: dict[str, bool],
        tenant_id: str,
        legal_entity_id: str,
    ) -> dict[str, Any]:
        """Authorize *before* reading files and again inside locked dispatch.

        Only an already authorized original contract reviewer can execute
        this initial vertical slice; broader roles are a future design.
        """
        actor = self._verified_actor(
            access_token, scope="lhfm:audit:execute",
            tenant_id=tenant_id, legal_entity_id=legal_entity_id,
        )
        if approval_receipt.get("reviewer_id") != actor.subject:
            raise PermissionError("only the authorizing contract reviewer may run this audit")

        def recheck() -> None:
            latest = self.verifier.verify(access_token)
            latest.require_scope("lhfm:audit:execute")
            if latest.subject != actor.subject or latest.token_id != actor.token_id:
                raise PermissionError("access token changed across dispatch boundary")

        return audit_from_csv(
            rule_path, transactions_path, settlements_path,
            source_system=source_system, completeness=completeness,
            controls=controls, approval_receipt=approval_receipt,
            approval_key=self.approval_key,
            approval_scope={"tenant_id": tenant_id, "legal_entity_id": legal_entity_id},
            contract_source_path=contract_source_path,
            approval_registry=self.registry,
            approval_actor_id=actor.subject,
            reauthorize_before_dispatch=recheck,
        )
