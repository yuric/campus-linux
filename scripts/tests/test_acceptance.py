import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


acceptance = module("acceptance", "scripts/check_acceptance.py")
admission = module("admission", "scripts/check-linux-admission.py")


class AdmissionTests(unittest.TestCase):
    def setUp(self):
        self.head = "a" * 40
        self.repo = {"visibility": "PUBLIC"}
        self.pr = {"headRefOid": self.head, "statusCheckRollup": [
            {"name": name, "status": "COMPLETED", "conclusion": "SUCCESS"}
            for name in sorted(admission.REQUIRED)]}

    def test_all_success_at_exact_head(self):
        admission.validate(self.pr, self.repo, self.head)

    def test_reject_every_non_success_state(self):
        for state in ["SKIPPED", "CANCELLED", "FAILURE", "NEUTRAL", "TIMED_OUT", None]:
            with self.subTest(state=state):
                changed = copy.deepcopy(self.pr)
                changed["statusCheckRollup"][0]["conclusion"] = state
                with self.assertRaises(ValueError):
                    admission.validate(changed, self.repo, self.head)

    def test_reject_missing_check(self):
        self.pr["statusCheckRollup"].pop()
        with self.assertRaises(ValueError):
            admission.validate(self.pr, self.repo, self.head)

    def test_reject_private_and_changed_head(self):
        for repo, head in [({"visibility": "PRIVATE"}, self.head), (self.repo, "b" * 40)]:
            with self.assertRaises(ValueError):
                admission.validate(self.pr, repo, head)


class ReceiptTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name)
        self.head = "a" * 40
        self.results = {"verify_amd64": "success", "verify_arm64": "success"}
        lock = json.loads((ROOT / "ci/toolchain-lock.json").read_text())
        for arch in ["amd64", "arm64"]:
            r = {"repository": "yuric/campus-linux", "head": self.head, "arch": arch,
                 "base": lock["verification_base"], "result": "success", "scope": "repository-policy",
                 "image_id": "sha256:" + "b" * 64, "archive_sha256": "c" * 64,
                 "container_command": "python3 -B scripts/verify_repository.py",
                 "dockerfile_sha256": hashlib.sha256((ROOT / "ci/Dockerfile.verify").read_bytes()).hexdigest()}
            for key in ["log", "packages"]:
                name = f"{key}-{arch}.txt"
                (self.path / name).write_text("synthetic policy-tool test fixture")
                r[key] = name
                r[key + "_sha256"] = hashlib.sha256((self.path / name).read_bytes()).hexdigest()
            (self.path / f"receipt-{arch}.json").write_text(json.dumps(r))

    def check(self):
        acceptance.check_receipts(self.path, self.head, self.results)

    def test_accept_bound_receipts(self):
        self.check()

    def test_reject_skipped_failed_cancelled_missing_jobs(self):
        for value in ["skipped", "failure", "cancelled", "", None]:
            self.results["verify_arm64"] = value
            with self.assertRaises(ValueError):
                self.check()
        self.results.pop("verify_arm64")
        with self.assertRaises(ValueError):
            self.check()

    def test_reject_missing_receipt(self):
        (self.path / "receipt-arm64.json").unlink()
        with self.assertRaises(FileNotFoundError):
            self.check()

    def test_reject_tampered_log(self):
        (self.path / "log-arm64.txt").write_text("different")
        with self.assertRaises(ValueError):
            self.check()

    def test_reject_wrong_head_arch_base_image_source_and_command(self):
        file = self.path / "receipt-arm64.json"
        original = json.loads(file.read_text())
        for field, value in [("head", "b" * 40), ("arch", "amd64"), ("base", "ubuntu:latest"),
                             ("image_id", "unknown"), ("archive_sha256", "e" * 64),
                             ("dockerfile_sha256", "f" * 64), ("container_command", "true")]:
            with self.subTest(field=field):
                file.write_text(json.dumps(dict(original, **{field: value})))
                with self.assertRaises(ValueError):
                    self.check()
        file.write_text(json.dumps(original))


if __name__ == "__main__":
    unittest.main()
