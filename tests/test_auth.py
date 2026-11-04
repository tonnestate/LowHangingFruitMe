"""Cryptographic access JWT tests and real MariaDB approval-service integration.

The RSA private key is generated in test memory, never committed. Tests do
not contact a real identity provider; production OIDC integration remains open.
"""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from uuid import uuid4

import jwt
from cryptography.hazmat.primitives.asymmetric import rsa

from lowhangingfruitme.auth import AccessTokenVerifier
from lowhangingfruitme.approval_registry import ApprovalRegistry
from lowhangingfruitme.approval_service import AuthenticatedApprovalService


ISS = "https://issuer.example.test/"
AUD = "https://lowhangingfruitme.example.test/api"
CLIENT = "lhfm-backend-test"
SUB = "REVIEWER-SYN-1"
SCOPE = {"tenant_id": "T-SYN-1", "legal_entity_id": "LE-SYN-1"}
BASE = Path(__file__).parent / "fixtures"


class TestTokenFactory:
    def __init__(self):
        self.private = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        public = json.loads(jwt.algorithms.RSAAlgorithm.to_jwk(self.private.public_key()))
        public.update(kid="fixture-key-2026", alg="RS256", use="sig")
        self.jwks = {"keys": [public]}

    def token(self, **overrides):
        now = int(datetime.now(timezone.utc).timestamp())
        claims = {
            "iss": ISS, "aud": AUD, "sub": SUB, "client_id": CLIENT,
            "iat": now, "nbf": now, "exp": now + 600,
            "jti": uuid4().hex,
            "scope": "lhfm:approval:write lhfm:approval:revoke lhfm:audit:execute",
        }
        claims.update(overrides)
        return jwt.encode(
            claims, self.private, algorithm="RS256",
            headers={"kid": "fixture-key-2026", "typ": "at+jwt"},
        )

    def verifier(self):
        return AccessTokenVerifier(
            issuer=ISS, audience=AUD, jwks=self.jwks,
            allowed_client_ids=(CLIENT,),
        )


class JWTAccessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.factory = TestTokenFactory()

    def test_verified_at_jwt_has_stable_subject_and_scopes(self):
        principal = self.factory.verifier().verify(self.factory.token())
        self.assertEqual(principal.subject, SUB)
        self.assertIn("lhfm:approval:write", principal.scopes)

    def test_tampered_token_rejected(self):
        token = self.factory.token()
        head, payload, signature = token.split(".")
        other = self.factory.token(sub="ANOTHER")
        tampered = head + "." + other.split(".")[1] + "." + signature
        with self.assertRaises(PermissionError):
            self.factory.verifier().verify(tampered)

    def test_wrong_issuer_rejected(self):
        with self.assertRaises(PermissionError):
            self.factory.verifier().verify(self.factory.token(iss="https://other.example.test/"))

    def test_wrong_audience_rejected(self):
        with self.assertRaises(PermissionError):
            self.factory.verifier().verify(self.factory.token(aud="different-api"))

    def test_wrong_client_id_rejected(self):
        with self.assertRaisesRegex(PermissionError, "client"):
            self.factory.verifier().verify(self.factory.token(client_id="other-oauth-client"))

    def test_wrong_kid_rejected(self):
        token = jwt.encode(
            {"iss": ISS}, self.factory.private, algorithm="RS256",
            headers={"kid": "untrusted-key", "typ": "at+jwt"},
        )
        with self.assertRaisesRegex(PermissionError, "unrecognized"):
            self.factory.verifier().verify(token)

    def test_oidc_id_token_not_accepted_as_api_access(self):
        token = jwt.encode(
            {"iss": ISS}, self.factory.private, algorithm="RS256",
            headers={"kid": "fixture-key-2026", "typ": "JWT"},
        )
        with self.assertRaisesRegex(PermissionError, "ID tokens"):
            self.factory.verifier().verify(token)

    def test_expired_access_rejected(self):
        now = int(datetime.now(timezone.utc).timestamp())
        with self.assertRaises(PermissionError):
            self.factory.verifier().verify(self.factory.token(iat=now - 1200,
                                                              nbf=now - 1200,
                                                              exp=now - 600))

    def test_missing_required_claim_rejected(self):
        token = self.factory.token()
        # create a properly signed but incomplete token
        payload = {
            "iss": ISS, "aud": AUD, "sub": SUB, "client_id": CLIENT,
            "exp": int(datetime.now(timezone.utc).timestamp()) + 300,
        }
        token = jwt.encode(payload, self.factory.private, algorithm="RS256",
                           headers={"kid":"fixture-key-2026", "typ":"at+jwt"})
        with self.assertRaises(PermissionError):
            self.factory.verifier().verify(token)

    def test_excessive_lifetime_rejected(self):
        now = int(datetime.now(timezone.utc).timestamp())
        with self.assertRaisesRegex(PermissionError, "lifetime"):
            self.factory.verifier().verify(self.factory.token(exp=now+7200))

    def test_missing_scope_rejected(self):
        principal = self.factory.verifier().verify(self.factory.token(scope="openid"))
        with self.assertRaisesRegex(PermissionError, "scope"):
            principal.require_scope("lhfm:approval:write")

    def test_jwks_rejects_duplicate_or_private_key(self):
        keys = [deepcopy(self.factory.jwks["keys"][0])]
        with self.assertRaisesRegex(ValueError, "unique"):
            AccessTokenVerifier(issuer=ISS, audience=AUD,
                                jwks={"keys": keys + keys},
                                allowed_client_ids=(CLIENT,))
        keys[0]["d"] = "private-content"
        with self.assertRaisesRegex(ValueError, "public signature"):
            AccessTokenVerifier(issuer=ISS, audience=AUD,
                                jwks={"keys": keys},
                                allowed_client_ids=(CLIENT,))

    def test_token_directed_signature_key_url_rejected(self):
        token = jwt.encode(
            {"iss": ISS}, self.factory.private, algorithm="RS256",
            headers={"kid": "fixture-key-2026", "typ": "at+jwt",
                     "jku": "https://attacker.invalid/jwks.json"},
        )
        with self.assertRaisesRegex(PermissionError, "token-directed"):
            self.factory.verifier().verify(token)

    def test_trusted_jwks_atomically_rotates_and_retires_previous_key(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "jwks.json"
            path.write_text(json.dumps(self.factory.jwks), encoding="utf-8")
            verifier = AccessTokenVerifier.from_trusted_file(
                issuer=ISS, audience=AUD, jwks_path=path,
                allowed_client_ids=(CLIENT,),
            )
            old = self.factory.token()
            self.assertEqual(verifier.verify(old).subject, SUB)

            replacement = TestTokenFactory()
            replacement.jwks["keys"][0]["kid"] = "rotated-public-key"
            token = jwt.encode(
                {
                    "iss": ISS, "aud": AUD, "sub": SUB, "client_id": CLIENT,
                    "iat": int(datetime.now(timezone.utc).timestamp()),
                    "nbf": int(datetime.now(timezone.utc).timestamp()),
                    "exp": int(datetime.now(timezone.utc).timestamp()) + 600,
                    "jti": uuid4().hex, "scope": "lhfm:audit:execute",
                },
                replacement.private, algorithm="RS256",
                headers={"kid": "rotated-public-key", "typ": "at+jwt"},
            )
            staged = root / "next.json"
            staged.write_text(json.dumps(replacement.jwks), encoding="utf-8")
            staged.replace(path)
            self.assertEqual(verifier.verify(token).subject, SUB)
            with self.assertRaisesRegex(PermissionError, "unrecognized"):
                verifier.verify(old)

    def test_invalid_jwks_replacement_fails_closed_until_fixed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "jwks.json"
            path.write_text(json.dumps(self.factory.jwks), encoding="utf-8")
            verifier = AccessTokenVerifier.from_trusted_file(
                issuer=ISS, audience=AUD, jwks_path=path,
                allowed_client_ids=(CLIENT,),
            )
            token = self.factory.token()
            self.assertEqual(verifier.verify(token).subject, SUB)
            staged = root / "broken.json"
            staged.write_text('{"keys":[]}', encoding="utf-8")
            staged.replace(path)
            with self.assertRaisesRegex(PermissionError, "verification keys unavailable"):
                verifier.verify(token)
            restored = root / "fixed.json"
            restored.write_text(json.dumps(self.factory.jwks), encoding="utf-8")
            restored.replace(path)
            self.assertEqual(verifier.verify(token).subject, SUB)

    def test_trusted_file_rejects_symlink(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "jwks.json"
            path.write_text(json.dumps(self.factory.jwks), encoding="utf-8")
            linked = Path(d) / "linked.json"
            linked.symlink_to(path)
            with self.assertRaisesRegex(ValueError, "symlinked"):
                AccessTokenVerifier.from_trusted_file(
                    issuer=ISS, audience=AUD, jwks_path=linked,
                    allowed_client_ids=(CLIENT,),
                )


@unittest.skipUnless(bool(os.environ.get("LHFM_DB_HOST")), "real MariaDB required")
class AuthenticatedServiceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.factory = TestTokenFactory()

    def setUp(self):
        self.key = b"only-for-synthetic-oidc-mariadb-tests-32"
        self.registry = ApprovalRegistry.from_environment()
        self.service = AuthenticatedApprovalService(
            verifier=self.factory.verifier(),
            registry=self.registry, approval_key=self.key,
        )
        self.rule = json.loads((BASE / "rule.json").read_text(encoding="utf-8"))
        self.contract = BASE / "synthetic_agreement.txt"
        from hashlib import sha256
        self.document_sha = sha256(self.contract.read_bytes()).hexdigest()

    def approve(self, token=None):
        return self.service.approve(
            self.factory.token() if token is None else token, rule=self.rule,
            document_sha256=self.document_sha, source_revision_id="REV-SYN-1",
            approval_id="AUTH-SYN-" + uuid4().hex,
            **SCOPE,
        )

    def test_token_can_issue_real_registered_approval(self):
        receipt = self.approve()
        with self.registry.guard(receipt, rule=self.rule, key=self.key,
                                 document_sha256=self.document_sha,
                                 **SCOPE) as active:
            self.assertEqual(active["revocation_status"], "ACTIVE_LOCKED_AT_DISPATCH")

    def test_unsigned_user_identity_cannot_issue_receipt(self):
        with self.assertRaises(PermissionError):
            self.approve(token="REVIEWER-SYN-1")

    def test_wrong_jwt_subject_denied_by_database_grant(self):
        with self.assertRaises(PermissionError):
            self.approve(token=self.factory.token(sub="NOT-AN-APPROVED-REVIEWER"))

    def test_cross_tenant_approval_denied(self):
        with self.assertRaisesRegex(PermissionError, "grant"):
            self.service.approve(
                self.factory.token(), rule=self.rule,
                document_sha256=self.document_sha,
                source_revision_id="REV-SYN-1",
                approval_id="AUTH-SYN-" + uuid4().hex,
                tenant_id="OTHER-TENANT", legal_entity_id=SCOPE["legal_entity_id"],
            )

    def test_revocation_requires_access_scope_and_live_db_grant(self):
        receipt = self.approve()
        with self.assertRaisesRegex(PermissionError, "scope"):
            self.service.revoke(
                self.factory.token(scope="openid"), approval_id=receipt["approval_id"],
                **SCOPE,
            )
        self.assertTrue(self.service.revoke(
            self.factory.token(), approval_id=receipt["approval_id"], **SCOPE,
        ))
        with self.assertRaises(PermissionError):
            with self.registry.guard(receipt, rule=self.rule, key=self.key,
                                     document_sha256=self.document_sha, **SCOPE):
                pass

    def audit(self, receipt, token=None):
        return self.service.audit_csv(
            self.factory.token() if token is None else token,
            rule_path=BASE / "rule.json",
            transactions_path=BASE / "transactions.csv",
            settlements_path=BASE / "settlements.csv",
            contract_source_path=self.contract,
            approval_receipt=receipt, source_system="erp",
            controls=json.loads((BASE / "source_controls.json").read_text()),
            completeness={"transactions_complete":True,
                          "settlements_complete":True,
                          "agreements_complete":True},
            **SCOPE,
        )

    def test_authenticated_full_csv_audit_and_revoke(self):
        receipt = self.approve()
        result = self.audit(receipt)
        self.assertEqual(result["status"], "EVIDENCED")
        self.assertEqual(result["difference_net"], "2500.00")
        self.assertEqual(result["fee_due_net"], "0.00")
        self.service.revoke(self.factory.token(), approval_id=receipt["approval_id"], **SCOPE)
        revoked = self.audit(receipt)
        self.assertFalse(revoked["audit_executed"])
        self.assertIsNone(revoked["difference_net"])

    def test_missing_scope_blocks_before_file_import(self):
        receipt = self.approve()
        with self.assertRaisesRegex(PermissionError, "scope"):
            self.audit(receipt, token=self.factory.token(scope="openid"))

    def test_token_reverification_at_dispatch_is_enforced(self):
        receipt = self.approve()
        valid = self.factory.verifier().verify(self.factory.token())
        with patch.object(self.service.verifier, "verify",
                          side_effect=[valid, PermissionError("token expired")]):
            blocked = self.audit(receipt, token="synthetic-mocked-token")
        self.assertFalse(blocked["audit_executed"])
        self.assertIsNone(blocked["difference_net"])
        self.assertIn("APPROVAL_NOT_ACTIVE_AT_DISPATCH", blocked["warnings"])


if __name__ == "__main__":
    unittest.main()
