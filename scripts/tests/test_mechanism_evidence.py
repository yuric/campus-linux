import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

SPEC = importlib.util.spec_from_file_location('mechanism_evidence', Path(__file__).resolve().parents[1] / 'check_mechanism_evidence.py')
CHECK = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CHECK)


class MechanismEvidenceTests(unittest.TestCase):
    def test_ignored_present_log_cannot_masquerade_as_delivered_evidence(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            subprocess.run(['git', 'init', '-q', temp], check=True)
            (root/'.gitignore').write_text('*.log\n')
            (root/'raw.log').write_bytes(b'actual synthetic capture\n')
            data = (root/'raw.log').read_bytes()
            (root/'index.json').write_text(json.dumps({'files': [{'path':'raw.log','bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}]}))
            subprocess.run(['git','add','.gitignore','index.json'], cwd=root, check=True)
            with self.assertRaisesRegex(ValueError, 'untracked indexed evidence'):
                CHECK.verify(root, ['index.json'])
            subprocess.run(['git','add','-f','raw.log'], cwd=root, check=True)
            self.assertEqual(CHECK.verify(root, ['index.json']), 1)
            (root/'raw.log').write_bytes(b'changed synthetic text!\n')
            with self.assertRaises(ValueError):
                CHECK.verify(root, ['index.json'])
            (root/'raw.log').unlink()
            with self.assertRaises(FileNotFoundError):
                CHECK.verify(root, ['index.json'])

    def test_archive_export_still_checks_hashes_without_git_metadata(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root/'raw.txt').write_bytes(b'one')
            (root/'index.json').write_text(json.dumps({'files': [{'path':'raw.txt','bytes':3,'sha256':hashlib.sha256(b'one').hexdigest()}]}))
            self.assertEqual(CHECK.verify(root, ['index.json']), 1)
            (root/'raw.txt').write_bytes(b'two')
            with self.assertRaisesRegex(ValueError, 'digest mismatch'):
                CHECK.verify(root, ['index.json'])
