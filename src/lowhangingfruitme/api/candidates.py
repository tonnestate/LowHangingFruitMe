"""Contract document extraction and accountable human review before HMAC approval.

This queue NEVER computes money or signs an approval. A source-bound proposal
can only reach APPROVED inside ApprovalRegistry.register's locked transaction.
All endpoint access requires a verified JWT subject AND an active exact-scope
MariaDB reviewer grant. The uploaded original is re-hashed on snapshot use.
"""
from __future__ import annotations

from hashlib import sha256
import json
from typing import Any, Callable
from pymysql.err import IntegrityError
from uuid import uuid4

from ..approval import rule_sha256
from ..approval_service import AuthenticatedApprovalService
from ..rebate import BonusRule
from .uploads import UploadService


class CandidateNotFound(LookupError):
    pass


class CandidateConflict(ValueError):
    pass


class CandidateDuplicate(CandidateConflict):
    """Duplicate persisted revision, not an invalid document citation."""


class CandidateUnavailable(RuntimeError):
    pass


class ContractCandidateService:
    def __init__(
        self, *, service: AuthenticatedApprovalService,
        uploads: UploadService, extractor: Callable[..., dict[str, Any]] | None,
    ) -> None:
        self.service = service
        self.uploads = uploads
        self.extractor = extractor
        self._connect = service.registry._connect

    def _actor(self, token: str, tenant_id: str, legal_entity_id: str) -> str:
        principal = self.service._verified_actor(
            token, scope="lhfm:approval:write",
            tenant_id=tenant_id, legal_entity_id=legal_entity_id,
        )
        principal.require_scope("lhfm:upload:write")
        return principal.subject

    @staticmethod
    def _evidence(segments: Any, document_digest: str) -> str:
        if not isinstance(segments, list) or not 1 <= len(segments) <= 2000:
            raise CandidateConflict("no bounded document evidence extracted")
        normalized = []
        citations = set()
        for segment in segments:
            if not isinstance(segment, dict):
                raise CandidateConflict("invalid document evidence")
            citation = segment.get("evidence_ref")
            text = segment.get("text")
            pages = segment.get("pages")
            if (not isinstance(citation, str) or len(citation) > 200
                    or not citation.startswith("sha256:" + document_digest + "#item=")
                    or citation in citations or not isinstance(text, str)
                    or not text.strip() or len(text) > 4000
                    or not isinstance(pages, list)
                    or len(pages) > 50
                    or any(type(x) is not int or not 1 <= x <= 50 for x in pages)):
                raise CandidateConflict("untrusted or malformed extraction provenance")
            citations.add(citation)
            normalized.append({
                "evidence_ref": citation, "text": text, "pages": pages,
            })
        evidence_json = json.dumps(
            normalized, ensure_ascii=False, separators=(",", ":"), allow_nan=False,
        )
        if len(evidence_json.encode("utf-8")) > 128 * 1024:
            raise CandidateConflict("extracted evidence exceeds review capacity")
        return evidence_json

    def extract(
        self, token: str, *, tenant_id: str, legal_entity_id: str,
        contract_upload_id: str, agreement_id: str, rule_id: str,
        rule_revision: str, source_revision_id: str,
    ) -> dict[str, Any]:
        actor = self._actor(token, tenant_id, legal_entity_id)
        if self.extractor is None:
            raise CandidateUnavailable("isolated document extractor not configured")
        if any(not isinstance(s, str) or not s.strip() or len(s) > 128
               for s in (agreement_id, rule_id, rule_revision, source_revision_id)):
            raise CandidateConflict("exact contract revision identity required")
        with self.uploads.snapshot_clean(
            upload_id=contract_upload_id, tenant_id=tenant_id,
            legal_entity_id=legal_entity_id, reviewer_id=actor,
            accepted_kinds=("CONTRACT_PDF",),
        ) as (path, upload):
            digest = upload["expected_sha256"]
            extracted = self.extractor(path)
        if not isinstance(extracted, dict) or extracted.get("file_sha256") != digest:
            raise CandidateConflict("parser source digest mismatch")
        evidence_json = self._evidence(extracted.get("segments"), digest)
        candidate_id = str(uuid4())
        db = self._connect()
        try:
            with db.cursor() as cur:
                cur.execute(
                    """INSERT INTO lhfm_contract_candidates
                       (candidate_id,tenant_id,legal_entity_id,reviewer_id,
                        contract_upload_id,agreement_id,rule_id,rule_revision,
                        source_revision_id,document_sha256,evidence_json,state)
                       VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'EXTRACTED')""",
                    (candidate_id,tenant_id,legal_entity_id,actor,
                     contract_upload_id,agreement_id,rule_id,rule_revision,
                     source_revision_id,digest,evidence_json),
                )
                cur.execute(
                    """INSERT INTO lhfm_contract_candidate_events
                       (candidate_id,tenant_id,legal_entity_id,actor_id,event_type)
                       VALUES (%s,%s,%s,%s,'EXTRACTED')""",
                    (candidate_id,tenant_id,legal_entity_id,actor),
                )
            db.commit()
        except IntegrityError as exc:
            db.rollback()
            raise CandidateDuplicate("candidate already exists for this document revision") from exc
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()
        return {"candidate_id": candidate_id, "state": "EXTRACTED",
                "document_sha256": digest, "segments": json.loads(evidence_json),
                "requires_human_confirmation": True}

    def get(
        self, token: str, *, candidate_id: str,
        tenant_id: str, legal_entity_id: str,
    ) -> dict[str, Any]:
        actor = self._actor(token, tenant_id, legal_entity_id)
        db = self._connect()
        try:
            with db.cursor() as cur:
                cur.execute(
                    """SELECT candidate_id,state,document_sha256,
                              agreement_id,rule_id,rule_revision,
                              source_revision_id,evidence_json,
                              reviewed_rule_json,approval_id
                       FROM lhfm_contract_candidates
                       WHERE candidate_id=%s AND tenant_id=%s
                         AND legal_entity_id=%s AND reviewer_id=%s""",
                    (candidate_id,tenant_id,legal_entity_id,actor),
                )
                row = cur.fetchone()
            if row is None:
                raise CandidateNotFound("candidate not found in reviewer scope")
            return {
                **{k:v for k,v in row.items()
                   if k not in ("evidence_json","reviewed_rule_json")},
                "segments": json.loads(row["evidence_json"]),
                "reviewed_rule": json.loads(row["reviewed_rule_json"])
                    if row["reviewed_rule_json"] else None,
            }
        finally:
            db.close()

    def review(
        self, token: str, *, candidate_id: str,
        tenant_id: str, legal_entity_id: str,
        rule: dict[str, Any], confirm_clause_review: bool,
    ) -> dict[str, str]:
        actor = self._actor(token, tenant_id, legal_entity_id)
        if confirm_clause_review is not True or not isinstance(rule, dict):
            raise CandidateConflict("explicit document-clause review required")
        try:
            parsed = BonusRule.load(rule)
        except (ValueError, TypeError, KeyError) as exc:
            raise CandidateConflict("unambiguous sourced rule required") from exc
        if not parsed.approved:
            raise CandidateConflict("human-reviewed rule required")
        digest = rule_sha256(rule)
        encoded = json.dumps(rule,ensure_ascii=False,sort_keys=True,
                             separators=(",",":"),allow_nan=False)
        if len(encoded.encode("utf-8")) > 64 * 1024:
            raise CandidateConflict("reviewed rule exceeds size limit")
        db = self._connect()
        try:
            with db.cursor() as cur:
                cur.execute(
                    """SELECT state,agreement_id,rule_id,rule_revision,evidence_json
                       FROM lhfm_contract_candidates
                       WHERE candidate_id=%s AND tenant_id=%s AND legal_entity_id=%s
                         AND reviewer_id=%s FOR UPDATE""",
                    (candidate_id,tenant_id,legal_entity_id,actor),
                )
                record = cur.fetchone()
                if record is None:
                    raise CandidateNotFound("candidate not found in reviewer scope")
                if record["state"] != "EXTRACTED":
                    raise CandidateConflict("review is not at EXTRACTED stage")
                if (rule.get("agreement_id"),rule.get("rule_id"),rule.get("revision")) != (
                    record["agreement_id"],record["rule_id"],record["rule_revision"]
                ):
                    raise CandidateConflict("reviewed rule revision differs from source")
                cited = rule.get("evidence_refs")
                permitted = {
                    x["evidence_ref"] for x in json.loads(record["evidence_json"])
                }
                if (not isinstance(cited, list) or not cited
                        or any(not isinstance(ref,str) or ref not in permitted
                               for ref in cited)):
                    raise CandidateConflict("rule must cite exact extracted clause references")
                cur.execute(
                    """UPDATE lhfm_contract_candidates SET
                       state='NEEDS_CONFIRMATION', reviewed_rule_json=%s,
                       reviewed_rule_sha256=%s, reviewed_at=UTC_TIMESTAMP(6)
                       WHERE candidate_id=%s AND state='EXTRACTED'""",
                    (encoded,digest,candidate_id),
                )
                if cur.rowcount != 1:
                    raise CandidateConflict("concurrent candidate review")
                cur.execute(
                    """INSERT INTO lhfm_contract_candidate_events
                       (candidate_id,tenant_id,legal_entity_id,actor_id,event_type)
                       VALUES (%s,%s,%s,%s,'NEEDS_CONFIRMATION')""",
                    (candidate_id,tenant_id,legal_entity_id,actor),
                )
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()
        return {"candidate_id":candidate_id,"state":"NEEDS_CONFIRMATION",
                "reviewed_rule_sha256":digest}

    def require_reviewed(
        self, *, candidate_id: str, actor_id: str, tenant_id: str,
        legal_entity_id: str, contract_upload_id: str,
        document_sha256: str, source_revision_id: str,
        rule: dict[str, Any],
    ) -> None:
        """Preflight only. Register must independently lock and recheck the row."""
        db = self._connect()
        try:
            with db.cursor() as cur:
                cur.execute(
                    """SELECT state,contract_upload_id,document_sha256,
                              source_revision_id,reviewed_rule_sha256,
                              agreement_id,rule_id,rule_revision
                       FROM lhfm_contract_candidates
                       WHERE candidate_id=%s AND tenant_id=%s AND legal_entity_id=%s
                         AND reviewer_id=%s""",
                    (candidate_id,tenant_id,legal_entity_id,actor_id),
                )
                row = cur.fetchone()
            if row is None:
                raise CandidateNotFound("reviewed candidate not found in actor scope")
            if (row["state"]!="NEEDS_CONFIRMATION"
                    or row["contract_upload_id"]!=contract_upload_id
                    or row["document_sha256"]!=document_sha256
                    or row["source_revision_id"]!=source_revision_id
                    or row["reviewed_rule_sha256"]!=rule_sha256(rule)
                    or (row["agreement_id"],row["rule_id"],row["rule_revision"])
                       != (rule.get("agreement_id"),rule.get("rule_id"),rule.get("revision"))):
                raise CandidateConflict("candidate rule/source review does not match")
        finally:
            db.close()
