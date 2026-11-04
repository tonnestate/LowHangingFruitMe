"""Private staged uploads with explicit ClamAV scanning; never a financial approval.

Uploads are untrusted until independently scanned AND format-checked, and even
then cannot directly become audit inputs. An operator must build and approve a
separate immutable source manifest before any calculation.
"""
from __future__ import annotations

import asyncio
from contextlib import contextmanager
from hashlib import sha256
import os
from pathlib import Path
import socket
import stat
import tempfile
import struct
from typing import Any, Protocol, Iterator
from uuid import uuid4

from .store import BundleNotFound
from ..approval_registry import ApprovalRegistry
from ..universal_import import _source

FORMATS: dict[str, tuple[str, str]] = {
    "ERP_CSV": (".csv", "text/csv"),
    "ERP_XLSX": (".xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
    "INVOICE_XML": (".xml", "application/xml"),
    "CONTRACT_PDF": (".pdf", "application/pdf"),
    "CONTRACT_DOCX": (".docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
    "RECOVERY_PDF": (".pdf", "application/pdf"),
}
MAX_UPLOAD = 16 * 1024 * 1024
MIN_UPLOAD = 1


class UploadRejected(ValueError):
    """File declined due to an invalid upload, suspicious format or scan result."""


class ScannerUnavailable(RuntimeError):
    """Scanning is unavailable. No upload may be promoted."""


class Scanner(Protocol):
    def scan(self, path: Path) -> bool:
        """Returns True only when a trusted scanner explicitly reports clean."""


class ClamAVScanner:
    """ClamAV clamd INSTREAM over a configured LOCAL UNIX socket, fail closed."""

    def __init__(self, unix_socket: str | Path, *, timeout: float = 20.0) -> None:
        p = Path(unix_socket)
        if not p.is_absolute() or not 1 <= timeout <= 60:
            raise ValueError("trusted scanner requires absolute UNIX socket and bounded timeout")
        self.unix_socket = str(p)
        self.timeout = timeout

    def ping(self) -> None:
        """Verify the actual local daemon protocol, not just socket existence."""
        try:
            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
                sock.settimeout(min(self.timeout, 3.0))
                sock.connect(self.unix_socket)
                sock.sendall(b"zPING\0")
                reply = sock.recv(64)
        except (OSError, TimeoutError) as exc:
            raise ScannerUnavailable("malware scanner ping unavailable") from exc
        if reply.split(b"\0", 1)[0] != b"PONG":
            raise ScannerUnavailable("malware scanner ping invalid")

    def scan(self, path: Path) -> bool:
        try:
            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
                sock.settimeout(self.timeout)
                sock.connect(self.unix_socket)
                sock.sendall(b"zINSTREAM\0")
                with path.open("rb") as data:
                    while chunk := data.read(32768):
                        sock.sendall(struct.pack(">I", len(chunk)))
                        sock.sendall(chunk)
                sock.sendall(struct.pack(">I", 0))
                answer = bytearray()
                while len(answer) < 2048:
                    chunk = sock.recv(2048 - len(answer))
                    if not chunk:
                        break
                    answer.extend(chunk)
                    if b"\0" in chunk:
                        break
        except (OSError, TimeoutError) as exc:
            raise ScannerUnavailable("trusted scanner unavailable") from exc
        result = bytes(answer).split(b"\0", 1)[0].strip()
        if result == b"stream: OK":
            return True
        if result.endswith(b" FOUND"):
            return False
        raise ScannerUnavailable("scanner did not return a valid verdict")


class UploadService:
    """Tenant scoped upload ledger + private append-only-by-ID blob filenames."""

    def __init__(
        self, *, registry: ApprovalRegistry, root: str | Path,
        scanner: Scanner,
    ) -> None:
        if scanner is None or not callable(getattr(scanner, "scan", None)):
            raise RuntimeError("a trusted malware scanner is mandatory")
        self._connect = registry._connect
        source = Path(root)
        if not source.is_absolute() or source.is_symlink() or not source.is_dir():
            raise ValueError("upload root must be an existing absolute non-symlink directory")
        self.root = source.resolve(strict=True)
        if stat.S_IMODE(self.root.stat().st_mode) & 0o077:
            raise ValueError("private upload directory must not be group/world accessible")
        self.scanner = scanner

    def create_intent(
        self, *, tenant_id: str, legal_entity_id: str,
        reviewer_id: str, kind: str, byte_size: int, digest: str,
    ) -> dict[str, Any]:
        if kind not in FORMATS:
            raise ValueError("unsupported upload category")
        if type(byte_size) is not int or not MIN_UPLOAD <= byte_size <= MAX_UPLOAD:
            raise ValueError("upload outside supported 1..16 MiB range")
        if (not isinstance(digest, str) or len(digest) != 64
                or any(c not in "0123456789abcdef" for c in digest)):
            raise ValueError("exact lowercase SHA-256 required")
        upload_id = str(uuid4())
        db = self._connect()
        try:
            with db.cursor() as cur:
                cur.execute(
                    """INSERT INTO lhfm_uploads
                       (upload_id, tenant_id, legal_entity_id, reviewer_id,
                        kind, expected_size, expected_sha256, state, expires_at)
                       VALUES (%s,%s,%s,%s,%s,%s,%s,'PENDING',
                               DATE_ADD(UTC_TIMESTAMP(6), INTERVAL 15 MINUTE))""",
                    (upload_id, tenant_id, legal_entity_id, reviewer_id,
                     kind, byte_size, digest),
                )
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()
        return {"upload_id": upload_id, "state": "PENDING",
                "kind": kind, "expected_size": byte_size,
                "expires_in_seconds": 900}

    def get_upload(
        self, *, upload_id: str, tenant_id: str,
        legal_entity_id: str, reviewer_id: str,
    ) -> dict[str, Any]:
        db = self._connect()
        try:
            with db.cursor() as cur:
                cur.execute(
                    """SELECT upload_id, kind, state, expected_size, expected_sha256
                       FROM lhfm_uploads WHERE upload_id=%s AND tenant_id=%s
                       AND legal_entity_id=%s AND reviewer_id=%s""",
                    (upload_id, tenant_id, legal_entity_id, reviewer_id),
                )
                data = cur.fetchone()
            if data is None:
                raise BundleNotFound("upload missing or outside authenticated scope")
            return data
        finally:
            db.close()

    def claim_upload(
        self, *, upload_id: str, tenant_id: str,
        legal_entity_id: str, reviewer_id: str,
    ) -> dict[str, Any]:
        """One writer only. The committed DB state survives worker crashes."""
        db = self._connect()
        try:
            with db.cursor() as cur:
                cur.execute(
                    """UPDATE lhfm_uploads SET state='RECEIVING'
                       WHERE upload_id=%s AND tenant_id=%s
                       AND legal_entity_id=%s AND reviewer_id=%s
                       AND state='PENDING' AND expires_at>UTC_TIMESTAMP(6)""",
                    (upload_id, tenant_id, legal_entity_id, reviewer_id),
                )
                if cur.rowcount != 1:
                    raise UploadRejected("upload missing, expired or already consumed")
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()
        return self.get_upload(
            upload_id=upload_id, tenant_id=tenant_id,
            legal_entity_id=legal_entity_id, reviewer_id=reviewer_id,
        )

    def settle(
        self, *, upload_id: str, state: str,
        tenant_id: str, legal_entity_id: str, reviewer_id: str,
    ) -> None:
        if state not in ("CLEAN", "REJECTED"):
            raise ValueError("invalid upload outcome")
        db = self._connect()
        try:
            with db.cursor() as cur:
                cur.execute(
                    """UPDATE lhfm_uploads SET state=%s,
                       finished_at=UTC_TIMESTAMP(6)
                       WHERE upload_id=%s AND tenant_id=%s
                         AND legal_entity_id=%s AND reviewer_id=%s
                         AND state='RECEIVING'""",
                    (state, upload_id, tenant_id, legal_entity_id, reviewer_id),
                )
                if cur.rowcount != 1:
                    raise UploadRejected("upload reservation state was lost")
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    @contextmanager
    def snapshot_clean(
        self, *, upload_id: str, tenant_id: str,
        legal_entity_id: str, reviewer_id: str,
        accepted_kinds: tuple[str, ...],
    ) -> Iterator[tuple[Path, dict[str, Any]]]:
        """Only the authenticated owner may read a clean immutable copy.

        Path is derived exclusively from the DB-scoped UUID and validated
        server-side kind. Original uploads never enter the audit source root.
        """
        record = self.get_upload(
            upload_id=upload_id, tenant_id=tenant_id,
            legal_entity_id=legal_entity_id, reviewer_id=reviewer_id,
        )
        if record["state"] != "CLEAN" or record["kind"] not in accepted_kinds:
            raise UploadRejected("upload not clean or wrong dataset/document class")
        suffix = FORMATS[record["kind"]][0]
        target = self.root / (upload_id + suffix)
        if target.is_symlink() or not target.is_file():
            raise UploadRejected("clean source is missing or unsafe")
        if stat.S_IMODE(target.stat().st_mode) & 0o077:
            raise UploadRejected("source permissions are not private")
        with tempfile.TemporaryDirectory(prefix="lhfm-source-snapshot-") as tmp:
            copied = Path(tmp) / ("source" + suffix)
            count = 0
            digest = sha256()
            with target.open("rb") as inp, copied.open("xb") as out:
                while chunk := inp.read(65536):
                    count += len(chunk)
                    if count > MAX_UPLOAD or count > record["expected_size"]:
                        raise UploadRejected("source changed since upload")
                    digest.update(chunk)
                    out.write(chunk)
            if (count != record["expected_size"] or
                    digest.hexdigest() != record["expected_sha256"]):
                raise UploadRejected("source changed since scan")
            yield copied, record

    async def receive(
        self, *, upload_id: str, tenant_id: str,
        legal_entity_id: str, reviewer_id: str, chunks: Any,
    ) -> dict[str, Any]:
        record = self.claim_upload(
            upload_id=upload_id, tenant_id=tenant_id,
            legal_entity_id=legal_entity_id, reviewer_id=reviewer_id,
        )
        suffix, _ = FORMATS[record["kind"]]
        staging = self.root / (upload_id + ".part")
        final = self.root / (upload_id + suffix)
        accepted = False
        try:
            flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
            if hasattr(os, "O_NOFOLLOW"):
                flags |= os.O_NOFOLLOW
            fd = os.open(staging, flags, 0o600)
            count = 0
            digest = sha256()
            with os.fdopen(fd, "wb") as target:
                async for chunk in chunks:
                    if not isinstance(chunk, bytes):
                        raise UploadRejected("invalid request byte stream")
                    count += len(chunk)
                    if count > record["expected_size"] or count > MAX_UPLOAD:
                        raise UploadRejected("uploaded byte count exceeds declared size")
                    digest.update(chunk)
                    target.write(chunk)
                target.flush()
                os.fsync(target.fileno())
            if count != record["expected_size"] or digest.hexdigest() != record["expected_sha256"]:
                raise UploadRejected("uploaded size or SHA-256 differs from declared source")
            verdict = await asyncio.to_thread(self.scanner.scan, staging)
            if verdict is not True:
                raise UploadRejected("malware scan did not approve this content")
            # Validate only AFTER trusted malware screening. XML parser rejects
            # external entities, Office parser bounds ZIP expansion.
            # _source needs the correct suffix. The verified bytes are already
            # in the exclusive .part file, so use os.link for the inspected name.
            inspected = self.root / (upload_id + ".inspect" + suffix)
            os.link(staging, inspected)
            try:
                try:
                    _source(inspected)
                except (ValueError, RuntimeError) as exc:
                    raise UploadRejected("file format validation failed") from exc
            finally:
                inspected.unlink(missing_ok=True)
            try:
                os.link(staging, final)  # O_EXCL-like: do not replace pre-existing path
            except FileExistsError as exc:
                raise UploadRejected("upload filename collision") from exc
            staging.unlink()
            self.settle(
                upload_id=upload_id, state="CLEAN", tenant_id=tenant_id,
                legal_entity_id=legal_entity_id, reviewer_id=reviewer_id,
            )
            accepted = True
            return {"upload_id": upload_id, "state": "CLEAN",
                    "kind": record["kind"], "byte_size": count,
                    "sha256": digest.hexdigest(),
                    "usable_for_audit": False}
        finally:
            if not accepted:
                staging.unlink(missing_ok=True)
                final.unlink(missing_ok=True)
                try:
                    self.settle(
                        upload_id=upload_id, state="REJECTED",
                        tenant_id=tenant_id, legal_entity_id=legal_entity_id,
                        reviewer_id=reviewer_id,
                    )
                except Exception:
                    # Preserve the original reason, but never promote data.
                    pass
