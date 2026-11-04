"""Runtime sandbox and pipe-bound tests; no customer files or Docling downloads."""
from __future__ import annotations

import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

from lowhangingfruitme.docling_subprocess import (
    DoclingSubprocessExtractor, _parent_netns, _trusted_launcher,
)
from lowhangingfruitme.documents_worker import require_isolated_network


class LocalSandboxRunner(DoclingSubprocessExtractor):
    """Synthetic only: replace worker with a tiny CLI for pipe/timeout tests."""

    def __init__(self, program: str, **kwargs):
        super().__init__(launcher="/usr/bin/env", **kwargs)
        self.program = program

    def _command(self, argument: str) -> list[str]:
        return [sys.executable, "-c", self.program]


@unittest.skipUnless(sys.platform == "linux", "Linux worker required")
class DocumentWorkerHardeningTests(unittest.TestCase):
    def test_no_launcher_fails_closed(self):
        with self.assertRaisesRegex(RuntimeError, "launcher required"):
            DoclingSubprocessExtractor() (Path("/tmp/test.pdf"))
        with self.assertRaisesRegex(RuntimeError, "launcher required"):
            DoclingSubprocessExtractor().preflight()

    def test_attestation_rejects_unisolated_network(self):
        current = _parent_netns()
        with patch.dict(os.environ, {"LHFM_PARENT_NETNS": current}):
            with self.assertRaisesRegex(RuntimeError, "shares the API"):
                require_isolated_network()

    def test_attestation_rejects_untrusted_namespace(self):
        with patch.dict(os.environ, {"LHFM_PARENT_NETNS": "net:[1234]"}):
            with patch("os.readlink", return_value="net:[1235]"):
                with patch("os.listdir", return_value=["lo", "eth0"]):
                    with self.assertRaisesRegex(RuntimeError, "unexpected network"):
                        require_isolated_network()

    def test_successful_worker_json_capture(self):
        result = LocalSandboxRunner(
            'import sys;sys.stdout.write(\'{"ok":true}\')'
        )(Path("/irrelevant"))
        self.assertEqual(result, {"ok": True})

    def test_stdout_flood_is_bounded_and_process_killed(self):
        with self.assertRaisesRegex(RuntimeError, "output limit exceeded"):
            LocalSandboxRunner(
                'import sys;sys.stdout.write("A"*100000);sys.stdout.flush()',
                max_stdout_bytes=512,
            )(Path("/irrelevant"))

    def test_hanging_worker_is_terminated(self):
        with self.assertRaisesRegex(RuntimeError, "deadline exceeded"):
            LocalSandboxRunner(
                'import time;time.sleep(3)',
                timeout_seconds=0.1,
            )(Path("/irrelevant"))

    def test_invalid_json_rejected(self):
        with self.assertRaisesRegex(RuntimeError, "invalid document worker response"):
            LocalSandboxRunner(
                'import sys;sys.stdout.write("not json")',
            )(Path("/irrelevant"))

    def test_fake_sandbox_preflight_rejected(self):
        with self.assertRaisesRegex(RuntimeError, "attestation failed"):
            LocalSandboxRunner(
                'import sys;sys.stdout.write(\'{"sandbox":"UNVERIFIED"}\')',
            ).preflight()

    def test_untrusted_paths_and_symlink_are_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            program = root / "unsafe"
            program.write_text("#!/bin/sh\nexit 0\n")
            program.chmod(0o777)
            with self.assertRaises(RuntimeError):
                _trusted_launcher(str(program))
            linked = root / "linked"
            linked.symlink_to("/usr/bin/env")
            with self.assertRaises(RuntimeError):
                _trusted_launcher(str(linked))


if __name__ == "__main__":
    unittest.main()
