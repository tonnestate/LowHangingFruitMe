"""Bounded, authenticated FastAPI audit resource API.

This is an operator-provisioned bundle-to-report pilot, NOT a public document
upload or production portal. It never accepts user-controlled filesystem paths,
approval signatures, secrets, source controls or claimed reviewer identities.
"""
from __future__ import annotations

import os
from pathlib import Path
from contextlib import nullcontext
from typing import Annotated, Literal, Any
from uuid import UUID, uuid4

from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel, ConfigDict, Field

from ..approval_service import AuthenticatedApprovalService
from ..invoices import extract_invoice_preview
from .store import BundleNotFound, PrivateAuditStore, RunConflict
from .promotion import ReviewedBundleService, ReviewRequired, RuleSemanticReviewRequired
from .candidates import (ContractCandidateService, CandidateNotFound,
                         CandidateConflict, CandidateUnavailable)
from .recovery import RecoveryLedger, CaseConflict
from .reports import customer_case, render_export, ReportNotReady
from .uploads import (ClamAVScanner, MAX_UPLOAD, ScannerUnavailable,
                      UploadRejected, UploadService)


class AuditRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    bundle_id: UUID
    tenant_id: str = Field(min_length=1, max_length=128, pattern=r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")
    legal_entity_id: str = Field(min_length=1, max_length=128, pattern=r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")


class UploadIntentRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    tenant_id: str = Field(min_length=1, max_length=128, pattern=r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")
    legal_entity_id: str = Field(min_length=1, max_length=128, pattern=r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")
    kind: Literal["ERP_CSV", "ERP_XLSX", "INVOICE_XML", "CONTRACT_PDF", "CONTRACT_DOCX", "RECOVERY_PDF"]
    byte_size: int = Field(strict=True, ge=1, le=MAX_UPLOAD)
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")


class ReviewedBundleRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    tenant_id: str = Field(min_length=1, max_length=128, pattern=r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")
    legal_entity_id: str = Field(min_length=1, max_length=128, pattern=r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")
    transactions_upload_id: UUID
    settlements_upload_id: UUID
    contract_upload_id: UUID
    source_system: str = Field(min_length=1, max_length=128, pattern=r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")
    source_revision_id: str = Field(min_length=1, max_length=128)
    rule: dict[str, Any]
    transaction_plan: dict[str, Any]
    settlement_plan: dict[str, Any]
    controls: dict[str, Any] | None
    completeness: dict[str, bool]
    confirm_contract_review: Literal[True]
    confirm_mapping_review: Literal[True]
    candidate_id: UUID | None = None


class CandidateExtractRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    tenant_id: str = Field(min_length=1,max_length=128,pattern=r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")
    legal_entity_id: str = Field(min_length=1,max_length=128,pattern=r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")
    contract_upload_id: UUID
    agreement_id: str = Field(min_length=1,max_length=128)
    rule_id: str = Field(min_length=1,max_length=128)
    rule_revision: str = Field(min_length=1,max_length=128)
    source_revision_id: str = Field(min_length=1,max_length=128)


class CandidateReviewRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    tenant_id: str = Field(min_length=1,max_length=128,pattern=r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")
    legal_entity_id: str = Field(min_length=1,max_length=128,pattern=r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")
    rule: dict[str,Any]
    confirm_clause_review: Literal[True]


class RecoveryEventRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    tenant_id: str = Field(min_length=1,max_length=128,pattern=r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")
    legal_entity_id: str = Field(min_length=1,max_length=128,pattern=r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")
    kind: Literal["REALIZATION", "REVERSAL"]
    amount_net: str = Field(pattern=r"^(?:0|[1-9][0-9]{0,10})\.[0-9]{2}$")
    evidence_upload_id: UUID
    reverses_event_id: UUID | None = None


class FinanceReviewRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    tenant_id: str = Field(min_length=1,max_length=128,pattern=r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")
    legal_entity_id: str = Field(min_length=1,max_length=128,pattern=r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")
    decision: Literal["CONFIRM", "REJECT"]
    confirm_evidence_review: Literal[True]


class CaseStatusRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    tenant_id: str = Field(min_length=1,max_length=128,pattern=r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")
    legal_entity_id: str = Field(min_length=1,max_length=128,pattern=r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")
    directive: Literal["DISPUTED", "CLOSED", "OPEN"]
    reason: str = Field(min_length=1,max_length=200)


def create_app(*, service: AuthenticatedApprovalService,
               store: PrivateAuditStore,
               uploads: UploadService | None = None,
               promotion: ReviewedBundleService | None = None,
               recovery: RecoveryLedger | None = None,
               candidates: ContractCandidateService | None = None) -> FastAPI:
    """Dependencies injected by a trusted bootstrap, never from HTTP input."""
    app = FastAPI(
        title="LowHangingFruitMe Audit API", version="0.12.0",
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

    def authorized_actor(token: str, *, tenant: str, entity: str,
                         required_scope: str = "lhfm:audit:execute") -> str:
        try:
            principal = service.verifier.verify(token)
        except (PermissionError, ValueError) as exc:
            raise HTTPException(status_code=401, detail={"code":"INVALID_ACCESS_TOKEN"}) from exc
        try:
            principal.require_scope(required_scope)
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

    @app.get("/readyz", include_in_schema=False)
    def readiness():
        """Operational check. Liveness is never proof of audit/upload readiness."""
        if (uploads is None or promotion is None or recovery is None
                or (promotion.require_candidate and candidates is None)
                or not isinstance(uploads.scanner, ClamAVScanner)):
            raise HTTPException(status_code=503, detail={"code": "NOT_READY"})
        try:
            from ..schema import require_operational_schema
            require_operational_schema(service.registry._connect)
            uploads.scanner.ping()
        except Exception as exc:
            # Do not expose DB structure, credentials or socket paths.
            raise HTTPException(status_code=503, detail={"code": "NOT_READY"}) from exc
        return {"status": "ready"}

    def configured_uploads() -> UploadService:
        if uploads is None:
            raise HTTPException(status_code=503, detail={"code":"UPLOAD_NOT_CONFIGURED"})
        return uploads

    @app.get("/v1/me")
    def get_verified_reviewer_identity(
        tenant_id: Annotated[str, Query(min_length=1,max_length=128,
            pattern=r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")],
        legal_entity_id: Annotated[str, Query(min_length=1,max_length=128,
            pattern=r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")],
        token: str = Depends(access_token),
    ):
        actor = authorized_actor(
            token,tenant=tenant_id,entity=legal_entity_id,
            required_scope="lhfm:upload:write",
        )
        principal = service.verifier.verify(token)
        return {"subject":actor,"tenant_id":tenant_id,
                "legal_entity_id":legal_entity_id,
                "scopes":sorted(principal.scopes)}

    @app.post("/v1/uploads", status_code=201)
    def create_upload_intent(
        body: UploadIntentRequest,
        token: str = Depends(access_token),
    ):
        actor = authorized_actor(
            token, tenant=body.tenant_id,
            entity=body.legal_entity_id, required_scope="lhfm:upload:write",
        )
        service_uploads = configured_uploads()
        return service_uploads.create_intent(
            tenant_id=body.tenant_id,
            legal_entity_id=body.legal_entity_id,
            reviewer_id=actor,
            kind=body.kind, byte_size=body.byte_size, digest=body.sha256,
        )

    @app.put("/v1/uploads/{upload_id}/content")
    async def upload_content(
        upload_id: UUID,
        request: Request,
        tenant_id: Annotated[str, Query(min_length=1, max_length=128,
                pattern=r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")],
        legal_entity_id: Annotated[str, Query(min_length=1, max_length=128,
                pattern=r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")],
        token: str = Depends(access_token),
    ):
        actor = authorized_actor(
            token, tenant=tenant_id, entity=legal_entity_id,
            required_scope="lhfm:upload:write",
        )
        service_uploads = configured_uploads()
        # Only raw bytes. Multipart filename and content-type claims are not
        # used as paths or financial classification sources.
        if request.headers.get("content-type", "").split(";", 1)[0].strip().lower() != "application/octet-stream":
            raise HTTPException(status_code=415, detail={"code":"RAW_UPLOAD_REQUIRED"})
        length = request.headers.get("content-length")
        if length is not None:
            if not length.isascii() or not length.isdigit():
                raise HTTPException(status_code=400, detail={"code":"INVALID_CONTENT_LENGTH"})
            if int(length) > MAX_UPLOAD:
                raise HTTPException(status_code=413, detail={"code":"UPLOAD_TOO_LARGE"})
        try:
            return await service_uploads.receive(
                upload_id=str(upload_id),
                tenant_id=tenant_id, legal_entity_id=legal_entity_id,
                reviewer_id=actor, chunks=request.stream(),
            )
        except UploadRejected as exc:
            raise HTTPException(status_code=422, detail={"code":"UPLOAD_REJECTED"}) from exc
        except ScannerUnavailable as exc:
            raise HTTPException(status_code=503, detail={"code":"MALWARE_SCANNER_UNAVAILABLE"}) from exc

    @app.get("/v1/uploads/{upload_id}")
    def get_upload(
        upload_id: UUID,
        tenant_id: Annotated[str, Query(min_length=1, max_length=128,
                pattern=r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")],
        legal_entity_id: Annotated[str, Query(min_length=1, max_length=128,
                pattern=r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")],
        token: str = Depends(access_token),
    ):
        actor = authorized_actor(
            token, tenant=tenant_id, entity=legal_entity_id,
            required_scope="lhfm:upload:write",
        )
        service_uploads = configured_uploads()
        try:
            record = service_uploads.get_upload(
                upload_id=str(upload_id), tenant_id=tenant_id,
                legal_entity_id=legal_entity_id, reviewer_id=actor,
            )
        except BundleNotFound as exc:
            raise HTTPException(status_code=404, detail={"code":"UPLOAD_NOT_FOUND"}) from exc
        return {**record, "usable_for_audit": False}

    @app.get("/v1/uploads/{upload_id}/invoice-preview")
    def get_verified_xml_invoice_preview(
        upload_id: UUID,
        tenant_id: Annotated[str, Query(min_length=1,max_length=128,
            pattern=r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")],
        legal_entity_id: Annotated[str, Query(min_length=1,max_length=128,
            pattern=r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")],
        token: str = Depends(access_token),
    ):
        actor=authorized_actor(
            token,tenant=tenant_id,entity=legal_entity_id,
            required_scope="lhfm:upload:write",
        )
        service_uploads=configured_uploads()
        try:
            with service_uploads.snapshot_clean(
                upload_id=str(upload_id),tenant_id=tenant_id,
                legal_entity_id=legal_entity_id,reviewer_id=actor,
                accepted_kinds=("INVOICE_XML",),
            ) as (source,_):
                return extract_invoice_preview(source)
        except BundleNotFound as exc:
            raise HTTPException(status_code=404,detail={"code":"UPLOAD_NOT_FOUND"}) from exc
        except (UploadRejected,ValueError) as exc:
            raise HTTPException(status_code=422,detail={"code":"INVOICE_PREVIEW_REQUIRES_REVIEW"}) from exc

    @app.get("/v1/uploads/{upload_id}/inspect")
    def inspect_upload_for_mapping(
        upload_id: UUID,
        tenant_id: Annotated[str, Query(min_length=1, max_length=128,
                pattern=r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")],
        legal_entity_id: Annotated[str, Query(min_length=1, max_length=128,
                pattern=r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")],
        dataset: Literal["transactions", "settlements"],
        sheet_name: str | None = None,
        token: str = Depends(access_token),
    ):
        actor = authorized_actor(
            token, tenant=tenant_id, entity=legal_entity_id,
            required_scope="lhfm:upload:write",
        )
        if promotion is None:
            raise HTTPException(status_code=503, detail={"code":"BUNDLE_REVIEW_UNAVAILABLE"})
        try:
            return promotion.inspect(
                token, tenant_id=tenant_id, legal_entity_id=legal_entity_id,
                upload_id=str(upload_id), dataset=dataset, sheet_name=sheet_name,
            )
        except BundleNotFound as exc:
            raise HTTPException(status_code=404, detail={"code":"UPLOAD_NOT_FOUND"}) from exc
        except (UploadRejected, ValueError) as exc:
            raise HTTPException(status_code=422, detail={"code":"SOURCE_INSPECTION_FAILED"}) from exc

    @app.post("/v1/contract-candidates", status_code=201)
    def extract_contract_candidate(
        body: CandidateExtractRequest, token: str = Depends(access_token),
    ):
        authorized_actor(
            token,tenant=body.tenant_id,entity=body.legal_entity_id,
            required_scope="lhfm:approval:write",
        )
        if candidates is None:
            raise HTTPException(status_code=503,detail={"code":"CANDIDATES_UNAVAILABLE"})
        try:
            return candidates.extract(
                token,tenant_id=body.tenant_id,legal_entity_id=body.legal_entity_id,
                contract_upload_id=str(body.contract_upload_id),
                agreement_id=body.agreement_id,rule_id=body.rule_id,
                rule_revision=body.rule_revision,
                source_revision_id=body.source_revision_id,
            )
        except CandidateUnavailable as exc:
            raise HTTPException(status_code=503,detail={"code":"EXTRACTION_UNAVAILABLE"}) from exc
        except RuntimeError as exc:
            raise HTTPException(status_code=503,detail={"code":"EXTRACTION_FAILED"}) from exc
        except BundleNotFound as exc:
            raise HTTPException(status_code=404,detail={"code":"CONTRACT_UPLOAD_NOT_FOUND"}) from exc
        except CandidateConflict as exc:
            raise HTTPException(status_code=409,detail={"code":"CANDIDATE_CONFLICT"}) from exc
        except (UploadRejected,ValueError) as exc:
            raise HTTPException(status_code=422,detail={"code":"CONTRACT_EVIDENCE_INVALID"}) from exc

    @app.get("/v1/contract-candidates/{candidate_id}")
    def read_contract_candidate(
        candidate_id: UUID,
        tenant_id: Annotated[str,Query(min_length=1,max_length=128,
            pattern=r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")],
        legal_entity_id: Annotated[str,Query(min_length=1,max_length=128,
            pattern=r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")],
        token: str = Depends(access_token),
    ):
        authorized_actor(token,tenant=tenant_id,entity=legal_entity_id,
                         required_scope="lhfm:approval:write")
        if candidates is None:
            raise HTTPException(status_code=503,detail={"code":"CANDIDATES_UNAVAILABLE"})
        try:
            return candidates.get(
                token,candidate_id=str(candidate_id),
                tenant_id=tenant_id,legal_entity_id=legal_entity_id,
            )
        except CandidateNotFound as exc:
            raise HTTPException(status_code=404,detail={"code":"CANDIDATE_NOT_FOUND"}) from exc

    @app.post("/v1/contract-candidates/{candidate_id}/review")
    def review_contract_candidate(
        candidate_id: UUID, body: CandidateReviewRequest,
        token: str = Depends(access_token),
    ):
        authorized_actor(token,tenant=body.tenant_id,entity=body.legal_entity_id,
                         required_scope="lhfm:approval:write")
        if candidates is None:
            raise HTTPException(status_code=503,detail={"code":"CANDIDATES_UNAVAILABLE"})
        try:
            return candidates.review(
                token,candidate_id=str(candidate_id),
                tenant_id=body.tenant_id,legal_entity_id=body.legal_entity_id,
                rule=body.rule,confirm_clause_review=body.confirm_clause_review,
            )
        except CandidateNotFound as exc:
            raise HTTPException(status_code=404,detail={"code":"CANDIDATE_NOT_FOUND"}) from exc
        except CandidateConflict as exc:
            raise HTTPException(status_code=409,detail={"code":"CANDIDATE_REVIEW_REQUIRED"}) from exc

    @app.post("/v1/bundles", status_code=201)
    def approve_and_prepare_bundle(
        body: ReviewedBundleRequest, token: str = Depends(access_token),
    ):
        authorized_actor(
            token, tenant=body.tenant_id, entity=body.legal_entity_id,
            required_scope="lhfm:approval:write",
        )
        if promotion is None:
            raise HTTPException(status_code=503, detail={"code":"BUNDLE_REVIEW_UNAVAILABLE"})
        try:
            return promotion.prepare(
                token, tenant_id=body.tenant_id,
                legal_entity_id=body.legal_entity_id,
                transaction_upload_id=str(body.transactions_upload_id),
                settlement_upload_id=str(body.settlements_upload_id),
                contract_upload_id=str(body.contract_upload_id),
                transaction_plan=body.transaction_plan,
                settlement_plan=body.settlement_plan,
                rule=body.rule, source_system=body.source_system,
                source_revision_id=body.source_revision_id,
                controls=body.controls, completeness=body.completeness,
                confirm_contract_review=body.confirm_contract_review,
                confirm_mapping_review=body.confirm_mapping_review,
                candidate_id=str(body.candidate_id) if body.candidate_id else None,
            )
        except BundleNotFound as exc:
            raise HTTPException(status_code=404, detail={"code":"UPLOAD_NOT_FOUND"}) from exc
        except RuleSemanticReviewRequired as exc:
            raise HTTPException(
                status_code=422,
                detail={"code":"RULE_SEMANTICS_NEEDS_REVIEW",
                        "next_action":"CHECK_ORIGINAL_CONTRACT_AND_CONFIRM_TIER_APPLICATION"},
            ) from exc
        except (ReviewRequired, UploadRejected, CandidateConflict, CandidateNotFound, ValueError) as exc:
            raise HTTPException(status_code=422, detail={"code":"BUNDLE_REVIEW_FAILED"}) from exc
        except PermissionError as exc:
            raise HTTPException(status_code=403, detail={"code":"NOT_AUTHORIZED"}) from exc

    @app.post("/v1/audits/{audit_id}/recovery-events",status_code=201)
    def record_recovery(
        audit_id: UUID, body: RecoveryEventRequest,
        token: str = Depends(access_token),
        idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
    ):
        actor = authorized_actor(
            token,tenant=body.tenant_id,entity=body.legal_entity_id,
            required_scope="lhfm:recovery:record",
        )
        if recovery is None:
            raise HTTPException(status_code=503,detail={"code":"RECOVERY_UNAVAILABLE"})
        if not idempotency_key:
            raise HTTPException(status_code=400,detail={"code":"IDEMPOTENCY_KEY_REQUIRED"})
        try:
            key=str(UUID(idempotency_key))
            if key!=idempotency_key.lower():
                raise ValueError("noncanonical idempotency key")
        except (ValueError,TypeError) as exc:
            raise HTTPException(status_code=400,detail={"code":"INVALID_IDEMPOTENCY_KEY"}) from exc
        try:
            return recovery.record(
                audit_id=str(audit_id),tenant_id=body.tenant_id,
                legal_entity_id=body.legal_entity_id,reviewer_id=actor,
                kind=body.kind,amount_net=body.amount_net,
                evidence_upload_id=str(body.evidence_upload_id),
                idempotency_key=key,
                reverses_event_id=str(body.reverses_event_id)
                    if body.reverses_event_id else None,
            )
        except BundleNotFound as exc:
            raise HTTPException(status_code=404,detail={"code":"RECOVERY_SOURCE_NOT_FOUND"}) from exc
        except CaseConflict as exc:
            raise HTTPException(status_code=409,detail={"code":"RECOVERY_CONFLICT"}) from exc
        except (ValueError,UploadRejected) as exc:
            raise HTTPException(status_code=422,detail={"code":"RECOVERY_EVIDENCE_INVALID"}) from exc

    @app.get("/v1/audits/{audit_id}/fee-ledger")
    def read_fee_ledger(
        audit_id: UUID,
        tenant_id: Annotated[str, Query(min_length=1,max_length=128,
            pattern=r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")],
        legal_entity_id: Annotated[str, Query(min_length=1,max_length=128,
            pattern=r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")],
        token: str = Depends(access_token),
    ):
        actor=authorized_actor(
            token,tenant=tenant_id,entity=legal_entity_id,
            required_scope="lhfm:recovery:read",
        )
        if recovery is None:
            raise HTTPException(status_code=503,detail={"code":"RECOVERY_UNAVAILABLE"})
        try:
            return recovery.ledger(
                audit_id=str(audit_id),tenant_id=tenant_id,
                legal_entity_id=legal_entity_id,reviewer_id=actor,
            )
        except BundleNotFound as exc:
            raise HTTPException(status_code=404,detail={"code":"AUDIT_NOT_FOUND"}) from exc
        except CaseConflict as exc:
            raise HTTPException(status_code=409,detail={"code":"LEDGER_REVIEW_REQUIRED"}) from exc

    @app.post("/v1/audits/{audit_id}/case-status", status_code=201)
    def record_case_status(
        audit_id: UUID, body: CaseStatusRequest, token: str = Depends(access_token),
    ):
        if recovery is None:
            raise HTTPException(status_code=503, detail={"code":"RECOVERY_UNAVAILABLE"})
        try:
            principal = service.verifier.verify(token)
        except (PermissionError, ValueError) as exc:
            raise HTTPException(status_code=401, detail={"code":"INVALID_ACCESS_TOKEN"}) from exc
        try:
            principal.require_scope("lhfm:recovery:verify")
            return recovery.annotate_status(
                audit_id=str(audit_id), tenant_id=body.tenant_id,
                legal_entity_id=body.legal_entity_id,
                finance_actor_id=principal.subject,
                directive=body.directive, reason=body.reason,
            )
        except PermissionError as exc:
            raise HTTPException(status_code=403, detail={"code":"FINANCE_NOT_AUTHORIZED"}) from exc
        except BundleNotFound as exc:
            raise HTTPException(status_code=404, detail={"code":"RECOVERY_CASE_NOT_FOUND"}) from exc
        except CaseConflict as exc:
            raise HTTPException(status_code=409, detail={"code":"CASE_STATUS_CONFLICT"}) from exc
        except ValueError as exc:
            raise HTTPException(status_code=422, detail={"code":"INVALID_CASE_STATUS"}) from exc

    @app.post("/v1/recovery-events/{event_id}/review")
    def verify_recovery(
        event_id: UUID, body: FinanceReviewRequest,
        token: str = Depends(access_token),
    ):
        if recovery is None:
            raise HTTPException(status_code=503,detail={"code":"RECOVERY_UNAVAILABLE"})
        try:
            principal=service.verifier.verify(token)
        except (PermissionError,ValueError) as exc:
            raise HTTPException(status_code=401,detail={"code":"INVALID_ACCESS_TOKEN"}) from exc
        try:
            principal.require_scope("lhfm:recovery:verify")
            recovery.require_finance_grant(
                tenant_id=body.tenant_id,legal_entity_id=body.legal_entity_id,
                finance_actor_id=principal.subject,
            )
        except PermissionError as exc:
            raise HTTPException(status_code=403,detail={"code":"FINANCE_NOT_AUTHORIZED"}) from exc
        try:
            return recovery.resolve(
                event_id=str(event_id),tenant_id=body.tenant_id,
                legal_entity_id=body.legal_entity_id,
                finance_actor_id=principal.subject,
                confirmed=body.decision=="CONFIRM",
            )
        except BundleNotFound as exc:
            raise HTTPException(status_code=404,detail={"code":"RECOVERY_EVENT_NOT_FOUND"}) from exc
        except PermissionError as exc:
            raise HTTPException(status_code=403,detail={"code":"FINANCE_NOT_AUTHORIZED"}) from exc
        except CaseConflict as exc:
            raise HTTPException(status_code=409,detail={"code":"RECOVERY_CONFLICT"}) from exc
        except (ValueError,UploadRejected) as exc:
            raise HTTPException(status_code=422,detail={"code":"RECOVERY_EVIDENCE_INVALID"}) from exc

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
            mapping_guard = nullcontext()
            if bundle.get("provenance") is not None:
                if promotion is None:
                    raise PermissionError("signed mapping verifier not configured")
                mapping_guard = promotion.mapping_registry.guard(
                    receipts=bundle.get("mapping_approvals"),
                    provenance=bundle["provenance"],
                    bundle_id=bundle_id, tenant_id=tenant,
                    legal_entity_id=entity, reviewer_id=actor,
                    approval_id=bundle["approval_receipt"]["approval_id"],
                )
            with mapping_guard:
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
            if bundle.get("provenance") is not None:
                report["input_provenance"] = bundle["provenance"]
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

    @app.get("/v1/audits/{audit_id}/report.{fmt}")
    def download_customer_report(
        audit_id: UUID,
        fmt: Literal["json", "pdf", "xlsx"],
        tenant_id: Annotated[str, Query(min_length=1, max_length=128,
            pattern=r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")],
        legal_entity_id: Annotated[str, Query(min_length=1, max_length=128,
            pattern=r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")],
        token: str = Depends(access_token),
    ):
        actor = authorized_actor(
            token, tenant=tenant_id, entity=legal_entity_id,
            required_scope="lhfm:audit:execute",
        )
        # A financial export contains realization information, therefore
        # the SAME verified access token must carry ledger read permission.
        try:
            service.verifier.verify(token).require_scope("lhfm:recovery:read")
        except (PermissionError, ValueError) as exc:
            raise HTTPException(status_code=403, detail={"code":"REPORT_SCOPE_REQUIRED"}) from exc
        if recovery is None:
            raise HTTPException(status_code=503, detail={"code":"RECOVERY_UNAVAILABLE"})
        try:
            run = store.get_run(
                audit_id=str(audit_id), tenant_id=tenant_id,
                legal_entity_id=legal_entity_id, reviewer_id=actor,
            )
            fee = recovery.ledger(
                audit_id=str(audit_id), tenant_id=tenant_id,
                legal_entity_id=legal_entity_id, reviewer_id=actor,
            )
            case = customer_case(run, fee)
            payload, mime = render_export(case, fmt)
        except BundleNotFound as exc:
            raise HTTPException(status_code=404, detail={"code":"AUDIT_NOT_FOUND"}) from exc
        except (ReportNotReady, CaseConflict) as exc:
            raise HTTPException(status_code=409, detail={"code":"REPORT_NOT_READY"}) from exc
        return Response(
            content=payload, media_type=mime,
            headers={"Content-Disposition":
                     f'attachment; filename="lhfm-{audit_id}.{fmt}"'},
        )

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
    # Read-only startup gate: never serve against missing SQL 007/008 structures.
    from ..schema import require_operational_schema
    require_operational_schema(service.registry._connect)
    store = PrivateAuditStore(registry=service.registry, source_root=root)
    upload_root = os.environ.get("LHFM_UPLOAD_ROOT")
    scanner_socket = os.environ.get("LHFM_CLAMD_UNIX_SOCKET")
    upload_service = None
    if upload_root and scanner_socket:
        source_root = Path(root).resolve(strict=True)
        private_upload_root = Path(upload_root).resolve(strict=True)
        if (private_upload_root == source_root or source_root in private_upload_root.parents
                or private_upload_root in source_root.parents):
            raise RuntimeError("untrusted upload storage must be outside audit source root")
        upload_service = UploadService(
            registry=service.registry, root=private_upload_root,
            scanner=ClamAVScanner(scanner_socket),
        )
    candidate_service = None
    if upload_service is not None:
        from ..docling_subprocess import DoclingSubprocessExtractor
        candidate_service = ContractCandidateService(
            service=service, uploads=upload_service,
            extractor=DoclingSubprocessExtractor(),
        )
    promotion_service = (
        ReviewedBundleService(
            service=service, uploads=upload_service, store=store,
            candidates=candidate_service, require_candidate=True,
        ) if upload_service is not None else None
    )
    recovery_service = (
        RecoveryLedger(registry=service.registry,store=store,uploads=upload_service)
        if upload_service is not None else None
    )
    return create_app(service=service, store=store,
                      uploads=upload_service,promotion=promotion_service,
                      recovery=recovery_service,candidates=candidate_service)
