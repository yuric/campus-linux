"""Read-only real-bundle mutation probes; all changed bytes remain in memory."""
import copy
import importlib.util
import json
from pathlib import Path
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]


def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / (name + ".py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


contract = load("check_contract")
acceptance = load("check_acceptance")


class OfflineContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.files = contract.leaves(ROOT / "contract")
        cls.ledger = json.loads((ROOT / "docs/acceptance/actions.json").read_text())
        cls.source = cls.files[".source"][1].decode()
        cls.spec_bytes = cls.files[contract.SPEC][1]

    def check_files(self, files):
        with patch.object(contract, "leaves", return_value=files):
            return contract.check(ROOT / "contract")

    def check_ledger(self, ledger):
        return acceptance.check_contract_bindings(ledger, self.source, self.spec_bytes)

    def test_current_bundle_and_ledger_match(self):
        self.assertEqual(self.check_files(self.files)["files"], 166)
        self.assertEqual(self.check_ledger(self.ledger), (431, 1275))

    def test_fixture_add_delete_edit_and_mode_fail_offline(self):
        targets = contract.external_targets(contract.yaml.safe_load(self.spec_bytes))
        name = next(name for name in self.files if name.startswith("contracts/") and name not in targets)
        for mutation in ("add", "delete", "edit", "mode"):
            with self.subTest(mutation=mutation):
                files = self.files.copy()
                if mutation == "add":
                    files["contracts/unexpected.json"] = ("100644", b"{}")
                elif mutation == "delete":
                    del files[name]
                elif mutation == "edit":
                    files[name] = (files[name][0], b"{}")
                else:
                    files[name] = ("100755", files[name][1])
                with self.assertRaisesRegex(ValueError, "reviewed digest pin"):
                    self.check_files(files)

    def test_missing_source_or_spec_fails(self):
        for name in (".source", contract.SPEC):
            with self.subTest(name=name):
                files = self.files.copy()
                del files[name]
                with self.assertRaisesRegex(ValueError, "missing contract"):
                    self.check_files(files)

    def test_stale_source_and_hash_fail(self):
        for key in ("server_contract_source", "server_contract_sha256"):
            with self.subTest(key=key):
                ledger = copy.deepcopy(self.ledger)
                ledger[key] = "stale"
                with self.assertRaisesRegex(ValueError, "ledger contract"):
                    self.check_ledger(ledger)

    def test_stale_operations_fail(self):
        for mutation in ("wrong_id", "missing_id", "path", "method", "pointer", "dangling_ref"):
            with self.subTest(mutation=mutation):
                ledger = copy.deepcopy(self.ledger)
                op = next(row["operations"][0] for row in ledger["actions"] if row["operations"])
                if mutation == "wrong_id":
                    op["operation_id"] = "doesNotExist"
                elif mutation == "missing_id":
                    del op["operation_id"]
                elif mutation == "path":
                    op["path"] = "/does-not-exist"
                elif mutation == "method":
                    op["method"] = "DELETE"
                elif mutation == "pointer":
                    op["schema_pointer"] = "#/paths/~1different/get"
                else:
                    op["schema_refs"].append("#/components/schemas/DoesNotExist")
                with self.assertRaises(ValueError):
                    self.check_ledger(ledger)

    def test_matching_path_pointer_still_requires_real_operation(self):
        ledger = copy.deepcopy(self.ledger)
        op = next(row["operations"][0] for row in ledger["actions"] if row["operations"])
        op["path"] = "/does-not-exist"
        op["schema_pointer"] = "#/paths/~1does-not-exist/" + op["method"].lower()
        with self.assertRaisesRegex(ValueError, "dangling schema pointer"):
            self.check_ledger(ledger)

    def test_pointer_escaping_and_arrays(self):
        document = {"a/b~c": [None]}
        self.assertIsNone(acceptance.resolve_pointer(document, "#/a~1b~0c/0"))
        for pointer in ("#/a~1b~0c/-1", "#/a~1b~0c/01", "#/a~1b~0c/1", "#/a~2b"):
            with self.subTest(pointer=pointer), self.assertRaises(ValueError):
                acceptance.resolve_pointer(document, pointer)
