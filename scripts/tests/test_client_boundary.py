"""Regression probes for the repository policy gate, not an application test suite."""

import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


CHECKER = Path(__file__).resolve().parents[1] / "check_client_boundary.py"


class BoundaryGateTests(unittest.TestCase):
    def run_gate(self, sources, entries=()):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name, source in sources.items():
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(source)
            (root / "scripts").mkdir(exist_ok=True)
            (root / "scripts/client-boundary-policy.json").write_text(
                json.dumps({"version": 1, "reviewed_files": list(entries)})
            )
            return subprocess.run(
                [sys.executable, str(CHECKER), "--root", str(root)],
                capture_output=True, text=True, check=False,
            )

    def test_literals_across_quotes_languages_and_source_locations(self):
        cases = {
            "src/view.ts": 'const engine = "codex";',
            "src/view.tsx": "const provider = 'openai';",
            "packages/view.jsx": "const stage = `done`;",
            "src-tauri/src/main.rs": 'let engine = "claude";',
            "src-tauri/src/raw.rs": 'let engine = r#"codex"#;',
            "new-host/tool.mjs": r'const provider = "\u006fpenai";',
            "other/tool.cts": r'const provider = "\x6fpenai";',
            "crates/raw.rs": r'let provider = "\u{6f}penai";',
        }
        for path, source in cases.items():
            with self.subTest(path=path):
                result = self.run_gate({path: source})
                self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                self.assertIn(f"{path}:1:", result.stdout)

    def test_common_transition_tables_and_multiline_error_inference(self):
        cases = [
            'const transitions = { queued: ["running"] };',
            'const workflowTransitions: Record<string, string[]> = { queued: ["running"] };',
            'const transition_table = new Map();',
            'const TRANSITIONS: &[(&str, &str)] = &[("queued", "running")];',
            'if (error.message\n .startsWith("secret-marker")) {}',
            'if (message?.includes("secret-marker")) {}',
            'if message.contains("secret-marker") {}',
        ]
        for source in cases:
            with self.subTest(source=source):
                result = self.run_gate({"src/logic.ts": source})
                self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                self.assertNotIn("secret-marker", result.stdout)

    def test_api_fields_and_comments_are_not_domain_decisions(self):
        result = self.run_gate({"src/view.ts": '''
// The API returns "openai"; never call error.message.includes("reason").
const provider = response.provider;
const stage = response.stage;
const description = "workflow transitions come from the API";
''', "src-tauri/src/lib.rs": '/* "claude" is an API identifier. */\nlet engine = response.engine;'})
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_only_fixture_comments_with_same_line_reasons_are_allowed(self):
        for path in ("tests/contract.ts", "src/view.test.ts", "fixtures/contract.rs"):
            for comment in ("// campus-boundary: allow server response fixture", "/* campus-boundary: allow server response fixture */"):
                with self.subTest(path=path, comment=comment):
                    result = self.run_gate({path: f'const engine = "codex"; {comment}'})
                    self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        invalid = [
            ("src/view.ts", 'const engine = "codex"; // campus-boundary: allow display choice'),
            ("tests/contract.ts", 'const engine = "codex"; // campus-boundary: allow '),
            ("tests/contract.ts", 'const engine = "codex"; /* campus-boundary: allow */'),
            ("tests/contract.ts", 'const note = "campus-boundary: allow fixture"; const engine = "codex";'),
            ("tests/contract.ts", '// campus-boundary: allow fixture\nconst engine = "codex";'),
        ]
        for path, source in invalid:
            with self.subTest(path=path, source=source):
                self.assertEqual(self.run_gate({path: source}).returncode, 1)

    def reviewed_entry(self, path, source, kind="generated-contract"):
        return {"path": path, "kind": kind, "sha256": hashlib.sha256(source.encode()).hexdigest(),
                "reason": "Verified contract or executor binding, no presentation decision",
                "evidence": "pinned source SHA and review receipt"}

    def test_generated_contracts_and_adapters_require_exact_review_receipts(self):
        for path, source, kind in (
            ("src/generated/api.ts", 'type Provider = "openai" | "anthropic";', "generated-contract"),
            ("src-tauri/src/engines.rs", 'const ENGINE: &str = "codex";', "executor-adapter"),
        ):
            with self.subTest(kind=kind):
                self.assertEqual(self.run_gate({path: source}).returncode, 1)
                entry = self.reviewed_entry(path, source, kind)
                result = self.run_gate({path: source}, [entry])
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                sibling = str(Path(path).with_name("unreviewed.ts"))
                self.assertEqual(self.run_gate({path: source, sibling: 'const engine = "codex";'}, [entry]).returncode, 1)
                self.assertEqual(self.run_gate({path: source + "\n// changed"}, [entry]).returncode, 1)

    def test_invalid_review_metadata_fails_closed(self):
        path, source = "src/generated/api.ts", 'type Engine = "codex";'
        for key, value in (("reason", " "), ("evidence", ""), ("kind", "presentation"),
                           ("path", "../outside.ts"), ("path", "missing.ts"), ("sha256", "bad")):
            with self.subTest(key=key, value=value):
                entry = self.reviewed_entry(path, source)
                entry[key] = value
                self.assertEqual(self.run_gate({path: source}, [entry]).returncode, 1)
        entry = self.reviewed_entry(path, source)
        self.assertEqual(self.run_gate({path: source}, [entry, entry]).returncode, 1)

    def test_empty_repository_does_not_claim_app_verification(self):
        result = self.run_gate({})
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("No product source yet", result.stdout)

    def test_missing_or_malformed_policy_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            policy = root / "scripts/client-boundary-policy.json"
            policy.parent.mkdir()
            for contents in (None, "{broken", '{"version": 2, "reviewed_files": []}'):
                with self.subTest(contents=contents):
                    if contents is not None:
                        policy.write_text(contents)
                    result = subprocess.run(
                        [sys.executable, str(CHECKER), "--root", str(root)],
                        capture_output=True, text=True, check=False,
                    )
                    self.assertEqual(result.returncode, 1)
                    self.assertIn("cannot verify policy", result.stdout)

    def test_source_symlinks_cannot_hide_unscanned_code(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "scripts").mkdir()
            (root / "scripts/client-boundary-policy.json").write_text(
                '{"version": 1, "reviewed_files": []}'
            )
            (root / "hidden.txt").write_text('const engine = "codex";')
            (root / "entry.ts").symlink_to("hidden.txt")
            result = subprocess.run(
                [sys.executable, str(CHECKER), "--root", str(root)],
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(result.returncode, 1)
            self.assertIn("source file symlinks", result.stdout)


if __name__ == "__main__":
    unittest.main()
