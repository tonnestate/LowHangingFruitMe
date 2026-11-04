"""Production startup preflight: reject unsafe config before serving finance."""
from __future__ import annotations

from contextlib import redirect_stderr
from io import StringIO
import os
from pathlib import Path
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from lowhangingfruitme.runtime import (
    RuntimeNotReady, main, validate_runtime_config, verify_runtime,
)


class RuntimeConfigTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="lhfm-runtime-ci-")
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.source = self.base / "source"
        self.upload = self.base / "uploads"
        self.source.mkdir(mode=0o700)
        self.upload.mkdir(mode=0o700)
        self.env = {
            "LHFM_DB_HOST": "127.0.0.1", "LHFM_DB_PORT": "3306",
            "LHFM_DB_USER": "synthetic", "LHFM_DB_PASSWORD": "not-a-real-secret",
            "LHFM_DB_NAME": "lhfm_test",
            "LHFM_API_SOURCE_ROOT": str(self.source),
            "LHFM_UPLOAD_ROOT": str(self.upload),
            "LHFM_CLAMD_UNIX_SOCKET": "/run/clamav/clamd.ctl",
            "LHFM_DOCLING_SANDBOX_LAUNCHER": "/usr/local/libexec/lhfm/docling",
            "LHFM_OIDC_ISSUER": "https://identity.example/realms/finance",
            "LHFM_OIDC_AUDIENCE": "synthetic-api",
            "LHFM_OIDC_JWKS_FILE": "/etc/lhfm/oidc-public.jwks",
            "LHFM_OIDC_ALLOWED_CLIENT_IDS": "synthetic-client",
            "LHFM_APPROVAL_KEY_HEX": "0" * 64,
        }
        self.uid = os.geteuid()

    @unittest.skipIf(os.geteuid() == 0, "CI positive preflight requires an unprivileged user")
    def test_private_staging_and_loopback_configuration_pass(self):
        source, upload, socket, launcher = validate_runtime_config(
            self.env, uid=self.uid,
        )
        self.assertEqual((source, upload), (self.source, self.upload))
        self.assertEqual(socket, "/run/clamav/clamd.ctl")
        self.assertEqual(launcher, "/usr/local/libexec/lhfm/docling")

    def test_root_worker_is_never_allowed(self):
        with self.assertRaisesRegex(RuntimeNotReady, "REFUSE_ROOT"):
            validate_runtime_config(self.env, uid=0)

    @unittest.skipIf(os.geteuid() == 0, "CI positive preflight requires an unprivileged user")
    def test_rejects_external_database_and_restore_namespace(self):
        for name, value in [
            ("LHFM_DB_HOST", "db.example.org"),
            ("LHFM_DB_HOST", "localhost"),
            ("LHFM_DB_PORT", "0"),
            ("LHFM_DB_PORT", "injection"),
            ("LHFM_DB_NAME", "lhfm_restore_drill"),
            ("LHFM_DB_PASSWORD", ""),
        ]:
            with self.subTest(name=name, value=value):
                env = {**self.env, name: value}
                with self.assertRaises(RuntimeNotReady):
                    validate_runtime_config(env, uid=self.uid)

    @unittest.skipIf(os.geteuid() == 0, "CI positive preflight requires an unprivileged user")
    def test_rejects_bad_storage_modes_and_symlink_roots(self):
        self.source.chmod(0o755)
        with self.assertRaisesRegex(RuntimeNotReady, "OWNER_OR_MODE"):
            validate_runtime_config(self.env, uid=self.uid)
        self.source.chmod(0o700)
        link = self.base / "linked"
        link.symlink_to(self.source)
        with self.assertRaisesRegex(RuntimeNotReady, "SYMLINK"):
            validate_runtime_config(
                {**self.env, "LHFM_API_SOURCE_ROOT": str(link)}, uid=self.uid,
            )

    @unittest.skipIf(os.geteuid() == 0, "CI positive preflight requires an unprivileged user")
    def test_rejects_overlapping_roots_and_missing_sandbox(self):
        for env in [
            {**self.env, "LHFM_UPLOAD_ROOT": str(self.source)},
            {**self.env, "LHFM_DOCLING_SANDBOX_LAUNCHER": "relative/docling"},
            {**self.env, "LHFM_CLAMD_UNIX_SOCKET": ""},
            {**self.env, "LHFM_OIDC_JWKS_FILE": "relative.jwks"},
            {**self.env, "LHFM_OIDC_ALLOWED_CLIENT_IDS": ""},
        ]:
            with self.subTest(env=env), self.assertRaises(RuntimeNotReady):
                validate_runtime_config(env, uid=self.uid)

    @unittest.skipIf(os.geteuid() == 0, "CI positive preflight requires an unprivileged user")
    def test_rejects_parent_child_storage_trees(self):
        nested = self.source / "subdir"
        nested.mkdir(mode=0o700)
        with self.assertRaisesRegex(RuntimeNotReady, "OVERLAP"):
            validate_runtime_config(
                {**self.env, "LHFM_UPLOAD_ROOT": str(nested)},
                uid=self.uid,
            )

    @unittest.skipIf(os.geteuid() == 0, "CI uses synthetic live dependencies")
    def test_read_only_checks_run_in_order_and_return_no_secrets(self):
        events = []
        fake_service = SimpleNamespace(
            registry=SimpleNamespace(_connect=lambda: None),
        )

        def schema(connect):
            self.assertIs(connect, fake_service.registry._connect)
            events.append("schema")

        def scanner(path):
            self.assertEqual(path, self.env["LHFM_CLAMD_UNIX_SOCKET"])
            return SimpleNamespace(ping=lambda: events.append("scanner"))

        def extractor(path):
            self.assertEqual(path, self.env["LHFM_DOCLING_SANDBOX_LAUNCHER"])
            return SimpleNamespace(preflight=lambda: events.append("sandbox"))

        with patch("lowhangingfruitme.runtime.require_operational_schema", schema):
            result = verify_runtime(
                env=self.env, uid=self.uid, service_factory=lambda: fake_service,
                scanner_factory=scanner, extractor_factory=extractor,
            )
        self.assertEqual(events, ["schema", "scanner", "sandbox"])
        self.assertEqual(result["schema"], "compatible")
        self.assertNotIn(self.env["LHFM_DB_PASSWORD"], str(result))

    def test_operator_error_does_not_leak_paths_or_credentials(self):
        captured = StringIO()
        with patch("lowhangingfruitme.runtime.verify_runtime",
                   side_effect=RuntimeError("PRIVATE /a/b/SECRET")):
            with redirect_stderr(captured):
                self.assertEqual(main(), 2)
        self.assertEqual(captured.getvalue().strip(), "LHFM_RUNTIME_NOT_READY")

    def test_real_api_factory_refuses_startup_when_runtime_gate_fails(self):
        from lowhangingfruitme.api.http import create_app_from_environment
        fake_service = SimpleNamespace(
            registry=SimpleNamespace(_connect=lambda: None),
        )
        with patch.dict(os.environ, {"LHFM_API_SOURCE_ROOT": "/not-used"}, clear=True):
            with patch(
                "lowhangingfruitme.api.http.AuthenticatedApprovalService.from_environment",
                return_value=fake_service,
            ):
                with patch(
                    "lowhangingfruitme.runtime.verify_runtime",
                    side_effect=RuntimeNotReady("CLAMAV_NOT_RESPONDING"),
                ) as preflight:
                    with self.assertRaisesRegex(RuntimeNotReady, "CLAMAV"):
                        create_app_from_environment()
                    preflight.assert_called_once()

    def test_python_server_supports_required_safe_proxy_flags(self):
        import subprocess
        import sys
        status = subprocess.run(
            [sys.executable, "-m", "uvicorn", "--help"],
            capture_output=True, text=True, timeout=15,
        )
        self.assertEqual(status.returncode, 0, status.stderr)
        for flag in ("--factory", "--no-proxy-headers", "--no-access-log"):
            self.assertIn(flag, status.stdout)

    def test_checked_systemd_boundary_does_not_expose_financial_api(self):
        path = Path(__file__).resolve().parents[1] / "deploy"
        api = (path / "lowhangingfruitme-api.service.example").read_text()
        portal = (path / "lowhangingfruitme-portal.service.example").read_text()
        self.assertIn("User=lhfm-api", api)
        self.assertIn("ExecStartPre=/srv/lowhangingfruitme/python/bin/lhfm-runtime-check", api)
        self.assertIn("--host 127.0.0.1 --port 8127 --workers 1", api)
        self.assertIn("--no-proxy-headers", api)
        self.assertIn("NoNewPrivileges=true", api)
        self.assertIn("EnvironmentFile=/etc/lowhangingfruitme/api.env", api)
        self.assertIn("EnvironmentFile=/etc/lowhangingfruitme/portal.env", portal)
        self.assertIn("User=lowhangingfruitme", portal)
        self.assertNotIn("User=lhfm-api", portal)
        self.assertIn("HOSTNAME=127.0.0.1", portal)
        self.assertIn("PUBLIC_LAUNCH_APPROVED=false", portal)


if __name__ == "__main__":
    unittest.main()
