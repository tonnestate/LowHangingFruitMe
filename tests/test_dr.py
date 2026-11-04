"""DR safety boundaries; real age/MariaDB integration runs in CI separately."""
from __future__ import annotations

import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from lowhangingfruitme.dr import (
    DRError, archive_path, client_config, create_backup, file_manifest,
    private_dir, private_file, require_key_outside, verify_restore,
)


class DisasterRecoverySafetyTests(unittest.TestCase):
    def test_archive_rejects_outside_paths(self):
        for path in ("/etc/passwd","data/../etc/passwd",
                     "data", "uploads/x", "data/..", "data\\evil",
                     "data/../../secrets"):
            with self.subTest(path=path), self.assertRaises(DRError):
                archive_path(path)
        self.assertEqual(archive_path("data/case/receipt.pdf"),"case/receipt.pdf")

    def test_private_roots_reject_world_access_and_symlinks(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            folder = root / "private"
            folder.mkdir(mode=0o700)
            self.assertEqual(private_dir(folder),folder)
            folder.chmod(0o755)
            with self.assertRaises(DRError):
                private_dir(folder)
            folder.chmod(0o700)
            link = root / "link"
            link.symlink_to(folder)
            with self.assertRaises(DRError):
                private_dir(link)
            secret = root / "config"
            secret.write_text("[client]\nhost=127.0.0.1\n",encoding="utf-8")
            secret.chmod(0o600)
            self.assertEqual(private_file(secret),secret)
            secret.chmod(0o644)
            with self.assertRaises(DRError):
                private_file(secret)

    def test_snapshot_rejects_hardlinks_symlinks_and_permission_leaks(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "private"
            root.mkdir(mode=0o700)
            source = root / "contract.pdf"
            source.write_bytes(b"synthetic-private-contract")
            source.chmod(0o600)
            expected = file_manifest(root)
            self.assertEqual(expected["contract.pdf"]["size"],26)
            self.assertEqual(len(expected["contract.pdf"]["sha256"]),64)
            leak = root / "hardlink"
            os.link(source,leak)
            with self.assertRaisesRegex(DRError,"unsafe"):
                file_manifest(root)
            leak.unlink()
            source.chmod(0o644)
            with self.assertRaisesRegex(DRError,"unsafe"):
                file_manifest(root)
            source.chmod(0o600)
            (root / "linked").symlink_to(source)
            with self.assertRaisesRegex(DRError,"unsafe"):
                file_manifest(root)

    def test_operator_signing_authority_cannot_be_part_of_backup(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "private"
            root.mkdir(mode=0o700)
            embedded = root / "signing.pem"
            embedded.write_bytes(b"synthetic-not-a-real-key")
            embedded.chmod(0o600)
            external = Path(directory) / "external-key.pem"
            external.write_bytes(b"synthetic-public-only")
            external.chmod(0o600)
            with self.assertRaisesRegex(DRError, "outside backup"):
                require_key_outside(embedded, root)
            require_key_outside(external, root)

    def test_wrong_operator_confirmations_prevent_data_access(self):
        with patch.dict(os.environ,{},clear=True):
            with self.assertRaisesRegex(DRError,"maintenance"):
                create_backup(defaults_file="/missing",database="lhfm_test",
                              upload_root="/missing",source_root="/missing",
                              destination="/missing/backup",recipient="age1unused123456",
                              signing_key="/missing")
            with self.assertRaisesRegex(DRError,"approval"):
                verify_restore(defaults_file="/missing",backup_dir="/missing",
                               identity="/missing",target_database="lhfm_restore_test",
                               verification_key="/missing")

    def test_restore_never_accepts_original_or_arbitrary_database(self):
        with patch.dict(os.environ,{"LHFM_RESTORE_REHEARSAL_APPROVED":"YES"}):
            for database in ("lhfm_test","mysql","production","lhfm_restore_foo;DROP"):
                with self.subTest(database=database),self.assertRaisesRegex(DRError,"ONLY"):
                    verify_restore(defaults_file="/missing",backup_dir="/missing",
                                   identity="/missing",target_database=database,
                                   verification_key="/missing")

    def test_defaults_file_must_be_private_and_loopback(self):
        with tempfile.TemporaryDirectory() as directory:
            file = Path(directory) / "db.cnf"
            file.write_text("[client]\nhost=db.public.example\nuser=u\npassword=p\n",
                            encoding="utf-8")
            file.chmod(0o600)
            with self.assertRaisesRegex(DRError,"loopback"):
                client_config(file)
            file.write_text("[client]\nhost=127.0.0.1\nuser=u\npassword=p\n",
                            encoding="utf-8")
            self.assertEqual(client_config(file)["host"],"127.0.0.1")


if __name__ == "__main__":
    unittest.main()
