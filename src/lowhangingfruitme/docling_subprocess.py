"""Bounded subprocess adapter for optional local Docling; no network sandbox claim."""
from __future__ import annotations
import json
import os
import resource
import subprocess
import sys
from pathlib import Path
from typing import Any


def _limits() -> None:
    resource.setrlimit(resource.RLIMIT_AS, (4 * 1024**3, 4 * 1024**3))
    resource.setrlimit(resource.RLIMIT_CPU, (90, 90))
    resource.setrlimit(resource.RLIMIT_FSIZE, (2 * 1024**2, 2 * 1024**2))


class DoclingSubprocessExtractor:
    """Requires OS-level egress restrictions and installed local model assets."""

    def __call__(self, path: Path) -> dict[str, Any]:
        env = {"PATH": "/usr/bin:/bin", "PYTHONNOUSERSITE": "1",
               "HOME": os.environ.get("LHFM_DOCLING_CACHE_HOME", "/nonexistent")}
        if os.environ.get("LHFM_DOCLING_CACHE_HOME"):
            env["HF_HOME"] = os.environ["LHFM_DOCLING_CACHE_HOME"]
        try:
            completed = subprocess.run(
                [sys.executable, "-I", "-m", "lowhangingfruitme.documents_worker",
                 str(path)],
                stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL, env=env, check=False,
                timeout=120, preexec_fn=_limits, close_fds=True,
                start_new_session=True,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise RuntimeError("document conversion worker unavailable") from exc
        if completed.returncode != 0 or len(completed.stdout) > 1024 * 1024:
            raise RuntimeError("document conversion worker failed or exceeded output bound")
        try:
            return json.loads(completed.stdout.decode("utf-8"))
        except (ValueError,UnicodeDecodeError) as exc:
            raise RuntimeError("invalid document conversion worker output") from exc
