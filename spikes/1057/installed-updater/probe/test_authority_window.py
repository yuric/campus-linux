"""Local receipt/staging regressions; no root, polkit or desktop execution."""
import hashlib
import importlib.util
from pathlib import Path
import stat
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch


spec = importlib.util.spec_from_file_location("authority_window", Path(__file__).with_name("authority-window.py"))
authority = importlib.util.module_from_spec(spec)
spec.loader.exec_module(authority)


class AuthorityReceiptTests(unittest.TestCase):
    def source_path(self):
        path = Mock()
        path.is_absolute.return_value = True
        path.resolve.return_value = path
        path.parent.stat.return_value = SimpleNamespace(st_mode=stat.S_IFDIR | 0o500)
        path.stat.return_value = SimpleNamespace(st_mode=stat.S_IFREG | 0o400, st_uid=0)
        path.read_bytes.return_value = b"reviewed helper bytes\n"
        return path

    def test_staged_helper_requires_reviewed_hash_and_locked_root_bytes(self):
        expected = hashlib.sha256(b"reviewed helper bytes\n").hexdigest()
        with patch.object(authority, "safe_root_parent") as parent_check:
            path = self.source_path()
            self.assertEqual(authority.staged_source(path, expected)["sha256"], expected)
            parent_check.assert_called_once_with(path.parent, private=True)
            for mutation in ("wrong_hash", "writable_directory", "writable_file", "nonroot_file", "symlink"):
                with self.subTest(mutation=mutation):
                    path = self.source_path()
                    if mutation == "wrong_hash":
                        path.read_bytes.return_value = b"changed helper"
                    elif mutation == "writable_directory":
                        path.parent.stat.return_value.st_mode |= 0o200
                    elif mutation == "writable_file":
                        path.stat.return_value.st_mode |= 0o200
                    elif mutation == "nonroot_file":
                        path.stat.return_value.st_uid = 1000
                    else:
                        path.resolve.return_value = Path("/different-source")
                    with self.assertRaises(RuntimeError):
                        authority.staged_source(path, expected)

    def test_restoration_timestamp_precedes_removal_even_when_receipt_io_fails(self):
        for failing_write in (False, True):
            with self.subTest(failing_write=failing_write), tempfile.TemporaryDirectory() as directory:
                rule = Path(directory) / "owned.rules"
                rule.write_bytes(b"exact owned rule")
                info = rule.stat()
                window = authority.Window.__new__(authority.Window)
                window.args = SimpleNamespace(mode="deny")
                window.owned = (info.st_dev, info.st_ino)
                window.rule_bytes = rule.read_bytes()
                window.record = {"ready_unix_ns": 100}
                saved = []

                def save():
                    saved.append((dict(window.record), rule.exists()))
                    if failing_write and len(saved) == 1:
                        raise OSError("receipt unavailable")

                window.save = save
                with patch.object(authority, "RULE", rule), patch.object(authority.time, "time_ns", return_value=200):
                    window.restore()
                self.assertEqual(saved[0][0]["restore_started_unix_ns"], 200)
                self.assertTrue(saved[0][1])
                self.assertFalse(rule.exists())
                self.assertEqual(window.record["cleanup"], "restored")
                if failing_write:
                    self.assertEqual(window.record["restore_start_persist_error"], "OSError")


if __name__ == "__main__":
    unittest.main()
