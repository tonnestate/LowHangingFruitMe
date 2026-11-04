"""Encrypted MariaDB + private-file disaster-recovery rehearsal.

Operator maintenance only. No plaintext backup archives, no public API.
Restore ONLY into a pre-created EMPTY lhfm_restore_* database.
"""
from __future__ import annotations

import argparse
import configparser
from contextlib import ExitStack
from hashlib import sha256
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import subprocess
import sys
import tarfile
import tempfile

import pymysql
from pymysql.cursors import DictCursor
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.serialization import (
    load_pem_private_key, load_pem_public_key,
)
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey,
)

from .schema import require_operational_schema

PARTS = ("database.sql.age", "uploads.tar.age", "sources.tar.age")
NAME = re.compile(r"^[a-z][a-z0-9_]{2,63}$")
TABLE = re.compile(r"^lhfm_[a-z0-9_]+$")
MAX_MANIFEST = 4 * 1024 * 1024
MAX_FILE = 32 * 1024 * 1024
MAX_TOTAL = 16 * 1024**3


class DRError(RuntimeError):
    pass


def private_dir(path):
    path = Path(path)
    if not path.is_absolute() or path.is_symlink():
        raise DRError("absolute nonsymlink directory required")
    s = path.stat()
    if not stat.S_ISDIR(s.st_mode) or (os.geteuid() != 0 and s.st_uid != os.geteuid()) or s.st_mode & 0o077:
        raise DRError("operator directory must be owner-only")
    return path


def private_file(path):
    path = Path(path)
    if not path.is_absolute() or path.is_symlink():
        raise DRError("absolute nonsymlink file required")
    s = path.stat()
    if not stat.S_ISREG(s.st_mode) or (os.geteuid() != 0 and s.st_uid != os.geteuid()) or s.st_mode & 0o077:
        raise DRError("operator file must be owner-only")
    return path


def output(path):
    descriptor = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    return os.fdopen(descriptor, "wb")


def client_config(file):
    file = private_file(file)
    parser = configparser.RawConfigParser(interpolation=None)
    try:
        if not parser.read(file, encoding="utf-8"):
            raise DRError("MariaDB configuration unavailable")
        client = parser["client"]
        if client.get("host") != "127.0.0.1":
            raise DRError("only loopback MariaDB is permitted")
        port = int(client.get("port", "3306"))
        if not 1 <= port <= 65535:
            raise DRError("invalid MariaDB port")
        if not client.get("user") or not client.get("password"):
            raise DRError("missing MariaDB credentials")
        return dict(host="127.0.0.1", port=port, user=client["user"],
                    password=client["password"])
    except (KeyError, ValueError, configparser.Error) as exc:
        raise DRError("invalid MariaDB configuration") from exc


def connect(config, database):
    return pymysql.connect(**config, database=database, autocommit=False,
                           charset="utf8mb4", cursorclass=DictCursor,
                           connect_timeout=8, read_timeout=45)


def table_counts(config, database, *, must_be_empty=False):
    db = connect(config, database)
    try:
        with db.cursor() as cursor:
            cursor.execute("SHOW TABLES")
            names = sorted(next(iter(row.values())) for row in cursor.fetchall())
            if must_be_empty:
                if names:
                    raise DRError("restore destination must exist and be empty")
                return {}
            if not names or len(names) > 256 or any(not TABLE.fullmatch(n) for n in names):
                raise DRError("unsafe application schema listing")
            require_operational_schema(lambda: connect(config, database))
            result = {}
            for name in names:
                cursor.execute("SELECT COUNT(*) AS cnt FROM " + chr(96) + name + chr(96))
                result[name] = int(cursor.fetchone()["cnt"])
            return result
    finally:
        db.close()


def file_manifest(root):
    root = private_dir(root)
    result = {}
    total = 0
    owner = root.stat().st_uid
    for directory, children, filenames in os.walk(root, followlinks=False):
        children.sort()
        filenames.sort()
        for folder in children:
            s = (Path(directory) / folder).lstat()
            if (not stat.S_ISDIR(s.st_mode) or s.st_uid != owner
                    or s.st_mode & 0o077):
                raise DRError("symlinked or externally accessible directory")
        for filename in filenames:
            path = Path(directory) / filename
            s = path.lstat()
            if (not stat.S_ISREG(s.st_mode) or s.st_nlink != 1
                    or s.st_uid != owner or s.st_mode & 0o077
                    or s.st_size > MAX_FILE or len(result) >= 100000):
                raise DRError("unsafe or oversized private file")
            digest = sha256()
            size = 0
            with path.open("rb") as stream:
                while block := stream.read(1024 * 1024):
                    digest.update(block)
                    size += len(block)
                    if size > MAX_FILE:
                        raise DRError("private file grew beyond limit")
            after = path.lstat()
            if (s.st_ino, s.st_mtime_ns, s.st_size) != (
                    after.st_ino, after.st_mtime_ns, size):
                raise DRError("private source changed during maintenance")
            total += size
            if total > MAX_TOTAL:
                raise DRError("backup exceeds private file capacity")
            result[path.relative_to(root).as_posix()] = {
                "size": size, "sha256": digest.hexdigest(),
            }
    return result


def encrypt_stream(producer, *, recipient, target):
    first = subprocess.Popen(producer, stdout=subprocess.PIPE,
                             stdin=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        assert first.stdout is not None
        with output(target) as out:
            second = subprocess.Popen(["age", "-r", recipient],
                                      stdin=first.stdout, stdout=out,
                                      stderr=subprocess.DEVNULL)
            first.stdout.close()
            try:
                result2 = second.wait(timeout=900)
                result1 = first.wait(timeout=900)
            except subprocess.TimeoutExpired as exc:
                second.kill()
                first.kill()
                second.wait()
                first.wait()
                raise DRError("encrypted backup deadline exceeded") from exc
        if result1 or result2:
            raise DRError("failed encrypted backup component")
    finally:
        if first.poll() is None:
            first.kill()
            first.wait()


def encrypt_tar(root, entries, *, recipient, target):
    with output(target) as out:
        worker = subprocess.Popen(["age", "-r", recipient],
                                  stdin=subprocess.PIPE, stdout=out,
                                  stderr=subprocess.DEVNULL)
        try:
            assert worker.stdin is not None
            with tarfile.open(fileobj=worker.stdin, mode="w|") as tar:
                for relative, info in sorted(entries.items()):
                    path = root / relative
                    s = path.lstat()
                    if (not stat.S_ISREG(s.st_mode) or s.st_nlink != 1
                            or s.st_uid != root.stat().st_uid
                            or s.st_mode & 0o077
                            or s.st_size != info["size"]):
                        raise DRError("file changed during archive creation")
                    member = tarfile.TarInfo("data/" + relative)
                    member.size = s.st_size
                    member.mode = 0o600
                    member.mtime = 0
                    with path.open("rb") as stream:
                        tar.addfile(member, stream)
                    after = path.lstat()
                    if (s.st_ino, s.st_mtime_ns) != (after.st_ino, after.st_mtime_ns):
                        raise DRError("file changed during archive creation")
            if not worker.stdin.closed:
                worker.stdin.close()
            if worker.wait(timeout=900):
                raise DRError("private files could not be encrypted")
        finally:
            if worker.poll() is None:
                worker.kill()
                worker.wait()


def encrypt_manifest(payload, *, recipient, target):
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True,
                     separators=(",", ":")).encode("utf-8")
    if len(raw) > MAX_MANIFEST:
        raise DRError("backup manifest exceeds size limit")
    with output(target) as out:
        outcome = subprocess.run(["age", "-r", recipient], input=raw,
                                 stdout=out, stderr=subprocess.DEVNULL,
                                 timeout=60, check=False)
    if outcome.returncode:
        raise DRError("failed to encrypt backup manifest")


def sign_manifest(ciphertext, signing_key, signature):
    try:
        private = load_pem_private_key(private_file(signing_key).read_bytes(),
                                       password=None)
    except (ValueError,TypeError) as exc:
        raise DRError("invalid operator signing key") from exc
    if not isinstance(private,Ed25519PrivateKey):
        raise DRError("Ed25519 operator signing key required")
    with output(signature) as result:
        result.write(private.sign(private_file(ciphertext).read_bytes()))


def verify_signature(ciphertext, signature, verification_key):
    try:
        public = load_pem_public_key(private_file(verification_key).read_bytes())
        if not isinstance(public,Ed25519PublicKey):
            raise DRError("Ed25519 verification key required")
        raw = private_file(signature).read_bytes()
        if len(raw) != 64:
            raise DRError("invalid backup signature length")
        public.verify(raw,private_file(ciphertext).read_bytes())
    except (ValueError,TypeError,InvalidSignature) as exc:
        raise DRError("backup signing authority verification failed") from exc


def create_backup(*, defaults_file, database, upload_root,
                  source_root, destination, recipient, signing_key):
    if os.environ.get("LHFM_MAINTENANCE_CONFIRMED") != "YES":
        raise DRError("operator must confirm stopped writes and maintenance")
    if not NAME.fullmatch(database) or database.startswith("lhfm_restore_"):
        raise DRError("invalid source database name")
    if not recipient.startswith("age1") or not 10 < len(recipient) < 200:
        raise DRError("real age public recipient required")
    if not shutil.which("age") or not shutil.which("mariadb-dump"):
        raise DRError("age and mariadb-dump must be installed")
    credentials = client_config(defaults_file)
    uploads, sources = private_dir(upload_root), private_dir(source_root)
    destination = Path(destination)
    private_dir(destination.parent)
    if uploads.resolve() == sources.resolve():
        raise DRError("uploads and sources must be separate")
    if any(destination.is_relative_to(root) or root.is_relative_to(destination)
           for root in (uploads, sources)):
        raise DRError("backup cannot overlap private roots")
    before = table_counts(credentials, database)
    uf, sf = file_manifest(uploads), file_manifest(sources)
    destination.mkdir(mode=0o700)
    try:
        encrypt_stream(
            ["mariadb-dump", "--defaults-extra-file=" + str(defaults_file),
             "--single-transaction", "--quick", "--hex-blob",
             "--routines", "--triggers", "--events", "--no-create-db",
             "--skip-lock-tables", database],
            recipient=recipient, target=destination / PARTS[0],
        )
        encrypt_tar(uploads, uf, recipient=recipient, target=destination / PARTS[1])
        encrypt_tar(sources, sf, recipient=recipient, target=destination / PARTS[2])
        if table_counts(credentials, database) != before:
            raise DRError("database changed during backup")
        if file_manifest(uploads) != uf or file_manifest(sources) != sf:
            raise DRError("private documents changed during backup")
        checks = {}
        for name in PARTS:
            sha = sha256()
            with (destination / name).open("rb") as stream:
                while chunk := stream.read(1024 * 1024):
                    sha.update(chunk)
            checks[name] = sha.hexdigest()
        encrypt_manifest({
            "format": "lhfm-dr-v1", "database": database,
            "tables": before, "files": {"uploads": uf, "sources": sf},
            "ciphertext_sha256": checks,
        }, recipient=recipient, target=destination / "manifest.json.age")
        sign_manifest(destination / "manifest.json.age", signing_key,
                      destination / "manifest.sig")
        return {"encrypted_backup_created": True, "tables": len(before),
                "upload_files": len(uf), "source_files": len(sf)}
    except Exception:
        shutil.rmtree(destination)
        raise


def decrypt_manifest(file, identity):
    process = subprocess.Popen(["age", "-d", "-i", str(identity), str(file)],
                               stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    try:
        assert process.stdout is not None
        body = process.stdout.read(MAX_MANIFEST + 1)
        if len(body) > MAX_MANIFEST or process.wait(timeout=60):
            raise DRError("manifest decrypt/authentication failed")
        try:
            doc = json.loads(body.decode("utf-8"))
        except (UnicodeDecodeError, ValueError) as exc:
            raise DRError("invalid encrypted manifest") from exc
        if (not isinstance(doc, dict) or doc.get("format") != "lhfm-dr-v1"
                or set(doc.get("ciphertext_sha256", {})) != set(PARTS)
                or set(doc.get("files", {})) != {"uploads", "sources"}
                or not isinstance(doc.get("tables"), dict)):
            raise DRError("incomplete or unsupported manifest")
        return doc
    finally:
        if process.poll() is None:
            process.kill()
            process.wait()
        if process.stdout:
            process.stdout.close()


def archive_path(name):
    if not isinstance(name, str) or name.startswith("/") or chr(92) in name:
        raise DRError("unsafe member path")
    parts = PurePosixPath(name).parts
    if len(parts) < 2 or parts[0] != "data" or any(p == ".." for p in parts):
        raise DRError("unsafe member path")
    return PurePosixPath(*parts[1:]).as_posix()


def verify_tar(file, identity, expected, destination):
    process = subprocess.Popen(["age", "-d", "-i", str(identity), str(file)],
                               stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    seen = set()
    total = 0
    try:
        assert process.stdout is not None
        with tarfile.open(fileobj=process.stdout, mode="r|") as tar:
            for item in tar:
                if not item.isfile() or item.size > MAX_FILE:
                    raise DRError("untrusted archive entry type/size")
                relative = archive_path(item.name)
                if relative in seen or relative not in expected:
                    raise DRError("unknown or duplicate file in encrypted backup")
                seen.add(relative)
                destination_file = destination / relative
                destination_file.parent.mkdir(parents=True,mode=0o700,exist_ok=True)
                digest = sha256()
                size = 0
                stream = tar.extractfile(item)
                if stream is None:
                    raise DRError("missing archive file bytes")
                with stream, output(destination_file) as out:
                    while data := stream.read(1024 * 1024):
                        size += len(data)
                        total += len(data)
                        if size > MAX_FILE or total > MAX_TOTAL:
                            raise DRError("archive exceeds restore limit")
                        digest.update(data)
                        out.write(data)
                if (size != expected[relative]["size"]
                        or digest.hexdigest() != expected[relative]["sha256"]):
                    raise DRError("restored private file hash differs")
        if process.wait(timeout=180) or seen != set(expected):
            raise DRError("archive incomplete or authentication failed")
        return len(seen)
    finally:
        if process.poll() is None:
            process.kill()
            process.wait()
        if process.stdout:
            process.stdout.close()


def verify_restore(*, defaults_file, backup_dir, identity, target_database, verification_key,
                   restore_upload_root=None, restore_source_root=None):
    if os.environ.get("LHFM_RESTORE_REHEARSAL_APPROVED") != "YES":
        raise DRError("explicit isolated restore approval required")
    if not NAME.fullmatch(target_database) or not target_database.startswith("lhfm_restore_"):
        raise DRError("restore may ONLY target lhfm_restore_*")
    if not shutil.which("age") or not shutil.which("mariadb"):
        raise DRError("age and MariaDB client required")
    credentials = client_config(defaults_file)
    identity = private_file(identity)
    root = private_dir(backup_dir)
    verify_signature(root / "manifest.json.age", root / "manifest.sig", verification_key)
    manifest = decrypt_manifest(root / "manifest.json.age", identity)
    if target_database == manifest["database"]:
        raise DRError("cannot overwrite original database")
    for name, expected in manifest["ciphertext_sha256"].items():
        digest = sha256()
        path = private_file(root / name)
        with path.open("rb") as stream:
            while data := stream.read(1024 * 1024):
                digest.update(data)
        if digest.hexdigest() != expected:
            raise DRError("ciphertext tampered or snapshot incomplete")
    if (restore_upload_root is None) != (restore_source_root is None):
        raise DRError("both isolated private restore roots must be provided together")
    target_uploads = target_sources = None
    if restore_upload_root is not None:
        target_uploads = private_dir(restore_upload_root)
        target_sources = private_dir(restore_source_root)
        source_root = root.resolve(strict=True)
        upload_dest = target_uploads.resolve(strict=True)
        audit_dest = target_sources.resolve(strict=True)
        if (upload_dest == audit_dest
                or upload_dest.is_relative_to(source_root)
                or audit_dest.is_relative_to(source_root)
                or source_root.is_relative_to(upload_dest)
                or source_root.is_relative_to(audit_dest)
                or any(any(folder.iterdir()) for folder in (target_uploads,target_sources))):
            raise DRError("isolated restore directories must be empty and distinct")
    table_counts(credentials, target_database, must_be_empty=True)
    child = subprocess.Popen(
        ["age", "-d", "-i", str(identity), str(root / PARTS[0])],
        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    try:
        assert child.stdout is not None
        maria = subprocess.Popen(
            ["mariadb", "--defaults-extra-file=" + str(defaults_file),
             "--database=" + target_database],
            stdin=child.stdout, stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL)
        child.stdout.close()
        try:
            rc_maria = maria.wait(timeout=900)
            rc_age = child.wait(timeout=900)
        except subprocess.TimeoutExpired as exc:
            maria.kill()
            child.kill()
            maria.wait()
            child.wait()
            raise DRError("database restore timed out") from exc
        if rc_maria or rc_age:
            raise DRError("isolated database restore failed")
    finally:
        if child.poll() is None:
            child.kill()
            child.wait()
    if table_counts(credentials, target_database) != manifest["tables"]:
        raise DRError("restored database row counts differ from source snapshot")
    with ExitStack() as stack:
        if restore_upload_root is None:
            temporary = stack.enter_context(
                tempfile.TemporaryDirectory(prefix="lhfm-dr-verify-")
            )
            base = Path(temporary)
            target_uploads, target_sources = base / "uploads", base / "sources"
            target_uploads.mkdir(mode=0o700)
            target_sources.mkdir(mode=0o700)
        for name, component, target in (
            ("uploads",PARTS[1],target_uploads),
            ("sources",PARTS[2],target_sources),
        ):
            verify_tar(root / component, identity,manifest["files"][name],target)
    return {"restore_verified": True, "table_counts_match": True,
            "target_database": target_database,
            "upload_files_checked": len(manifest["files"]["uploads"]),
            "audit_source_files_checked": len(manifest["files"]["sources"]),
            "invoice_created": False}


def main():
    parser = argparse.ArgumentParser(description="Encrypted LHFM DR maintenance only")
    actions = parser.add_subparsers(dest="action", required=True)
    a = actions.add_parser("backup")
    for field in ("defaults-file","database","upload-root","source-root",
                  "destination","age-recipient","signing-key"):
        a.add_argument("--"+field, required=True)
    b = actions.add_parser("restore-verify")
    for field in ("defaults-file","backup-dir","age-identity","target-database","verification-key"):
        b.add_argument("--"+field, required=True)
    for field in ("restore-upload-root","restore-source-root"):
        b.add_argument("--"+field)
    options = parser.parse_args()
    try:
        if options.action == "backup":
            result = create_backup(
                defaults_file=options.defaults_file,database=options.database,
                upload_root=options.upload_root,source_root=options.source_root,
                destination=options.destination,recipient=options.age_recipient,
                signing_key=options.signing_key)
        else:
            result = verify_restore(
                defaults_file=options.defaults_file,
                backup_dir=options.backup_dir,identity=options.age_identity,
                target_database=options.target_database,
                verification_key=options.verification_key,
                restore_upload_root=options.restore_upload_root,
                restore_source_root=options.restore_source_root)
        print(json.dumps(result,sort_keys=True))
        return 0
    except Exception as exc:
        print("DR_BLOCKED: " + str(exc),file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
