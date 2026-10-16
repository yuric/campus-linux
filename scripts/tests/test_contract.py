import importlib.util
import pathlib
import shutil
import subprocess
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("contract", ROOT / "scripts/check_contract.py")
contract = importlib.util.module_from_spec(spec)
spec.loader.exec_module(contract)


class ContractTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = pathlib.Path(self.temp.name)
        self.server = self.base / "server"
        self.server.mkdir()
        self.git("init", "-q")
        self.git("config", "user.email", "fixture@example.invalid")
        self.git("config", "user.name", "fixture")
        self.write(self.server / contract.SPEC,
                   "openapi: 3.0.3\npaths:\n  /fixture:\n    get:\n"
                   "      externalValue: '../../contracts/example.json'\n")
        self.write(self.server / "contracts/example.json", '{"fixture": true}\n')
        self.write(self.server / "contracts/unreferenced.json", '{}\n')
        self.git("add", ".")
        self.git("-c", "commit.gpgsign=false", "commit", "-qm", "fixture")
        self.sha = self.git("rev-parse", "HEAD").strip()
        self.git("update-ref", "refs/remotes/origin/main", self.sha)
        self.bundle = self.base / "contract"
        for name in [contract.SPEC, "contracts/example.json", "contracts/unreferenced.json"]:
            self.write(self.bundle / name, (self.server / name).read_text())
        self.write(self.bundle / ".source", f"yuric/campus-server@{self.sha}\n")

    def git(self, *args):
        return subprocess.check_output(["git", "-C", str(self.server), *args], text=True)

    def write(self, path, value):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(value)

    def test_complete_bundle_matches_ref_and_fresh_export(self):
        fresh = self.base / "fresh"
        shutil.copytree(self.bundle, fresh)
        result = contract.check(self.bundle, self.server, fresh)
        self.assertEqual(result["files"], 4)
        self.assertEqual(result["external_targets"], 1)
        self.assertTrue(result["server_comparison"])

    def test_provenance_rejects_old_repository_and_bad_sha(self):
        for value in [f"campus@{self.sha}\n", "yuric/campus-server@HEAD\n"]:
            with self.subTest(value=value):
                self.write(self.bundle / ".source", value)
                with self.assertRaisesRegex(ValueError, "provenance"):
                    contract.check(self.bundle)

    def test_missing_external_fixture_fails(self):
        (self.bundle / "contracts/example.json").unlink()
        with self.assertRaisesRegex(ValueError, "missing externalValue"):
            contract.check(self.bundle)

    def test_external_targets_cannot_escape_or_use_network(self):
        for value in ["../../../outside.json", "/tmp/outside.json", "https://example.invalid/a", "//example.invalid/a"]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                contract.external_targets({"examples": [{"externalValue": value}]})

    def test_unreferenced_fixture_is_required_by_server_comparison(self):
        (self.bundle / "contracts/unreferenced.json").unlink()
        with self.assertRaisesRegex(ValueError, "leaf paths"):
            contract.check(self.bundle, self.server)

    def test_extra_file_fails_server_comparison(self):
        self.write(self.bundle / "stale.json", "{}")
        with self.assertRaisesRegex(ValueError, "leaf paths"):
            contract.check(self.bundle, self.server)

    def test_changed_bytes_fail_server_comparison(self):
        self.write(self.bundle / "contracts/example.json", "{}")
        with self.assertRaisesRegex(ValueError, "mode/bytes"):
            contract.check(self.bundle, self.server)

    def test_changed_executable_mode_fails_server_comparison(self):
        (self.bundle / "contracts/example.json").chmod(0o755)
        with self.assertRaisesRegex(ValueError, "mode/bytes"):
            contract.check(self.bundle, self.server)

    def test_symlink_fails_before_reading_content(self):
        path = self.bundle / "contracts/example.json"
        path.unlink()
        path.symlink_to(self.server / "contracts/example.json")
        with self.assertRaisesRegex(ValueError, "non-regular"):
            contract.check(self.bundle)

    def test_reexport_changed_bytes_fail(self):
        fresh = self.base / "fresh"
        shutil.copytree(self.bundle, fresh)
        self.write(fresh / "contracts/example.json", "{}")
        with self.assertRaisesRegex(ValueError, "fresh re-export differs"):
            contract.check(self.bundle, reexport=fresh)

    def test_invalid_json_fails(self):
        self.write(self.bundle / "contracts/example.json", "invalid JSON")
        with self.assertRaises(ValueError):
            contract.check(self.bundle)

    def test_unmerged_server_source_fails_ancestry(self):
        self.git("-c", "commit.gpgsign=false", "commit", "--allow-empty", "-qm", "unmerged")
        unmerged = self.git("rev-parse", "HEAD").strip()
        self.write(self.bundle / ".source", f"yuric/campus-server@{unmerged}\n")
        with self.assertRaises(subprocess.CalledProcessError):
            contract.check(self.bundle, self.server)
