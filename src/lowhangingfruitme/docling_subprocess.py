"""Fail-closed, bounded, OS-sandboxed local contract-PDF extraction.

Never run untrusted PDFs in the API process. A root-owned operator launcher must
place the worker in an independent, loopback-only network namespace. The worker
independently checks this property. Neither check validates a legal contract.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import re
import selectors
import signal
import stat
import subprocess
import sys
from time import monotonic
from typing import Any

MAX_STDOUT_BYTES = 1024 * 1024


def _trusted_launcher(raw: str | None) -> Path:
    if not raw or not os.path.isabs(raw):
        raise RuntimeError("absolute trusted document sandbox launcher required")
    path = Path(raw)
    # Check each parent to prevent a root-owned file in a user-writable tree
    # being swapped out between permission validation and launch.
    try:
        for part in (path, *path.parents):
            metadata = part.lstat()
            if (stat.S_ISLNK(metadata.st_mode) or metadata.st_uid != 0
                    or metadata.st_mode & 0o022):
                raise RuntimeError("document sandbox launcher path is not root-controlled")
        metadata = path.stat()
    except OSError as exc:
        raise RuntimeError("document sandbox launcher does not exist or is unreadable") from exc
    if not stat.S_ISREG(metadata.st_mode) or not (metadata.st_mode & 0o111):
        raise RuntimeError("document sandbox launcher must be an executable regular file")
    return path


def _parent_netns() -> str:
    if sys.platform != "linux":
        raise RuntimeError("document sandbox requires Linux network namespaces")
    try:
        value = os.readlink("/proc/self/ns/net")
    except OSError as exc:
        raise RuntimeError("parent network namespace unavailable") from exc
    if not re.fullmatch(r"net:\[\d+\]", value):
        raise RuntimeError("invalid parent network namespace identifier")
    return value


class DoclingSubprocessExtractor:
    """Isolate process and network access; reject absent/unverified launcher."""

    def __init__(
        self, *, launcher: str | None = None,
        timeout_seconds: float = 120.0,
        max_stdout_bytes: int = MAX_STDOUT_BYTES,
    ) -> None:
        self.launcher = launcher
        if not (0 < timeout_seconds <= 120.0 and
                0 < max_stdout_bytes <= MAX_STDOUT_BYTES):
            raise ValueError("document worker resource budget out of bounds")
        self.timeout_seconds = timeout_seconds
        self.max_stdout_bytes = max_stdout_bytes

    def _command(self, argument: str) -> list[str]:
        return [str(_trusted_launcher(self.launcher)), sys.executable, "-I",
                "-m", "lowhangingfruitme.documents_worker", argument]

    def _execute(self, argument: str) -> dict[str, Any]:
        _trusted_launcher(self.launcher)  # no local fallback, even in preflight
        parent_ns = _parent_netns()
        env = {
            "PATH": "/usr/bin:/bin",
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONNOUSERSITE": "1",
            "HOME": os.environ.get("LHFM_DOCLING_CACHE_HOME", "/nonexistent"),
            "LHFM_PARENT_NETNS": parent_ns,
        }
        if os.environ.get("LHFM_DOCLING_CACHE_HOME"):
            env["HF_HOME"] = os.environ["LHFM_DOCLING_CACHE_HOME"]
        command = self._command(argument)
        try:
            process = subprocess.Popen(
                command, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL, env=env, close_fds=True,
                start_new_session=True,
            )
        except OSError as exc:
            raise RuntimeError("document sandbox launcher unavailable") from exc
        chunks: list[bytes] = []
        size = 0
        deadline = monotonic() + self.timeout_seconds
        try:
            if process.stdout is None:
                raise RuntimeError("document worker stdout unavailable")
            with selectors.DefaultSelector() as watcher:
                watcher.register(process.stdout, selectors.EVENT_READ)
                while watcher.get_map():
                    remaining = deadline - monotonic()
                    if remaining <= 0:
                        raise RuntimeError("document worker deadline exceeded")
                    ready = watcher.select(remaining)
                    if not ready:
                        raise RuntimeError("document worker deadline exceeded")
                    for key, _ in ready:
                        data = os.read(key.fd, 64 * 1024)
                        if not data:
                            watcher.unregister(key.fileobj)
                            continue
                        size += len(data)
                        if size > self.max_stdout_bytes:
                            raise RuntimeError("document worker output limit exceeded")
                        chunks.append(data)
            remaining = deadline - monotonic()
            if remaining <= 0:
                raise RuntimeError("document worker deadline exceeded")
            if process.wait(timeout=remaining) != 0:
                raise RuntimeError("document worker rejected the document or sandbox")
            try:
                result = json.loads(b"".join(chunks).decode("utf-8"))
            except (UnicodeDecodeError, ValueError) as exc:
                raise RuntimeError("invalid document worker response") from exc
            if not isinstance(result, dict):
                raise RuntimeError("invalid document worker response structure")
            return result
        except subprocess.TimeoutExpired as exc:
            raise RuntimeError("document worker deadline exceeded") from exc
        finally:
            if process.poll() is None:
                # Kill descendants in the same session; do not leave a timed-out
                # PDF parser consuming resources after the HTTP request ends.
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                process.wait()
            if process.stdout is not None:
                process.stdout.close()

    def preflight(self) -> None:
        """Actually launch the sandbox and verify independent network isolation."""
        result = self._execute("--preflight")
        if result != {"sandbox": "NETWORK_ISOLATED"}:
            raise RuntimeError("document worker sandbox attestation failed")

    def __call__(self, path: Path) -> dict[str, Any]:
        # A real parse is also re-attested by the worker; health can be stale.
        return self._execute(str(path))



def main() -> int:
    """Operator check: sandbox networking only, not real PDF/OCR acceptance."""
    try:
        DoclingSubprocessExtractor(
            launcher=os.environ.get("LHFM_DOCLING_SANDBOX_LAUNCHER"),
        ).preflight()
    except Exception:
        print("DOCUMENT_SANDBOX_NOT_READY", file=sys.stderr)
        return 2
    print("DOCUMENT_SANDBOX_NETWORK_ISOLATED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
