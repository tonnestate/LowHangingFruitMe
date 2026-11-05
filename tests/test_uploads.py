"""Private upload HTTP regression with real MariaDB and synthetic JWT credentials.

Test scanner is deliberately fake; this proves the fail-closed protocol wiring,
NOT that a production ClamAV daemon has been deployed or independently audited.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from hashlib import sha256
import json
import os
from pathlib import Path
import socket
import struct
from tempfile import TemporaryDirectory
import threading
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
from lowhangingfruitme.api.uploads import (
    ClamAVScanner, ScannerUnavailable, UploadRejected, UploadService,
)

ISS = "https://upload-idp.example.test/"
AUD = "https://upload-api.example.test/"
CLIENT = "lhfm-upload-test"
ACTOR = "REVIEWER-SYN-1"
TENANT = "T-SYN-1"
ENTITY = "LE-SYN-1"
KEY = b"only-synthetic-test-secret-for-upload-API-32"


class ScannerStub:
    """In-memory test-only decision function, never used in deployment."""
    def __init__(self, mode="clean"):
        self.mode = mode
        self.calls = 0

    def scan(self, path: Path) -> bool:
        self.calls += 1
        if self.mode == "unavailable":
            raise ScannerUnavailable("fake test scanner outage")
        return self.mode == "clean"


@unittest.skipUnless(bool(os.environ.get("LHFM_DB_HOST")), "real MariaDB required")
class UploadApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.private = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        public = json.loads(jwt.algorithms.RSAAlgorithm.to_jwk(cls.private.public_key()))
        public.update(kid="synthetic-upload-key", alg="RS256", use="sig")
        cls.verifier = AccessTokenVerifier(
            issuer=ISS, audience=AUD, jwks={"keys": [public]},
            allowed_client_ids=(CLIENT,),
        )

    def token(self, **overrides):
        now = int(datetime.now(timezone.utc).timestamp())
        data = {
            "iss": ISS, "aud": AUD, "sub": ACTOR, "client_id": CLIENT,
            "iat": now, "nbf": now, "exp": now + 600, "jti": str(uuid4()),
            "scope": "lhfm:upload:write",
        }
        data.update(overrides)
        return jwt.encode(
            data, self.private, algorithm="RS256",
            headers={"kid": "synthetic-upload-key", "typ": "at+jwt"},
        )

    def setUp(self):
        tmp = TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.stage = self.root / "quarantine"
        self.stage.mkdir(mode=0o700)
        self.registry = ApprovalRegistry.from_environment()
        self.service = AuthenticatedApprovalService(
            verifier=self.verifier, registry=self.registry, approval_key=KEY,
        )
        self.store = PrivateAuditStore(registry=self.registry, source_root=self.root)
        self.scanner = ScannerStub()
        self.uploads = UploadService(
            registry=self.registry, root=self.stage, scanner=self.scanner,
        )
        self.client = TestClient(create_app(
            service=self.service, store=self.store, uploads=self.uploads,
        ))
        self.addCleanup(self.client.close)
        self.csv = (
            b"Belegnummer;Kreditor;Belegdatum;Nettobetrag;Gebucht;Belegart\n"
            b"INV-001;SUP-1;10.05.2025;210.000,00;Ja;PURCHASE\n"
        )

    def auth(self, token=None):
        return {"Authorization": "Bearer " + (token or self.token())}

    def scope(self, tenant=TENANT, entity=ENTITY):
        return {"tenant_id": tenant, "legal_entity_id": entity}

    def intent(self, content=None, *, kind="ERP_CSV", token=None, size=None, sha=None,
               tenant=TENANT, entity=ENTITY):
        raw = self.csv if content is None else content
        body = {
            **self.scope(tenant, entity), "kind": kind,
            "byte_size": len(raw) if size is None else size,
            "sha256": sha256(raw).hexdigest() if sha is None else sha,
        }
        return self.client.post("/v1/uploads", json=body, headers=self.auth(token))

    def put(self, upload_id, raw=None, *, token=None, tenant=TENANT, entity=ENTITY,
            content_type="application/octet-stream"):
        return self.client.put(
            "/v1/uploads/" + upload_id + "/content",
            params=self.scope(tenant, entity),
            headers={**self.auth(token), "Content-Type": content_type},
            content=self.csv if raw is None else raw,
        )

    def get_status(self, upload_id, *, token=None, tenant=TENANT, entity=ENTITY):
        return self.client.get(
            "/v1/uploads/" + upload_id,
            params=self.scope(tenant, entity), headers=self.auth(token),
        )

    def test_valid_csv_upload_with_private_source_integrity(self):
        created = self.intent()
        self.assertEqual(created.status_code, 201, created.text)
        upload_id = created.json()["upload_id"]
        self.assertEqual(created.json()["state"], "PENDING")
        result = self.put(upload_id)
        self.assertEqual(result.status_code, 200, result.text)
        self.assertEqual(result.json()["state"], "CLEAN")
        self.assertEqual(result.json()["sha256"], sha256(self.csv).hexdigest())
        self.assertFalse(result.json()["usable_for_audit"])
        self.assertEqual(self.scanner.calls, 1)
        uploaded = self.stage / (upload_id + ".csv")
        self.assertEqual(uploaded.read_bytes(), self.csv)
        self.assertEqual(uploaded.stat().st_mode & 0o777, 0o600)
        self.assertEqual(self.get_status(upload_id).json()["state"], "CLEAN")

    def test_no_token_or_wrong_scope_cannot_open_upload_intent(self):
        body = {
            **self.scope(), "kind":"ERP_CSV", "byte_size":len(self.csv),
            "sha256":sha256(self.csv).hexdigest(),
        }
        self.assertEqual(self.client.post("/v1/uploads",json=body).status_code,401)
        self.assertEqual(self.intent(token=self.token(scope="lhfm:audit:execute")).status_code,403)
        self.assertEqual(self.intent(token="fake-access-token").status_code,401)

    def test_wrong_tenant_or_subject_denied(self):
        self.assertEqual(self.intent(tenant="OTHER-TENANT").status_code,403)
        self.assertEqual(self.intent(token=self.token(sub="NOT-REVIEWER")).status_code,403)
        upload_id=self.intent().json()["upload_id"]
        self.assertEqual(self.get_status(upload_id,tenant="OTHER-TENANT").status_code,403)
        self.assertEqual(self.get_status(upload_id,token=self.token(sub="NOT-REVIEWER")).status_code,403)

    def test_tampered_content_rejected_and_deleted(self):
        upload_id=self.intent().json()["upload_id"]
        r=self.put(upload_id,raw=self.csv+b"change")
        self.assertEqual(r.status_code,422,r.text)
        self.assertEqual(self.get_status(upload_id).json()["state"],"REJECTED")
        self.assertFalse(list(self.stage.iterdir()))
        self.assertEqual(self.put(upload_id).status_code,422)

    def test_preexisting_staging_collision_keeps_foreign_partial(self):
        upload_id = self.intent().json()["upload_id"]
        existing = self.stage / (upload_id + ".part")
        existing.write_bytes(b"previous-upload-partial-must-survive")
        existing.chmod(0o600)
        response = self.put(upload_id)
        self.assertEqual(response.status_code, 422, response.text)
        self.assertEqual(response.json()["detail"]["code"], "UPLOAD_REJECTED")
        self.assertEqual(existing.read_bytes(), b"previous-upload-partial-must-survive")
        self.assertEqual(self.get_status(upload_id).json()["state"], "REJECTED")
        self.assertEqual(self.scanner.calls, 0)

    def test_preexisting_inspect_collision_keeps_foreign_inspected_file(self):
        upload_id = self.intent().json()["upload_id"]
        existing = self.stage / (upload_id + ".inspect.csv")
        existing.write_bytes(b"previous-inspection-must-survive")
        existing.chmod(0o600)
        response = self.put(upload_id)
        self.assertEqual(response.status_code, 422, response.text)
        self.assertEqual(response.json()["detail"]["code"], "UPLOAD_REJECTED")
        self.assertEqual(existing.read_bytes(), b"previous-inspection-must-survive")
        self.assertFalse((self.stage / (upload_id + ".part")).exists())
        self.assertFalse((self.stage / (upload_id + ".csv")).exists())
        self.assertEqual(self.get_status(upload_id).json()["state"], "REJECTED")
        self.assertEqual(self.scanner.calls, 1)

    def test_preexisting_final_collision_never_deletes_financial_source(self):
        upload_id = self.intent().json()["upload_id"]
        existing = self.stage / (upload_id + ".csv")
        existing.write_bytes(b"existing-final-evidence-must-survive")
        existing.chmod(0o600)
        response = self.put(upload_id)
        self.assertEqual(response.status_code, 422, response.text)
        self.assertEqual(response.json()["detail"]["code"], "UPLOAD_REJECTED")
        self.assertEqual(existing.read_bytes(), b"existing-final-evidence-must-survive")
        self.assertFalse((self.stage / (upload_id + ".part")).exists())
        self.assertFalse((self.stage / (upload_id + ".inspect.csv")).exists())
        self.assertEqual(self.get_status(upload_id).json()["state"], "REJECTED")
        self.assertEqual(self.scanner.calls, 1)

    def test_wrong_hash_rejected(self):
        upload_id=self.intent(sha="0"*64).json()["upload_id"]
        self.assertEqual(self.put(upload_id).status_code,422)
        self.assertEqual(self.get_status(upload_id).json()["state"],"REJECTED")
        self.assertFalse(list(self.stage.iterdir()))

    def test_malware_detection_refuses_promotion(self):
        self.scanner.mode="infected"
        upload_id=self.intent().json()["upload_id"]
        r=self.put(upload_id)
        self.assertEqual(r.status_code,422,r.text)
        self.assertEqual(self.scanner.calls,1)
        self.assertFalse(list(self.stage.iterdir()))
        self.assertEqual(self.get_status(upload_id).json()["state"],"REJECTED")

    def test_scanner_outage_refuses_promotion(self):
        self.scanner.mode="unavailable"
        upload_id=self.intent().json()["upload_id"]
        r=self.put(upload_id)
        self.assertEqual(r.status_code,503,r.text)
        self.assertEqual(self.get_status(upload_id).json()["state"],"REJECTED")
        self.assertFalse(list(self.stage.iterdir()))

    def test_malformed_pdf_is_rejected_after_scan(self):
        bad=b"untrusted pretend PDF"
        upload_id=self.intent(bad,kind="CONTRACT_PDF").json()["upload_id"]
        r=self.put(upload_id,raw=bad)
        self.assertEqual(r.status_code,422,r.text)
        self.assertEqual(self.scanner.calls,1)
        self.assertEqual(self.get_status(upload_id).json()["state"],"REJECTED")
        self.assertFalse(list(self.stage.iterdir()))

    def test_xml_entity_attack_rejected_after_scan(self):
        attack=b'<!DOCTYPE Invoice [<!ENTITY x SYSTEM "file:///etc/passwd">]><Invoice>&x;</Invoice>'
        upload_id=self.intent(attack,kind="INVOICE_XML").json()["upload_id"]
        r=self.put(upload_id,raw=attack)
        self.assertEqual(r.status_code,422,r.text)
        self.assertFalse(list(self.stage.iterdir()))

    def test_authenticated_xml_invoice_preview_never_becomes_posted_ledger(self):
        from test_invoices import UBL
        created=self.intent(UBL,kind="INVOICE_XML")
        self.assertEqual(created.status_code,201,created.text)
        upload_id=created.json()["upload_id"]
        transferred=self.put(upload_id,raw=UBL)
        self.assertEqual(transferred.status_code,200,transferred.text)
        preview=self.client.get(
            "/v1/uploads/"+upload_id+"/invoice-preview",
            params=self.scope(),headers=self.auth(),
        )
        self.assertEqual(preview.status_code,200,preview.text)
        result=preview.json()
        self.assertEqual(result["document_id"],"INVOICE-SYN-100")
        self.assertEqual(result["line_count"],1)
        self.assertEqual(result["lines"][0]["quantity"],"2")
        self.assertIn(sha256(UBL).hexdigest(),result["lines"][0]["source_ref"])
        self.assertFalse(result["accounting_posted"])
        self.assertFalse(result["usable_for_audit"])
        self.assertFalse(result["schema_validated"])
        other_tenant=self.client.get(
            "/v1/uploads/"+upload_id+"/invoice-preview",
            params=self.scope(tenant="OTHER-TENANT"),headers=self.auth(),
        )
        self.assertEqual(other_tenant.status_code,403)

    def test_xml_preview_denied_for_non_invoice_upload(self):
        upload_id=self.intent().json()["upload_id"]
        self.assertEqual(self.put(upload_id).status_code,200)
        result=self.client.get(
            "/v1/uploads/"+upload_id+"/invoice-preview",
            params=self.scope(),headers=self.auth(),
        )
        self.assertEqual(result.status_code,422)
        self.assertNotIn("sha256:",result.text.lower())

    def test_multipart_and_unsupported_upload_types_fail(self):
        upload_id=self.intent().json()["upload_id"]
        self.assertEqual(
            self.put(upload_id,content_type="multipart/form-data; boundary=wrong").status_code,
            415,
        )
        self.assertEqual(self.get_status(upload_id).json()["state"],"PENDING")
        self.assertEqual(self.intent(kind="RAW_EXECUTABLE").status_code,422)

    def test_declared_size_is_validated_without_reading_body(self):
        self.assertEqual(self.intent(size=16*1024*1024+1).status_code,422)
        self.assertEqual(self.intent(size=0).status_code,422)

    def test_single_claim_under_parallel_requests(self):
        upload_id=self.intent().json()["upload_id"]
        def claim(_):
            try:
                self.uploads.claim_upload(
                    upload_id=upload_id,tenant_id=TENANT,
                    legal_entity_id=ENTITY,reviewer_id=ACTOR,
                )
                return "claimed"
            except UploadRejected:
                return "blocked"
        with ThreadPoolExecutor(max_workers=2) as pool:
            responses=list(pool.map(claim,range(2)))
        self.assertCountEqual(responses,["claimed","blocked"])

    def test_expired_intent_cannot_be_consumed(self):
        upload_id=self.intent().json()["upload_id"]
        db=self.registry._connect()
        try:
            with db.cursor() as c:
                c.execute("UPDATE lhfm_uploads SET expires_at=DATE_SUB(UTC_TIMESTAMP(),INTERVAL 1 MINUTE) WHERE upload_id=%s",(upload_id,))
            db.commit()
        finally:
            db.close()
        self.assertEqual(self.put(upload_id).status_code,422)
        self.assertEqual(self.get_status(upload_id).json()["state"],"PENDING")

    def test_upload_is_not_an_audit_bundle(self):
        upload_id=self.intent().json()["upload_id"]
        self.assertEqual(self.put(upload_id).status_code,200)
        # The scanned file cannot bypass the separate signed-bundle audit gate.
        result=self.client.post(
            "/v1/audits",
            json={"bundle_id":upload_id,**self.scope()},
            headers={
                **self.auth(token=self.token(scope="lhfm:audit:execute")),
                "Idempotency-Key":str(uuid4()),
            },
        )
        self.assertEqual(result.status_code,404)

    def test_readiness_rejects_synthetic_scanner_and_missing_services(self):
        result = self.client.get("/readyz")
        self.assertEqual(result.status_code, 503)
        self.assertEqual(result.json()["detail"]["code"], "NOT_READY")
        self.assertEqual(self.client.get("/healthz").status_code, 200)

    def test_unconfigured_upload_gate_fails_closed(self):
        client=TestClient(create_app(service=self.service,store=self.store))
        self.addCleanup(client.close)
        body={**self.scope(),"kind":"ERP_CSV","byte_size":len(self.csv),
              "sha256":sha256(self.csv).hexdigest()}
        r=client.post("/v1/uploads",json=body,headers=self.auth())
        self.assertEqual(r.status_code,503)


class ClamAVProtocolTests(unittest.TestCase):
    def test_absent_daemon_fails_closed(self):
        with TemporaryDirectory() as temp:
            f=Path(temp)/"test.csv"
            f.write_bytes(b"a,b\n1,2\n")
            with self.assertRaises(ScannerUnavailable):
                ClamAVScanner(str(Path(temp)/"missing.sock"),timeout=1).scan(f)

    def test_local_clamd_ping_requires_exact_pong(self):
        with TemporaryDirectory() as temp:
            path = Path(temp) / "ping.sock"
            server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            server.bind(str(path))
            server.listen(1)
            observed = []

            def serve():
                try:
                    conn, _ = server.accept()
                    with conn:
                        observed.append(conn.recv(64))
                        conn.sendall(b"PONG\0")
                finally:
                    server.close()

            thread = threading.Thread(target=serve, daemon=True)
            thread.start()
            ClamAVScanner(path, timeout=2).ping()
            thread.join(timeout=2)
            self.assertEqual(observed, [b"zPING\0"])

    def test_local_clamd_ping_rejects_incorrect_reply(self):
        with TemporaryDirectory() as temp:
            path = Path(temp) / "bad-ping.sock"
            server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            server.bind(str(path))
            server.listen(1)

            def serve():
                try:
                    conn, _ = server.accept()
                    with conn:
                        conn.recv(64)
                        conn.sendall(b"UNKNOWN\0")
                finally:
                    server.close()

            thread = threading.Thread(target=serve, daemon=True)
            thread.start()
            with self.assertRaises(ScannerUnavailable):
                ClamAVScanner(path, timeout=2).ping()
            thread.join(timeout=2)

    def test_local_clamd_instream_framing_and_clean_response(self):
        with TemporaryDirectory() as temp:
            sockpath=Path(temp)/"fake.sock"
            file=Path(temp)/"test.csv"
            file.write_bytes(b"a,b\n1,2\n")
            server=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM)
            server.bind(str(sockpath))
            server.listen(1)
            received=[]
            def serve():
                try:
                    conn,_=server.accept()
                    with conn:
                        data=b""
                        while len(data)<10:
                            data+=conn.recv(10-len(data))
                        received.append(data)
                        while True:
                            size=conn.recv(4)
                            if len(size)!=4:
                                raise AssertionError("incomplete fake CLAMD frame")
                            amount=struct.unpack(">I",size)[0]
                            if amount==0:
                                break
                            payload=b""
                            while len(payload)<amount:
                                payload+=conn.recv(amount-len(payload))
                            received.append(payload)
                        conn.sendall(b"stream: OK\0")
                finally:
                    server.close()
            thread=threading.Thread(target=serve,daemon=True)
            thread.start()
            self.assertTrue(ClamAVScanner(sockpath,timeout=3).scan(file))
            thread.join(timeout=3)
            self.assertEqual(received[0],b"zINSTREAM\0")
            self.assertEqual(b"".join(received[1:]),file.read_bytes())


if __name__ == "__main__":
    unittest.main()
