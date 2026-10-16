"""Integration-boundary negatives only; synthetic archives are never installed evidence."""
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import tarfile
import tempfile
import unittest

spec = importlib.util.spec_from_file_location("adapter", Path(__file__).with_name("install-deb.py"))
adapter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(adapter)


def archive(entries):
    output = io.BytesIO()
    with tarfile.open(fileobj=output, mode="w:gz", format=tarfile.USTAR_FORMAT) as tar:
        for name, content, mode, kind in entries:
            member = tarfile.TarInfo(name)
            member.mode = mode
            member.type = kind
            member.size = len(content) if kind == tarfile.REGTYPE else 0
            tar.addfile(member, io.BytesIO(content) if member.isfile() else None)
    return output.getvalue()


def deb(version="1.0.0", extra=None):
    control = archive([("control", f"Package: campus-updater-1057\nVersion: {version}\nArchitecture: arm64\n".encode(), 0o644, tarfile.REGTYPE)])
    entries = [("usr/bin/campus-updater-1057", ("app" + version).encode(), 0o755, tarfile.REGTYPE),
               ("usr/lib/campus-updater-1057/inert-helper.txt", b"helper", 0o644, tarfile.REGTYPE)]
    if extra:
        entries.append(extra)
    members = [("debian-binary", b"2.0\n"), ("control.tar.gz", control), ("data.tar.gz", archive(entries))]
    result = b"!<arch>\n"
    for name, content in members:
        header = f"{name + '/':<16}{0:<12}{0:<6}{0:<6}{'100644':<8}{len(content):<10}`\n".encode()
        result += header + content + (b"\n" if len(content) % 2 else b"")
    return result


class AdapterTests(unittest.TestCase):
    def test_measured_admission_binds_three_exact_real_package_slots(self):
        records = [adapter.package_record(deb(version)) for version in sorted(adapter.VERSIONS)]
        value = {"schema": 1, "package": adapter.PACKAGE, "architecture": "arm64", "packages": records,
                 "max_package_bytes": max(item["size"] for item in records),
                 "max_expanded_data_bytes": max(item["expanded_data_bytes"] for item in records)}
        self.assertEqual(adapter.validate_admission(value), value)
        value["max_package_bytes"] += 1
        with self.assertRaisesRegex(adapter.Refused, "measured_package_bound"):
            adapter.validate_admission(value)

    def test_unreviewed_payload_path_cannot_replace_trust(self):
        for name in ("etc/campus-updater-1057/public-key.txt", "usr/lib/campus-updater-1057/verify-signature",
                     "usr/lib/campus-updater-1057/install-deb.py", "etc/cron.d/fixture"):
            with self.subTest(name=name), self.assertRaisesRegex(adapter.Refused, "unreviewed_fixture_data_path"):
                adapter.package_record(deb(extra=(name, b"replacement", 0o644, tarfile.REGTYPE)))

    def test_archive_symlink_rejected(self):
        with self.assertRaisesRegex(adapter.Refused, "special_file_or_link"):
            adapter.package_record(deb(extra=("usr/share/applications/campus-updater-1057.desktop", b"", 0o777, tarfile.SYMTYPE)))

    def test_source_symlink_and_oversize_rejected_before_staging(self):
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "source"
            source.write_bytes(b"12345")
            link = Path(temporary) / "link"
            link.symlink_to(source)
            with self.assertRaises(OSError):
                adapter.copy_to_stage(link, Path(temporary) / "staged", 5, os.getuid())
            with self.assertRaisesRegex(adapter.Refused, "source_size"):
                adapter.copy_to_stage(source, Path(temporary) / "staged", 4, os.getuid())
            self.assertFalse((Path(temporary) / "staged").exists())

    def test_staged_copy_is_independent_of_caller_replacement(self):
        with tempfile.TemporaryDirectory() as temporary:
            source, staged = Path(temporary) / "source", Path(temporary) / "stage"
            source.write_bytes(b"original")
            size, digest = adapter.copy_to_stage(source, staged, 8, os.getuid())
            source.write_bytes(b"modified")
            self.assertEqual(staged.read_bytes(), b"original")
            self.assertEqual((size, digest), (8, adapter.digest(b"original")))

    def test_authenticated_signed_version_must_equal_package(self):
        with tempfile.TemporaryDirectory() as temporary:
            package = Path(temporary) / "package.deb"
            package.write_bytes(deb())
            record = adapter.package_record(package.read_bytes())
            admission = {"packages": [record], "max_package_bytes": record["size"],
                         "max_expanded_data_bytes": record["expanded_data_bytes"]}
            calls = []
            def verifier(command):
                calls.append(command)
                return subprocess.CompletedProcess(command, 0, '{"version":"3.0.0"}', "")
            with self.assertRaisesRegex(adapter.Refused, "signed_version_differs"):
                adapter.verify_staged(package, Path(temporary) / "package.sig", admission, verifier)
            self.assertEqual(calls[0][0], "/usr/lib/campus-updater-1057/verify-signature")

    def test_bad_signature_refuses_even_an_admitted_package(self):
        with tempfile.TemporaryDirectory() as temporary:
            package = Path(temporary) / "package.deb"
            package.write_bytes(deb())
            record = adapter.package_record(package.read_bytes())
            admission = {"packages": [record], "max_package_bytes": record["size"]}
            with self.assertRaisesRegex(adapter.Refused, "signature_verification_failed"):
                adapter.verify_staged(package, Path(temporary) / "package.sig", admission,
                    lambda cmd: subprocess.CompletedProcess(cmd, 1, "", "signature rejected"))

    def test_mutated_root_staged_package_cannot_reuse_admission(self):
        with tempfile.TemporaryDirectory() as temporary:
            package = Path(temporary) / "package.deb"
            original = deb()
            record = adapter.package_record(original)
            package.write_bytes(original[:-1] + bytes([original[-1] ^ 1]))
            admission = {"packages": [record], "max_package_bytes": record["size"]}
            with self.assertRaisesRegex(adapter.Refused, "not_in_exact_fixture_admission"):
                adapter.verify_staged(package, Path(temporary) / "package.sig", admission,
                    lambda cmd: self.fail("unexpected verifier call for unadmitted fixture bytes"))

    def test_archive_traversal_and_setuid_refused(self):
        for name, mode in (("usr/../../etc/profile", 0o644),
                           ("usr/share/applications/campus-updater-1057.desktop", 0o4755)):
            with self.subTest(name=name), self.assertRaises(adapter.Refused):
                adapter.package_record(deb(extra=(name, b"payload", mode, tarfile.REGTYPE)))

    def test_replay_comparison_is_at_installer_seam_and_forward_rollback_passes(self):
        calls = []
        def compare(command):
            calls.append(command)
            return subprocess.CompletedProcess(command, 0 if command[2] > command[4] else 1)
        for version in ("1.0.0", "2.0.0"):
            with self.subTest(version=version), self.assertRaisesRegex(adapter.Refused, "signed_same_or_lower"):
                adapter.require_forward_version(version, "2.0.0", compare)
        adapter.require_forward_version("3.0.0", "2.0.0", compare)
        self.assertEqual(calls[-1], ["/usr/bin/dpkg", "--compare-versions", "3.0.0", "gt", "2.0.0"])


if __name__ == "__main__":
    unittest.main()
