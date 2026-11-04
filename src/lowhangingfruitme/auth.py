"""Resource-server authentication for RFC 9068-style JWT access tokens.

Trusted issuer, resource audience, accepted client IDs and PUBLIC JWKS come
from trusted deployment configuration; never from a token, request or user.
The library does not run OAuth login, issue access tokens, fetch JWKS URLs or
provision reviewers. Those remain external IdP/admin responsibilities.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import os
import stat
import threading
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

import jwt


@dataclass(frozen=True, slots=True)
class VerifiedPrincipal:
    """Verified identity only; DB authorization must still be enforced."""
    subject: str
    issuer: str
    client_id: str
    token_id: str
    expires_at: int
    scopes: frozenset[str]

    def require_scope(self, scope: str) -> None:
        if scope not in self.scopes:
            raise PermissionError("required access-token scope is missing")


class AccessTokenVerifier:
    """Asymmetric signature validator with pinned, trusted local JWKS.

    Only RS256 JWT ACCESS tokens with typ=at+jwt are accepted. This avoids
    accidentally accepting an OIDC ID token as a resource-server credential.
    """

    def __init__(
        self, *, issuer: str, audience: str, jwks: dict[str, Any],
        allowed_client_ids: tuple[str, ...],
        max_lifetime_seconds: int = 3600,
    ) -> None:
        if not isinstance(issuer, str) or not issuer.startswith("https://"):
            raise ValueError("trusted issuer must be a configured HTTPS URI")
        if not isinstance(audience, str) or not audience.strip():
            raise ValueError("trusted resource audience must be explicitly configured")
        if not isinstance(allowed_client_ids, tuple) or not allowed_client_ids or any(
            not isinstance(v, str) or not v.strip() for v in allowed_client_ids
        ):
            raise ValueError("trusted client IDs must be nonempty")
        if type(max_lifetime_seconds) is not int or not 60 <= max_lifetime_seconds <= 3600:
            raise ValueError("access-token lifetime policy must be 60..3600 seconds")
        if not isinstance(jwks, dict) or not isinstance(jwks.get("keys"), list):
            raise ValueError("trusted JWKS must contain keys")
        self._key_lock = threading.RLock()
        self._jwks_file: Path | None = None
        self._jwks_digest: str | None = None
        self._keys: dict[str, Any] = {}
        for item in jwks["keys"]:
            if not isinstance(item, dict):
                raise ValueError("invalid JWKS entry")
            kid = item.get("kid")
            if not isinstance(kid, str) or not kid or kid in self._keys:
                raise ValueError("JWKS kid must be unique and nonempty")
            if item.get("kty") != "RSA" or item.get("alg") not in (None, "RS256"):
                raise ValueError("only RSA/RS256 verification keys are supported")
            if item.get("use") not in (None, "sig") or "d" in item:
                raise ValueError("JWKS must include public signature keys only")
            if item.get("key_ops") not in (None, ["verify"]):
                raise ValueError("JWKS must not permit non-verification operations")
            # Only public JWK parameters; reject unexpected key material or
            # token-directed URLs/other JOSE extensions.
            if set(item) - {"kty", "kid", "alg", "use", "key_ops", "n", "e"}:
                raise ValueError("unrecognized JWKS key metadata")
            try:
                self._keys[kid] = jwt.PyJWK.from_dict(item, algorithm="RS256").key
            except (ValueError, TypeError, jwt.PyJWTError) as exc:
                raise ValueError("invalid RSA verification key") from exc
        if not self._keys:
            raise ValueError("no trusted signing keys")
        self.issuer = issuer
        self.audience = audience
        self.allowed_client_ids = frozenset(allowed_client_ids)
        self.max_lifetime_seconds = max_lifetime_seconds

    @staticmethod
    def _read_public_jwks_file(path: Path) -> bytes:
        """Bounded, no-follow regular file read from trusted deployment storage."""
        if not path.is_absolute() or path.is_symlink():
            raise ValueError("trusted JWKS path must be absolute and not symlinked")
        flags = os.O_RDONLY
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        descriptor = os.open(path, flags)
        try:
            metadata = os.fstat(descriptor)
            if (not stat.S_ISREG(metadata.st_mode)
                    or not 0 < metadata.st_size <= 128 * 1024):
                raise ValueError("trusted JWKS file missing or outside size bound")
            with os.fdopen(descriptor, "rb", closefd=False) as stream:
                raw = stream.read(128 * 1024 + 1)
            if len(raw) > 128 * 1024:
                raise ValueError("trusted JWKS file too large")
            return raw
        finally:
            os.close(descriptor)

    @classmethod
    def from_trusted_file(
        cls, *, issuer: str, audience: str, jwks_path: str | Path,
        allowed_client_ids: tuple[str, ...],
    ) -> "AccessTokenVerifier":
        """Use ONLY pinned operator-provisioned file; no URL/JWKS network fetch."""
        path = Path(jwks_path).absolute()
        raw = cls._read_public_jwks_file(path)
        verifier = cls(
            issuer=issuer, audience=audience,
            jwks=json.loads(raw.decode("utf-8")),
            allowed_client_ids=allowed_client_ids,
        )
        verifier._jwks_file = path
        verifier._jwks_digest = sha256(raw).hexdigest()
        return verifier

    def _refresh_trusted_public_keys(self) -> None:
        """Read-before-verify; invalid/missing replacement always fails closed.

        Public JWKS updates must be published atomically by a trusted operator.
        A newly published valid file takes effect without a service restart.
        """
        if self._jwks_file is None:
            return
        try:
            # Hold the same lock during file reading, validation and swap.
            # Otherwise two concurrent verifications could publish an old
            # snapshot after a newer JWKS revision had already been installed.
            with self._key_lock:
                raw = self._read_public_jwks_file(self._jwks_file)
                digest = sha256(raw).hexdigest()
                if digest == self._jwks_digest:
                    return
                candidate = AccessTokenVerifier(
                    issuer=self.issuer, audience=self.audience,
                    jwks=json.loads(raw.decode("utf-8")),
                    allowed_client_ids=tuple(sorted(self.allowed_client_ids)),
                    max_lifetime_seconds=self.max_lifetime_seconds,
                )
                self._keys = candidate._keys
                self._jwks_digest = digest
        except (OSError, UnicodeError, ValueError, TypeError, KeyError,
                json.JSONDecodeError) as exc:
            raise PermissionError("trusted JWT verification keys unavailable") from exc

    def verify(self, raw_token: str) -> VerifiedPrincipal:
        if not isinstance(raw_token, str) or not 30 <= len(raw_token) <= 8192:
            raise PermissionError("invalid access token")
        self._refresh_trusted_public_keys()
        try:
            header = jwt.get_unverified_header(raw_token)
            if header.get("typ") not in ("at+jwt", "application/at+jwt"):
                raise PermissionError("ID tokens or untyped JWTs cannot authorize API access")
            if header.get("alg") != "RS256" or set(header) - {"typ", "alg", "kid"}:
                raise PermissionError("unsupported or token-directed signature metadata")
            kid = header.get("kid")
            with self._key_lock:
                key = self._keys.get(kid) if isinstance(kid, str) else None
            if key is None:
                raise PermissionError("unrecognized trusted signing key")
            claims = jwt.decode(
                raw_token, key=key,
                algorithms=["RS256"], audience=self.audience, issuer=self.issuer,
                leeway=0,
                options={
                    "require": ["iss", "aud", "sub", "exp", "iat", "nbf", "jti", "client_id"],
                    "verify_signature": True,
                },
            )
        except jwt.PyJWTError as exc:
            raise PermissionError("invalid or expired access token") from exc
        if any(type(claims.get(k)) is not int for k in ("iat", "nbf", "exp")):
            raise PermissionError("invalid token timestamp types")
        if (claims["exp"] <= claims["iat"]
                or claims["exp"] - claims["iat"] > self.max_lifetime_seconds
                or claims["nbf"] > claims["exp"]):
            raise PermissionError("invalid token lifetime")
        if any(not isinstance(claims.get(k), str) or not claims[k].strip()
               for k in ("sub", "jti", "client_id")):
            raise PermissionError("missing stable access-token identity")
        if claims["client_id"] not in self.allowed_client_ids:
            raise PermissionError("untrusted OAuth client ID")
        if type(claims.get("scope", "")) is not str:
            raise PermissionError("invalid token scope")
        scopes = frozenset(claims.get("scope", "").split())
        return VerifiedPrincipal(
            subject=claims["sub"], issuer=claims["iss"], client_id=claims["client_id"],
            token_id=claims["jti"], expires_at=claims["exp"], scopes=scopes,
        )
