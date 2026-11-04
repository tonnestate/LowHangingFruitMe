"""End-to-end upload -> verified human mapping -> signed bundle -> audit.

Only synthetic data, ephemeral RSA keys and CI's dedicated MariaDB.
"""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from hashlib import sha256
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from uuid import uuid4

from fastapi.testclient import TestClient
import jwt
from cryptography.hazmat.primitives.asymmetric import rsa

from lowhangingfruitme.approval_registry import ApprovalRegistry
from lowhangingfruitme.approval_service import AuthenticatedApprovalService
from lowhangingfruitme.auth import AccessTokenVerifier
from lowhangingfruitme.api.http import create_app
from lowhangingfruitme.api.store import PrivateAuditStore
from lowhangingfruitme.api.uploads import UploadService, UploadRejected
from lowhangingfruitme.api.promotion import ReviewedBundleService

BASE=Path(__file__).parent/"fixtures"
TENANT, ENTITY, ACTOR="T-SYN-1","LE-SYN-1","REVIEWER-SYN-1"
ISS, AUD, CLIENT="https://issuer.example.test/","https://lhfm.example.test/api","lhfm-test-review-pipeline"

TXN=(
 "Belegnummer;Kreditor;Belegdatum;Nettobetrag;Gebucht;Belegart\n"
 "INV-001;SUP-1;10.05.2025;210.000,00;Ja;PURCHASE\n"
 "RET-001;SUP-1;10.07.2025;-10.000,00;Ja;RETURN\n"
).encode()
SETTLED=(
 "Belegnummer;Kreditor;Belegdatum;Nettobetrag;Gebucht;Belegart;Vertragsnr;Bonus_von;Bonus_bis\n"
 "CREDIT-001;SUP-1;15.01.2026;1.500,00;Ja;CREDIT;AGR-1;01.01.2025;31.12.2025\n"
).encode()
CONTRACT=b"%PDF-1.7\n% synthetic source for isolated CI only; rule is human-approved\n"

TX_MAPPING={
 "external_id":"Belegnummer","supplier_id":"Kreditor",
 "date":"Belegdatum","amount_net":"Nettobetrag",
 "posted":"Gebucht","kind":"Belegart",
}
CR_MAPPING={**TX_MAPPING,"agreement_id":"Vertragsnr",
            "period_start":"Bonus_von","period_end":"Bonus_bis"}


class StubCleanScanner:
    def scan(self, path):
        return True  # CI only; not a production integration


@unittest.skipUnless(bool(os.getenv("LHFM_DB_HOST")), "real isolated MariaDB required")
class ReviewedPipelineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.private=rsa.generate_private_key(public_exponent=65537,key_size=2048)
        jwk=json.loads(jwt.algorithms.RSAAlgorithm.to_jwk(cls.private.public_key()))
        jwk.update(kid="review-synthetic",alg="RS256",use="sig")
        cls.verifier=AccessTokenVerifier(
            issuer=ISS,audience=AUD,jwks={"keys":[jwk]},
            allowed_client_ids=(CLIENT,),
        )

    def token(self, **overrides):
        now=int(datetime.now(timezone.utc).timestamp())
        claims={
            "iss":ISS,"aud":AUD,"sub":ACTOR,"client_id":CLIENT,
            "iat":now,"nbf":now,"exp":now+600,
            "jti":str(uuid4()),
            "scope":"lhfm:upload:write lhfm:approval:write lhfm:audit:execute",
        }
        claims.update(overrides)
        return jwt.encode(claims,self.private,algorithm="RS256",
                          headers={"typ":"at+jwt","kid":"review-synthetic"})

    def setUp(self):
        tmp=TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.home=Path(tmp.name)
        q=self.home/"uploads"
        a=self.home/"approved"
        q.mkdir(mode=0o700)
        a.mkdir(mode=0o700)
        self.registry=ApprovalRegistry.from_environment()
        self.service=AuthenticatedApprovalService(
            verifier=self.verifier,registry=self.registry,approval_key=b"synthetic-signer-secret-only-for-ci-xxxxxxxx",
        )
        self.store=PrivateAuditStore(registry=self.registry,source_root=a)
        self.uploads=UploadService(registry=self.registry,root=q,scanner=StubCleanScanner())
        self.promotion=ReviewedBundleService(
            service=self.service,uploads=self.uploads,store=self.store,
            require_candidate=False,  # explicit legacy synthetic compatibility only
        )
        self.client=TestClient(create_app(
            service=self.service,store=self.store,
            uploads=self.uploads,promotion=self.promotion,
        ))
        self.addCleanup(self.client.close)
        self.rule=json.loads((BASE/"rule.json").read_text(encoding="utf-8"))
        self.controls=json.loads((BASE/"source_controls.json").read_text(encoding="utf-8"))

    def headers(self, **overrides):
        return {"Authorization":"Bearer "+self.token(**overrides)}

    def scope(self):
        return {"tenant_id":TENANT,"legal_entity_id":ENTITY}

    def upload(self, data,kind):
        r=self.client.post("/v1/uploads",json={
            **self.scope(),"kind":kind,"byte_size":len(data),
            "sha256":sha256(data).hexdigest(),
        },headers=self.headers())
        self.assertEqual(r.status_code,201,r.text)
        upload_id=r.json()["upload_id"]
        put=self.client.put(
            "/v1/uploads/"+upload_id+"/content",params=self.scope(),
            headers={**self.headers(),"Content-Type":"application/octet-stream"},
            content=data,
        )
        self.assertEqual(put.status_code,200,put.text)
        self.assertEqual(put.json()["state"],"CLEAN")
        return upload_id

    def inputs(self):
        tx=self.upload(TXN,"ERP_CSV")
        se=self.upload(SETTLED,"ERP_CSV")
        co=self.upload(CONTRACT,"CONTRACT_PDF")
        return tx,se,co

    def plan(self,data,dataset):
        return {
            "source_sha256":sha256(data).hexdigest(),
            "dataset":dataset,
            "mapping":TX_MAPPING if dataset=="transactions" else CR_MAPPING,
            "constants":{"currency":"EUR","basis":"INVOICE"}
                if dataset=="transactions" else {"currency":"EUR"},
            "sheet_name":None,"decimal_format":"DE",
            "date_format":"DE","boolean_format":"DE",
            "reviewed_by":ACTOR,"confirmed":True,
        }

    def body(self,tx,se,co):
        return {
            **self.scope(),
            "transactions_upload_id":tx,
            "settlements_upload_id":se,
            "contract_upload_id":co,
            "source_system":"erp","source_revision_id":"2025-SYN-REV-A",
            "rule":self.rule,"transaction_plan":self.plan(TXN,"transactions"),
            "settlement_plan":self.plan(SETTLED,"settlements"),
            "controls":self.controls,
            "completeness":{"transactions_complete":True,
                            "settlements_complete":True,
                            "agreements_complete":True},
            "confirm_contract_review":True,"confirm_mapping_review":True,
        }

    def post(self,body,**token_overrides):
        return self.client.post("/v1/bundles",json=body,
                                headers=self.headers(**token_overrides))

    def test_full_reviewed_upload_to_evidenced_report(self):
        tx,se,co=self.inputs()
        preview=self.client.get(
            "/v1/uploads/"+tx+"/inspect",
            params={**self.scope(),"dataset":"transactions"},
            headers=self.headers(),
        )
        self.assertEqual(preview.status_code,200,preview.text)
        info=preview.json()
        self.assertEqual(info["rows"],2)
        self.assertFalse(info["audit_ready"])
        self.assertEqual(info["proposed_mapping"]["external_id"],["Belegnummer"])
        result=self.post(self.body(tx,se,co))
        self.assertEqual(result.status_code,201,result.text)
        bundle_id=result.json()["bundle_id"]
        self.assertEqual(result.json()["status"],"REGISTERED")
        self.assertFalse(result.json()["source_ledger_complete_proven"])
        self.assertEqual(result.json()["provenance"]["transactions"]["original_sha256"],sha256(TXN).hexdigest())
        self.assertEqual(result.json()["provenance"]["settlements"]["rows"],1)
        assert (self.store.root/bundle_id/"lineage.json").exists()
        audit=self.client.post(
            "/v1/audits",json={**self.scope(),"bundle_id":bundle_id},
            headers={**self.headers(),"Idempotency-Key":str(uuid4())},
        )
        self.assertEqual(audit.status_code,201,audit.text)
        self.assertEqual(audit.json()["status"],"COMPLETED")
        report=self.client.get(
            "/v1/audits/"+audit.json()["audit_id"],params=self.scope(),
            headers=self.headers(),
        )
        self.assertEqual(report.status_code,200,report.text)
        amounts=report.json()["report"]
        self.assertEqual(amounts["difference_net"],"2500.00")
        self.assertEqual(amounts["fee_due_net"],"0.00")
        self.assertEqual(amounts["input_provenance"]["transactions"]["mapping_sha256"],
                         result.json()["provenance"]["transactions"]["mapping_sha256"])

    def test_new_rule_revision_blocks_old_bundle_but_preserves_completed_audit(self):
        tx, se, co = self.inputs()
        old_bundle = self.post(self.body(tx, se, co))
        self.assertEqual(old_bundle.status_code, 201, old_bundle.text)
        old_id = old_bundle.json()["bundle_id"]
        original = self.client.post(
            "/v1/audits", json={**self.scope(), "bundle_id": old_id},
            headers={**self.headers(), "Idempotency-Key": str(uuid4())},
        )
        self.assertEqual(original.status_code, 201, original.text)
        self.assertEqual(original.json()["status"], "COMPLETED")

        newer_tx, newer_se, newer_co = self.inputs()
        new_request = self.body(newer_tx, newer_se, newer_co)
        new_request["rule"] = {**self.rule, "revision": "2"}
        new_request["source_revision_id"] = "2025-SYN-REV-B"
        new_bundle = self.post(new_request)
        self.assertEqual(new_bundle.status_code, 201, new_bundle.text)
        new_id = new_bundle.json()["bundle_id"]
        self.assertNotEqual(old_id, new_id)

        stale = self.client.post(
            "/v1/audits", json={**self.scope(), "bundle_id": old_id},
            headers={**self.headers(), "Idempotency-Key": str(uuid4())},
        )
        # The existing audit service converts invalid/revoked approval to a
        # non-final NEEDS_REVIEW result rather than exposing financial amounts.
        self.assertEqual(stale.status_code, 201, stale.text)
        self.assertEqual(stale.json()["status"], "NEEDS_REVIEW")
        self.assertFalse(stale.json()["audit_executed"])
        # Completed reports are immutable historical evidence, not live re-runs.
        history = self.client.get(
            "/v1/audits/" + original.json()["audit_id"],
            params=self.scope(), headers=self.headers(),
        )
        self.assertEqual(history.status_code, 200, history.text)
        self.assertEqual(history.json()["report"]["difference_net"], "2500.00")

        current = self.client.post(
            "/v1/audits", json={**self.scope(), "bundle_id": new_id},
            headers={**self.headers(), "Idempotency-Key": str(uuid4())},
        )
        self.assertEqual(current.status_code, 201, current.text)
        self.assertEqual(current.json()["status"], "COMPLETED")

    def test_mapping_receipts_are_persistently_signed(self):
        tx,se,co=self.inputs()
        created=self.post(self.body(tx,se,co))
        self.assertEqual(created.status_code,201,created.text)
        bundle=created.json()["bundle_id"]
        self.assertEqual(created.json()["mapping_approval_status"],"SIGNED_REGISTERED")
        manifest=self.store.load_bundle(
            bundle_id=bundle,tenant_id=self.scope()['tenant_id'],legal_entity_id=self.scope()['legal_entity_id'],
            reviewer_id=ACTOR,
        )
        self.assertEqual(set(manifest["mapping_approvals"]),
                         {"transactions","settlements"})
        with self.promotion.mapping_registry.guard(
            receipts=manifest["mapping_approvals"],
            provenance=manifest["provenance"],bundle_id=bundle,
            tenant_id=self.scope()['tenant_id'],legal_entity_id=self.scope()['legal_entity_id'],reviewer_id=ACTOR,
            approval_id=manifest["approval_receipt"]["approval_id"],
        ):
            db=self.registry._connect()
            try:
                with db.cursor() as cur:
                    cur.execute(
                        "SELECT COUNT(*) AS n FROM lhfm_mapping_approval_events "
                        "WHERE bundle_id=%s AND event_type='ISSUED'",(bundle,),
                    )
                    self.assertEqual(cur.fetchone()["n"],2)
            finally:
                db.close()

    def test_revoked_mapping_blocks_report_even_if_contract_signed(self):
        tx,se,co=self.inputs()
        created=self.post(self.body(tx,se,co))
        self.assertEqual(created.status_code,201,created.text)
        bundle=created.json()["bundle_id"]
        changed=self.promotion.mapping_registry.revoke_bundle(
            bundle_id=bundle,tenant_id=self.scope()['tenant_id'],
            legal_entity_id=self.scope()['legal_entity_id'],reviewer_id=ACTOR,
        )
        self.assertTrue(changed)
        self.assertFalse(self.promotion.mapping_registry.revoke_bundle(
            bundle_id=bundle,tenant_id=self.scope()['tenant_id'],
            legal_entity_id=self.scope()['legal_entity_id'],reviewer_id=ACTOR,
        ))
        attempt=self.client.post(
            "/v1/audits",json={**self.scope(),"bundle_id":bundle},
            headers={**self.headers(),"Idempotency-Key":str(uuid4())},
        )
        self.assertEqual(attempt.status_code,503,attempt.text)

    def test_mapping_receipt_tamper_blocks_audit(self):
        tx,se,co=self.inputs()
        created=self.post(self.body(tx,se,co))
        self.assertEqual(created.status_code,201,created.text)
        bundle=created.json()["bundle_id"]
        db=self.registry._connect()
        try:
            with db.cursor() as cur:
                cur.execute(
                    "SELECT manifest_json FROM lhfm_api_bundles WHERE bundle_id=%s",
                    (bundle,),
                )
                manifest=json.loads(cur.fetchone()["manifest_json"])
                manifest["mapping_approvals"]["transactions"]["source_sha256"]="0"*64
                cur.execute(
                    "UPDATE lhfm_api_bundles SET manifest_json=%s WHERE bundle_id=%s",
                    (json.dumps(manifest),bundle),
                )
            db.commit()
        finally:
            db.close()
        attempt=self.client.post(
            "/v1/audits",json={**self.scope(),"bundle_id":bundle},
            headers={**self.headers(),"Idempotency-Key":str(uuid4())},
        )
        self.assertEqual(attempt.status_code,503,attempt.text)

    def test_cross_tenant_mapping_verification_rejected(self):
        tx,se,co=self.inputs()
        created=self.post(self.body(tx,se,co))
        self.assertEqual(created.status_code,201,created.text)
        bundle=created.json()["bundle_id"]
        manifest=self.store.load_bundle(
            bundle_id=bundle,tenant_id=self.scope()['tenant_id'],legal_entity_id=self.scope()['legal_entity_id'],
            reviewer_id=ACTOR,
        )
        with self.assertRaises(PermissionError):
            with self.promotion.mapping_registry.guard(
                receipts=manifest["mapping_approvals"],
                provenance=manifest["provenance"],bundle_id=bundle,
                tenant_id="T-FOREIGN",legal_entity_id=self.scope()['legal_entity_id'],reviewer_id=ACTOR,
                approval_id=manifest["approval_receipt"]["approval_id"],
            ):
                pass

    def test_human_review_and_identity_required(self):
        tx,se,co=self.inputs()
        body=self.body(tx,se,co)
        body["confirm_contract_review"]=False
        self.assertEqual(self.post(body).status_code,422)
        body["confirm_contract_review"]=True
        body["transaction_plan"]["reviewed_by"]="IMPERSONATOR"
        self.assertEqual(self.post(body).status_code,422)
        body=self.body(tx,se,co)
        self.assertEqual(self.post(body,scope="lhfm:upload:write").status_code,403)
        self.assertEqual(self.post(body,sub="FORGED-ACTOR").status_code,403)

    def test_r2_unknown_application_blocks_before_signing_and_tells_customer_why(self):
        tx,se,co=self.inputs()
        body=self.body(tx,se,co)
        body["rule"].pop("rate")
        body["rule"]["kind"]="MARGINAL_PER_TIER"
        body["rule"]["tiers"]=[{"threshold":"80000.00","rate":"0.02"}]
        no_semantics=self.post(body)
        self.assertEqual(no_semantics.status_code,422,no_semantics.text)
        self.assertEqual(no_semantics.json()["detail"]["code"],"RULE_SEMANTICS_NEEDS_REVIEW")
        self.assertFalse(list(self.store.root.iterdir()))
        body["rule"]["tier_semantics"]={
            "application":"FULL_BASE",
            "evidence_ref":body["rule"]["evidence_refs"][0],
            "reviewed":True,
        }
        contradictory=self.post(body)
        self.assertEqual(contradictory.status_code,422,contradictory.text)
        self.assertEqual(contradictory.json()["detail"]["code"],"RULE_SEMANTICS_NEEDS_REVIEW")
        body["rule"]["tier_semantics"]["application"]="EXCESS_ONLY"
        accepted=self.post(body)
        self.assertEqual(accepted.status_code,201,accepted.text)
        self.assertEqual(accepted.json()["mapping_approval_status"],"SIGNED_REGISTERED")

    def test_mappings_bound_to_exact_uploaded_bytes(self):
        tx,se,co=self.inputs()
        body=self.body(tx,se,co)
        body["transaction_plan"]["source_sha256"]="0"*64
        self.assertEqual(self.post(body).status_code,422)
        self.assertFalse(list(self.store.root.iterdir()))

    def test_tenant_scope_prevents_reading_clean_upload(self):
        tx,se,co=self.inputs()
        body=self.body(tx,se,co)
        body["tenant_id"]="T-OTHER"
        self.assertEqual(self.post(body).status_code,403)
        self.assertFalse(list(self.store.root.iterdir()))

    def test_raw_unreviewed_upload_id_not_usable_as_audit_bundle(self):
        tx,se,co=self.inputs()
        fake=self.client.post(
            "/v1/audits",json={**self.scope(),"bundle_id":tx},
            headers={**self.headers(),"Idempotency-Key":str(uuid4())},
        )
        self.assertEqual(fake.status_code,404)

    def test_missing_independent_controls_is_review_only(self):
        tx,se,co=self.inputs()
        body=self.body(tx,se,co)
        body["controls"]=None
        registered=self.post(body)
        self.assertEqual(registered.status_code,201,registered.text)
        audit=self.client.post(
            "/v1/audits",json={**self.scope(),"bundle_id":registered.json()["bundle_id"]},
            headers={**self.headers(),"Idempotency-Key":str(uuid4())},
        )
        self.assertEqual(audit.status_code,201,audit.text)
        self.assertEqual(audit.json()["status"],"NEEDS_REVIEW")


if __name__=="__main__":
    unittest.main()
