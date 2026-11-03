"""Authenticated FastAPI -> MariaDB -> signed deterministic CSV audit acceptance.

Real MariaDB is only used inside CI's isolated lhfm_test. The RSA key and
all source files are synthetic and never persisted to the public repository.
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

from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi.testclient import TestClient
import jwt

from lowhangingfruitme.approval import issue_approval
from lowhangingfruitme.approval_registry import ApprovalRegistry
from lowhangingfruitme.approval_service import AuthenticatedApprovalService
from lowhangingfruitme.auth import AccessTokenVerifier
from lowhangingfruitme.api.http import create_app
from lowhangingfruitme.api.store import PrivateAuditStore


ROOT = Path(__file__).parent / "fixtures"
ISS = "https://issuer.example.test/"
AUD = "https://lowhangingfruitme.example.test/api"
CLIENT = "lhfm-test-api"
ACTOR = "REVIEWER-SYN-1"
TENANT = "T-SYN-1"
LEGAL = "LE-SYN-1"
KEY = b"synthetic-private-API-integration-only-signer-key"


@unittest.skipUnless(bool(os.getenv("LHFM_DB_HOST")), "real MariaDB service required")
class AuditApiIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.private = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        jwk = json.loads(jwt.algorithms.RSAAlgorithm.to_jwk(cls.private.public_key()))
        jwk.update(kid="api-synthetic-public", alg="RS256", use="sig")
        cls.verifier = AccessTokenVerifier(
            issuer=ISS, audience=AUD,
            jwks={"keys": [jwk]}, allowed_client_ids=(CLIENT,),
        )

    def token(self, **kwargs):
        now = int(datetime.now(timezone.utc).timestamp())
        claims = {
            "iss": ISS, "aud": AUD, "sub": ACTOR, "client_id": CLIENT,
            "iat": now, "nbf": now, "exp": now+600,
            "jti": str(uuid4()), "scope": "lhfm:audit:execute",
        }
        claims.update(kwargs)
        return jwt.encode(claims, self.private, algorithm="RS256",
                          headers={"typ":"at+jwt", "kid":"api-synthetic-public"})

    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        for name in ("rule.json", "transactions.csv", "settlements.csv",
                     "synthetic_agreement.txt"):
            (self.root / name).write_bytes((ROOT / name).read_bytes())
        self.rule = json.loads((self.root / "rule.json").read_text(encoding="utf-8"))
        doc_hash = sha256((self.root / "synthetic_agreement.txt").read_bytes()).hexdigest()
        self.receipt = issue_approval(
            self.rule, key=KEY, tenant_id=TENANT, legal_entity_id=LEGAL,
            reviewer_id=ACTOR, approval_id="API-SYN-"+uuid4().hex,
            source_revision_id="REV-API-SYN", document_sha256=doc_hash,
            approved_at=datetime.now(timezone.utc),
        )
        self.registry = ApprovalRegistry.from_environment()
        self.registry.register(
            self.receipt, rule=self.rule, key=KEY, document_sha256=doc_hash,
            tenant_id=TENANT, legal_entity_id=LEGAL,
            authenticated_actor_id=ACTOR,
        )
        self.store = PrivateAuditStore(registry=self.registry, source_root=self.root)
        self.bundle_id = str(uuid4())
        self.manifest = {
            "source_system": "erp", "files": {
                "rule": self.ref("rule.json"),
                "transactions": self.ref("transactions.csv"),
                "settlements": self.ref("settlements.csv"),
                "contract": self.ref("synthetic_agreement.txt"),
            },
            "controls": json.loads((ROOT/"source_controls.json").read_text(encoding="utf-8")),
            "completeness": {
                "transactions_complete": True,
                "settlements_complete": True,
                "agreements_complete": True,
            },
            "approval_receipt": self.receipt,
        }
        self.store.provision_bundle(
            bundle_id=self.bundle_id, tenant_id=TENANT, legal_entity_id=LEGAL,
            manifest=self.manifest,
        )
        svc = AuthenticatedApprovalService(
            verifier=self.verifier, registry=self.registry, approval_key=KEY,
        )
        self.client = TestClient(create_app(service=svc, store=self.store))
        self.addCleanup(self.client.close)

    def ref(self, name):
        return {"path": name, "sha256": sha256((self.root/name).read_bytes()).hexdigest()}

    def headers(self, token=None, key=None):
        return {
            "Authorization":"Bearer "+(token if token is not None else self.token()),
            "Idempotency-Key":key or str(uuid4()),
        }

    def submit(self, *, token=None, key=None, bundle_id=None, tenant=None,
               entity=None, extra=None):
        body={"bundle_id":bundle_id or self.bundle_id,
              "tenant_id":tenant or TENANT,
              "legal_entity_id":entity or LEGAL}
        body.update(extra or {})
        return self.client.post("/v1/audits", json=body, headers=self.headers(token, key))

    def get_report(self, audit_id, token=None, tenant=None, entity=None):
        return self.client.get(
            "/v1/audits/"+audit_id,
            params={"tenant_id":tenant or TENANT,"legal_entity_id":entity or LEGAL},
            headers={"Authorization":"Bearer "+(token or self.token())},
        )

    def test_health_does_not_need_token_or_disclose_configuration(self):
        r=self.client.get("/healthz")
        self.assertEqual(r.status_code,200)
        self.assertEqual(r.json(),{"status":"alive"})
        self.assertEqual(r.headers["cache-control"],"no-store")
        self.assertNotIn("openapi",self.client.get("/openapi.json").text.lower())

    def test_valid_signed_api_request_runs_existing_financial_engine(self):
        r=self.submit()
        self.assertEqual(r.status_code,201,r.text)
        self.assertEqual(r.json()["status"],"COMPLETED")
        self.assertTrue(r.json()["audit_executed"])
        self.assertFalse(r.json()["replayed"])
        report=self.get_report(r.json()["audit_id"])
        self.assertEqual(report.status_code,200,report.text)
        evidence=report.json()["report"]
        self.assertEqual(evidence["status"],"EVIDENCED")
        self.assertEqual(evidence["difference_net"],"2500.00")
        self.assertEqual(evidence["billable_recovery_net"],"0.00")
        self.assertEqual(evidence["fee_due_net"],"0.00")
        self.assertEqual(evidence["approval_verification"]["revocation_status"],
                         "ACTIVE_LOCKED_AT_DISPATCH")

    def test_missing_bearer_token_rejected(self):
        r=self.client.post("/v1/audits",json={"bundle_id":self.bundle_id,
            "tenant_id":TENANT,"legal_entity_id":LEGAL},
            headers={"Idempotency-Key":str(uuid4())})
        self.assertEqual(r.status_code,401)

    def test_untrusted_jwt_and_wrong_oauth_client_rejected(self):
        self.assertEqual(self.submit(token="forged-token").status_code,401)
        self.assertEqual(self.submit(token=self.token(client_id="other")).status_code,401)

    def test_missing_scope_and_wrong_tenant_rejected(self):
        self.assertEqual(self.submit(token=self.token(scope="openid")).status_code,403)
        self.assertEqual(self.submit(tenant="OTHER-TENANT").status_code,403)

    def test_unknown_bundle_not_discoverable(self):
        r=self.submit(bundle_id=str(uuid4()))
        self.assertEqual(r.status_code,404)
        self.assertNotIn(self.root.as_posix(),r.text)

    def test_user_paths_and_client_supplied_receipts_are_not_api_fields(self):
        r=self.submit(extra={"rule_path":"/etc/passwd","approval_key":"forged"})
        self.assertEqual(r.status_code,422)

    def test_idempotency_retry_does_not_recalculate(self):
        key=str(uuid4())
        a=self.submit(key=key)
        self.assertEqual(a.status_code,201,a.text)
        b=self.submit(key=key)
        self.assertEqual(b.status_code,200,b.text)
        self.assertTrue(b.json()["replayed"])
        self.assertEqual(b.json()["audit_id"],a.json()["audit_id"])

    def test_idempotency_key_reuse_other_bundle_is_conflict(self):
        key=str(uuid4())
        self.assertEqual(self.submit(key=key).status_code,201)
        new_bundle=str(uuid4())
        self.store.provision_bundle(
            bundle_id=new_bundle,tenant_id=TENANT,
            legal_entity_id=LEGAL,manifest=deepcopy(self.manifest))
        r=self.submit(key=key,bundle_id=new_bundle)
        self.assertEqual(r.status_code,409)

    def test_no_idempotency_key_blocked(self):
        r=self.client.post("/v1/audits",json={
            "bundle_id":self.bundle_id,"tenant_id":TENANT,
            "legal_entity_id":LEGAL
        },headers={"Authorization":"Bearer "+self.token()})
        self.assertEqual(r.status_code,400)

    def test_source_mutation_fails_closed_and_keeps_no_partial_report(self):
        (self.root/"transactions.csv").write_bytes(b"not an authentic source anymore\n")
        r=self.submit()
        self.assertEqual(r.status_code,503,r.text)
        self.assertNotIn(self.root.as_posix(),r.text)
        # The failed reservation is deliberately not silently retried.
        conn=self.registry._connect()
        try:
            with conn.cursor() as c:
                c.execute("""SELECT audit_id FROM lhfm_api_runs
                             WHERE status='FAILED' AND tenant_id=%s AND reviewer_id=%s
                             ORDER BY started_at DESC LIMIT 1""",(TENANT,ACTOR))
                row=c.fetchone()
            self.assertIsNotNone(row)
        finally:
            conn.close()

    def test_revoked_approval_cannot_produce_final_amount(self):
        self.registry.revoke(self.receipt["approval_id"],tenant_id=TENANT,
                             legal_entity_id=LEGAL,authenticated_actor_id=ACTOR)
        r=self.submit()
        self.assertEqual(r.status_code,201,r.text)
        self.assertEqual(r.json()["status"],"NEEDS_REVIEW")
        self.assertFalse(r.json()["audit_executed"])
        report=self.get_report(r.json()["audit_id"]).json()["report"]
        self.assertIsNone(report["difference_net"])
        self.assertEqual(report["fee_due_net"],"0.00")

    def test_missing_controls_keeps_readiness_gate(self):
        manifest=deepcopy(self.manifest)
        manifest["controls"]=None
        new_bundle=str(uuid4())
        self.store.provision_bundle(bundle_id=new_bundle,tenant_id=TENANT,
                                    legal_entity_id=LEGAL,manifest=manifest)
        r=self.submit(bundle_id=new_bundle)
        self.assertEqual(r.status_code,201,r.text)
        self.assertEqual(r.json()["status"],"NEEDS_REVIEW")
        report=self.get_report(r.json()["audit_id"]).json()["report"]
        self.assertIsNone(report["difference_net"])

    def test_missing_or_wrong_audit_report_returns_404(self):
        r=self.get_report(str(uuid4()))
        self.assertEqual(r.status_code,404)
        a=self.submit().json()["audit_id"]
        self.assertEqual(self.get_report(a,tenant="OTHER").status_code,403)

    def test_bundle_path_traversal_and_symlink_rejected(self):
        link=self.root/"other.csv"
        link.symlink_to(self.root/"transactions.csv")
        with self.assertRaisesRegex(ValueError,"symlink"):
            self.store._private_path("other.csv")
        with self.assertRaisesRegex(ValueError,"escapes"):
            self.store._private_path("../etc/passwd")


if __name__ == "__main__":
    unittest.main()
