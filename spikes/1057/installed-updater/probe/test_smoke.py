"""Receipt-admission regressions; these do not run or certify installed artifacts."""
import copy
import importlib.util
import json
from pathlib import Path
import unittest
from urllib.parse import urlsplit


spec = importlib.util.spec_from_file_location("installed_smoke", Path(__file__).with_name("smoke.py"))
smoke = importlib.util.module_from_spec(spec)
spec.loader.exec_module(smoke)
REPOSITORY = Path(__file__).resolve().parents[4]


def recorded_negatives():
    records = []
    for architecture in ("arm64", "amd64"):
        receipt_dir = REPOSITORY / "docs/acceptance/receipts/installed-updater-1057/first-build" / architecture
        receipt = json.loads((receipt_dir / "installed-smoke.json").read_text())
        index = json.loads((receipt_dir / "package-index.json").read_text())
        artifacts = {row["filename"]: row for row in index["artifacts"]}
        max_deb_bytes = max(row["bytes"] for row in artifacts.values() if row["format"] == "deb")
        for command in receipt["commands"]:
            fmt, _, kind = command["case"].partition("/") if command["case"] else ("", "", "")
            if "--update" not in command["argv"] or kind not in {
                    "missing-exact-target", "bad-signature", "signed-version-mismatch", "wrong-format"}:
                continue
            events = [json.loads(line) for line in command["stdout"].splitlines() if line.startswith("{")]
            args = {"kind": kind, "fmt": fmt, "target": events[0]["exact_target"], "events": events,
                    "requests": [row for row in receipt["requests"] if row["case"] == command["case"]]}
            if kind != "missing-exact-target":
                selected = events[1]
                artifact = artifacts[Path(urlsplit(selected["url"]).path).name]
                args.update(selected_url=selected["url"], package_sha256=artifact["sha256"],
                            package_bytes=artifact["bytes"], max_deb_bytes=max_deb_bytes)
            records.append((architecture + "/" + command["case"], args))
    return records


class NegativeEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.recorded = recorded_negatives()

    def test_actual_first_build_boundaries_are_admitted(self):
        self.assertEqual(len(self.recorded), 16)
        for name, args in self.recorded:
            with self.subTest(case=name):
                smoke.require_negative_evidence(**args)

    def test_gtk_refusal_and_zero_http_never_count_as_security_refusal(self):
        for name, args in self.recorded:
            for mutation in ("zero_http", "generic_failure", "generic_with_http", "wrong_error"):
                with self.subTest(case=name, mutation=mutation):
                    bad = copy.deepcopy(args)
                    if mutation in ("zero_http", "generic_failure"):
                        bad["requests"] = []
                    if mutation in ("generic_failure", "generic_with_http"):
                        bad["events"] = [{"event": "refused", "error": "GTK initialization failed"}]
                    if mutation == "wrong_error":
                        bad["events"][-1]["error"] = "GTK initialization failed"
                    with self.assertRaises(RuntimeError):
                        smoke.require_negative_evidence(**bad)

    def test_wrong_download_or_install_event_cannot_pass(self):
        for name, args in self.recorded:
            with self.subTest(case=name):
                bad = copy.deepcopy(args)
                bad["events"].insert(-1, {"event": "appimage_replaced"})
                with self.assertRaises(RuntimeError):
                    smoke.require_negative_evidence(**bad)
                bad = copy.deepcopy(args)
                bad["requests"].append({"path": "/packages/unintended.deb"})
                with self.assertRaises(RuntimeError):
                    smoke.require_negative_evidence(**bad)

    def test_missing_authority_is_not_wrong_format_evidence(self):
        for name, args in self.recorded:
            if args["kind"] != "wrong-format" or args["fmt"] != "deb":
                continue
            with self.subTest(case=name):
                bad = copy.deepcopy(args)
                adapter = json.loads(bad["events"][3]["stdout"])
                adapter.update(phase="admission", reason="polkit_caller_required")
                bad["events"][3]["stdout"] = json.dumps(adapter)
                with self.assertRaises(RuntimeError):
                    smoke.require_negative_evidence(**bad)

    def test_signed_wrong_architecture_requires_verified_expected_bytes(self):
        args = copy.deepcopy(next(args for _, args in self.recorded
                                  if args["fmt"] == "appimage" and args["kind"] == "wrong-format"))
        args["kind"] = "wrong-architecture"
        args["selected_url"] = "http://127.0.0.1:17857/negative/wrong-architecture"
        args["events"][1]["url"] = args["selected_url"]
        args["requests"] = [{"path": "/stable/linux.json"}, {"path": "/negative/wrong-architecture"}]
        smoke.require_negative_evidence(**args)
        args["events"][2]["sha256"] = "0" * 64
        with self.assertRaises(RuntimeError):
            smoke.require_negative_evidence(**args)

    def test_privileged_signature_requires_signature_seam_and_unchanged_hashes(self):
        before = {"app": "a" * 64, "helper": "b" * 64}
        response = {"status": "refused", "phase": "signature_and_schema", "reason": "signature_verification_failed",
                    "installed_version": "1.0.0", "package_sha256": "c" * 64, "app_helper_unchanged": True,
                    "before": before, "after": dict(before)}
        smoke.require_privileged_signature_refusal(response, "c" * 64)
        for mutation in ({"reason": "polkit_caller_required"}, {"phase": "root_staging"}, {"dpkg_exit": 1},
                         {"authenticated_version": "2.0.0"}, {"after": {"app": "d" * 64, "helper": "b" * 64}}):
            with self.subTest(mutation=mutation):
                with self.assertRaises(RuntimeError):
                    smoke.require_privileged_signature_refusal({**response, **mutation}, "c" * 64)


if __name__ == "__main__":
    unittest.main()
