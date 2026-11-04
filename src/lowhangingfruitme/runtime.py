"""Fail-closed preflight of the private financial API's live local dependencies.

Executed under the exact unprivileged API service UID before uvicorn launches.
No migrations, writes, account provisioning, credential printing or HTTP bypass.
"""
from __future__ import annotations

import os
import re
from pathlib import Path
import stat
import sys
from typing import Callable, Mapping

from .approval_service import AuthenticatedApprovalService
from .api.uploads import ClamAVScanner
from .docling_subprocess import DoclingSubprocessExtractor
from .schema import require_operational_schema


class RuntimeNotReady(RuntimeError):
    """Reject incomplete or unsafe operator configuration."""


def _private_root(value: str | None, *, owner_uid: int) -> Path:
    if not value:
        raise RuntimeNotReady("PRIVATE_STORAGE_NOT_CONFIGURED")
    path = Path(value)
    if not path.is_absolute():
        raise RuntimeNotReady("PRIVATE_STORAGE_NOT_ABSOLUTE")
    for member in (path, *path.parents):
        if member.is_symlink():
            raise RuntimeNotReady("PRIVATE_STORAGE_SYMLINK")
    try:
        details = path.stat()
    except OSError as exc:
        raise RuntimeNotReady("PRIVATE_STORAGE_UNAVAILABLE") from exc
    if (not stat.S_ISDIR(details.st_mode)
            or details.st_uid != owner_uid
            or stat.S_IMODE(details.st_mode) != 0o700):
        raise RuntimeNotReady("PRIVATE_STORAGE_OWNER_OR_MODE")
    return path.resolve(strict=True)


def validate_runtime_config(
    env: Mapping[str, str], *, uid: int,
) -> tuple[Path, Path, str, str]:
    """Side-effect-free config gate before connecting to real dependencies."""
    if uid == 0:
        raise RuntimeNotReady("REFUSE_ROOT_API_WORKER")
    if env.get("LHFM_DB_HOST") != "127.0.0.1":
        raise RuntimeNotReady("DB_MUST_USE_LOOPBACK")
    if not env.get("LHFM_DB_USER") or not env.get("LHFM_DB_PASSWORD"):
        raise RuntimeNotReady("DB_CREDENTIALS_NOT_CONFIGURED")
    if env["LHFM_DB_USER"].lower() in ("root", "mysql", "admin"):
        raise RuntimeNotReady("PRIVILEGED_DB_ACCOUNT_FORBIDDEN")
    database = env.get("LHFM_DB_NAME", "")
    if (not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]{2,63}", database)
            or database.lower() in ("mysql", "information_schema", "performance_schema", "sys")
            or database.lower().startswith("lhfm_restore_")):
        raise RuntimeNotReady("INVALID_LIVE_DATABASE")
    try:
        port = int(env.get("LHFM_DB_PORT", "3306"))
    except (ValueError, TypeError) as exc:
        raise RuntimeNotReady("INVALID_DB_PORT") from exc
    if not 1 <= port <= 65535:
        raise RuntimeNotReady("INVALID_DB_PORT")

    sources = _private_root(env.get("LHFM_API_SOURCE_ROOT"), owner_uid=uid)
    uploads = _private_root(env.get("LHFM_UPLOAD_ROOT"), owner_uid=uid)
    if (sources == uploads or sources.is_relative_to(uploads)
            or uploads.is_relative_to(sources)):
        raise RuntimeNotReady("PRIVATE_STORAGE_ROOTS_OVERLAP")
    socket = env.get("LHFM_CLAMD_UNIX_SOCKET")
    if not socket or not Path(socket).is_absolute() or Path(socket).is_symlink():
        raise RuntimeNotReady("CLAMAV_SOCKET_NOT_CONFIGURED")
    launcher = env.get("LHFM_DOCLING_SANDBOX_LAUNCHER")
    if not launcher or not Path(launcher).is_absolute():
        raise RuntimeNotReady("DOCUMENT_SANDBOX_NOT_CONFIGURED")
    for field in (
        "LHFM_OIDC_ISSUER", "LHFM_OIDC_AUDIENCE", "LHFM_OIDC_JWKS_FILE",
        "LHFM_OIDC_ALLOWED_CLIENT_IDS", "LHFM_APPROVAL_KEY_HEX",
    ):
        if not env.get(field):
            raise RuntimeNotReady("AUTH_CONFIGURATION_INCOMPLETE")
    if (not env["LHFM_OIDC_ISSUER"].startswith("https://")
            or not Path(env["LHFM_OIDC_JWKS_FILE"]).is_absolute()):
        raise RuntimeNotReady("AUTH_CONFIGURATION_INCOMPLETE")
    return sources, uploads, socket, launcher


def verify_runtime(
    *,
    env: Mapping[str, str] | None = None,
    uid: int | None = None,
    service_factory: Callable[[], AuthenticatedApprovalService] | None = None,
    scanner_factory: Callable[[str], ClamAVScanner] = ClamAVScanner,
    extractor_factory: Callable[[str], DoclingSubprocessExtractor] | None = None,
) -> dict[str, str]:
    """Perform read-only DB, real ClamAV and isolated Docling checks."""
    values = os.environ if env is None else env
    owner = os.geteuid() if uid is None else uid
    _sources, _uploads, socket, launcher = validate_runtime_config(values, uid=owner)
    make_service = service_factory or AuthenticatedApprovalService.from_environment
    service = make_service()
    require_operational_schema(service.registry._connect)
    scanner_factory(socket).ping()
    make_extractor = extractor_factory or (
        lambda path: DoclingSubprocessExtractor(launcher=path)
    )
    make_extractor(launcher).preflight()
    return {
        "source_storage": "private",
        "upload_storage": "private",
        "schema": "compatible",
        "oidc": "trusted_jwks_configured",
        "clamav": "responsive",
        "docling": "network_isolation_preflight_passed",
    }


def main() -> int:
    try:
        verify_runtime()
    except Exception:
        # Never print private paths, credentials or DB error messages.
        print("LHFM_RUNTIME_NOT_READY", file=sys.stderr)
        return 2
    print("LHFM_RUNTIME_LOCAL_PREFLIGHT_PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
