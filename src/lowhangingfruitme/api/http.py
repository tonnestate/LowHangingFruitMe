"""Bounded, authenticated FastAPI audit resource API.

This is an operator-provisioned bundle-to-report pilot, NOT a public document
upload or production portal. It never accepts user-controlled filesystem paths,
approval signatures, secrets, source controls or claimed reviewer identities.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Annotated
from uuid import UUID, uuid4

from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field

from ..approval_service import AuthenticatedApprovalService
from .store import BundleNotFound, PrivateAuditStore, RunConflict


class AuditRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    bundle_id: UUID
    tenant_id: str = Field(min_length=1, max_length=128, pattern=r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")
    legal_entity_id: str = Field(min_length=1, max_length=128, pattern=r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")


def create_app(*, service: AuthenticatedApprovalService,
               store: PrivateAuditStore) -> FastAPI:
    """Dependencies injected by a trusted bootstrap, never from HTTP input."""
    app = FastAPI(
        title="LowHangingFruitMe Audit API", version="0.8.0",
        docs_url=None, redoc_url=None, openapi_url=None,
    )

    @app.middleware("http")
    async def safe_response_headers(request: Request, call_next):
        response = await call_next(request)
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-Correlation-ID"] = str(uuid4())
        return response

    def access_token(authorization: Annotated[str | None, Header()] = None) -> str:
        if not authorization or len(authorization) > 8200:
            raise HTTPException(status_code=401, detail={"code":"AUTH_REQUIRED"})
        parts = authorization.split(" ")
        if len(parts) != 2 or parts[0] != "Bearer" or not parts[1]:
            raise HTTPException(status_code=401, detail={"code":"INVALID_AUTH_HEADER"})
        return parts[1]

    def authorized_actor(token: str, *, tenant: str, entity: str) -> str:
        try:
            principal = service.verifier.verify(token)
        except (PermissionError, ValueError) as exc:
            raise HTTPException(status_code=401, detail={"code":"INVALID_ACCESS_TOKEN"}) from exc
        try:
            principal.require_scope("lhfm:audit:execute")
            service.registry.require_scoped_reviewer(
                tenant_id=tenant, legal_entity_id=entity,
                actor_id=principal.subject,
            )
        except PermissionError as exc:
            raise HTTPException(status_code=403, detail={"code":"NOT_AUTHORIZED"}) from exc
        return principal.subject

    @app.get("/healthz", include_in_schema=False)
    def health():
        return {"status":"alive"}

    @app.post("/v1/audits", status_code=201)
    def submit(
        body: AuditRequest, request: Request,
        token: str = Depends(access_token),
        idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
    ):
        if not idempotency_key:
            raise HTTPException(status_code=400, detail={"code":"IDEMPOTENCY_KEY_REQUIRED"})
        try:
            key = str(UUID(idempotency_key))
        except (ValueError, TypeError, AttributeError) as exc:
            raise HTTPException(status_code=400, detail={"code":"INVALID_IDEMPOTENCY_KEY"}) from exc
        if key != idempotency_key.lower():
            raise HTTPException(status_code=400, detail={"code":"NON_CANONICAL_IDEMPOTENCY_KEY"})
        tenant, entity = body.tenant_id, body.legal_entity_id
        actor = authorized_actor(token, tenant=tenant, entity=entity)
        bundle_id = str(body.bundle_id)
        try:
            bundle = store.load_bundle(
                bundle_id=bundle_id, tenant_id=tenant,
                legal_entity_id=entity, reviewer_id=actor,
            )
            reserved, created = store.reserve_run(
                tenant_id=tenant, legal_entity_id=entity,
                reviewer_id=actor, bundle_id=bundle_id, idempotency_key=key,
            )
        except BundleNotFound as exc:
            raise HTTPException(status_code=404, detail={"code":"BUNDLE_NOT_FOUND"}) from exc
        except RunConflict as exc:
            raise HTTPException(status_code=409, detail={"code":"IDEMPOTENCY_CONFLICT"}) from exc
        if not created:
            response_code = 202 if reserved["status"] == "PROCESSING" else 200
            return JSONResponse(
                status_code=response_code,
                content={"audit_id":reserved["audit_id"],"status":reserved["status"],
                         "audit_executed":bool(reserved["audit_executed"]),
                         "replayed":True},
            )
        audit_id = reserved["audit_id"]
        try:
            with store.snapshot(bundle) as files:
                report = service.audit_csv(
                    token,
                    rule_path=files["rule"],
                    transactions_path=files["transactions"],
                    settlements_path=files["settlements"],
                    contract_source_path=files["contract"],
                    approval_receipt=bundle["approval_receipt"],
                    source_system=bundle["source_system"],
                    controls=bundle["controls"],
                    completeness=bundle["completeness"],
                    tenant_id=tenant, legal_entity_id=entity,
                )
            store.finish_run(audit_id=audit_id, report=report)
        except Exception as exc:
            store.fail_run(audit_id=audit_id)
            # Never expose source paths, HMAC data, tracebacks or financial inputs.
            raise HTTPException(
                status_code=503, detail={"code":"AUDIT_EXECUTION_FAILED"},
            ) from exc
        state = "COMPLETED" if report.get("audit_executed") is True else "NEEDS_REVIEW"
        return {"audit_id":audit_id, "status":state,
                "audit_executed":bool(report.get("audit_executed")),
                "replayed":False}

    @app.get("/v1/audits/{audit_id}")
    def get_audit(
        audit_id: UUID,
        tenant_id: Annotated[str, Query(min_length=1, max_length=128,
                pattern=r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")],
        legal_entity_id: Annotated[str, Query(min_length=1, max_length=128,
                pattern=r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")],
        token: str = Depends(access_token),
    ):
        actor = authorized_actor(token, tenant=tenant_id, entity=legal_entity_id)
        try:
            return store.get_run(audit_id=str(audit_id), tenant_id=tenant_id,
                                 legal_entity_id=legal_entity_id, reviewer_id=actor)
        except BundleNotFound as exc:
            raise HTTPException(status_code=404, detail={"code":"AUDIT_NOT_FOUND"}) from exc

    return app


def create_app_from_environment() -> FastAPI:
    """Use: uvicorn lowhangingfruitme.api.http:create_app_from_environment --factory.

    Private trusted configuration is required before constructing the app.
    This does not set up TLS, a public upload service or production customer IAM.
    """
    root = os.environ.get("LHFM_API_SOURCE_ROOT")
    if not root:
        raise RuntimeError("LHFM_API_SOURCE_ROOT required")
    service = AuthenticatedApprovalService.from_environment()
    store = PrivateAuditStore(registry=service.registry, source_root=root)
    return create_app(service=service, store=store)
