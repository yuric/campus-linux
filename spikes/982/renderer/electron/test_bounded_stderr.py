"""Real local children only; no Electron/guest/display/network."""
import io
import pathlib
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch
import bounded_stderr as cap


class CaptureTest(unittest.TestCase):
    def run_child(self, script, limit=3):
        err = io.BytesIO()
        with tempfile.TemporaryFile() as out:
            result = cap.capture([sys.executable, '-c', script], stdout=out,
                                 stderr=err, cwd=None, limit=limit)
        return result, err.getvalue()

    def test_overflow_drains_to_successful_eof(self):
        result, data = self.run_child('import os; os.write(2,b"x"*1048576)')
        self.assertEqual(result['returncode'], 0)
        self.assertEqual(result['stderr_bytes_observed'], 1048576)
        self.assertEqual(len(data), cap.LIMIT)
        self.assertEqual(data.count(cap.MARKER), 1)
        self.assertTrue(result['stderr_overflow'])
        self.assertFalse(result['usable'])

    def test_short_eof_preserved(self):
        result, data = self.run_child('import os; os.write(2,b"actual error")')
        self.assertEqual(data, b'actual error')
        self.assertFalse(result['stderr_overflow'])
        self.assertEqual(result['returncode'], 0)

    def test_deadline_after_eof_still_bounds_child(self):
        start = time.monotonic()
        result, _ = self.run_child('import os,time; os.close(2); time.sleep(30)', .15)
        self.assertTrue(result['timeout'])
        self.assertFalse(result['usable'])
        self.assertLess(time.monotonic()-start, 3)
        self.assertLess(result['returncode'], 0)

    def test_continuous_overflow_is_deadline_bounded(self):
        start = time.monotonic()
        result, data = self.run_child('import os\nwhile True: os.write(2,b"x"*16384)', .15)
        self.assertTrue(result['timeout'])
        self.assertFalse(result['usable'])
        self.assertEqual(len(data), cap.LIMIT)
        self.assertLess(time.monotonic()-start, 3)

    def test_hidden_reap_never_signals_recycled_group(self):
        original = subprocess.Popen.wait
        def hidden_wait(child, *args, **kwargs):
            original(child, *args, **kwargs)
            raise KeyboardInterrupt()
        with patch.object(subprocess.Popen, 'wait', hidden_wait), patch.object(cap.os, 'killpg') as kill:
            result, _ = self.run_child('pass')
            self.assertIn('KeyboardInterrupt', result['failure'])
            self.assertTrue(result['child_reaped'])
            self.assertFalse(result['usable'])
            kill.assert_not_called()

    def test_descendant_holding_stderr_cannot_extend_deadline(self):
        start = time.monotonic()
        result, _ = self.run_child('import subprocess,sys; subprocess.Popen([sys.executable,"-c","import time;time.sleep(30)"])', .15)
        self.assertEqual(result['returncode'], 0)
        self.assertTrue(result['timeout'])
        self.assertFalse(result['usable'])
        self.assertLess(time.monotonic()-start, 3)

    def test_write_failure_reaps_owned_child(self):
        class Broken:
            def write(self, data):
                raise OSError('full')
        children = []
        with tempfile.TemporaryFile() as out:
            result = cap.capture([sys.executable, '-c', 'import os,time;os.write(2,b"x");time.sleep(30)'],
                            stdout=out, stderr=Broken(), cwd=None, limit=3, launched=children.append)
        self.assertIsNotNone(children[0].returncode)
        self.assertIn('OSError: full', result['failure'])
        self.assertFalse(result['usable'])

    def test_diagnostic_receipt_cannot_freeze(self):
        with tempfile.TemporaryDirectory() as folder:
            root = pathlib.Path(folder)
            (root/'raw.json').write_text('{"kind":"preflight","diagnostic_only":"gpu-startup"}')
            result = subprocess.run([sys.executable, str(pathlib.Path(__file__).with_name('freeze.py')),
                                     str(root/'raw.json'), str(root/'unused'), str(root/'out')],
                                    capture_output=True, timeout=3)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn(b'not freeze or timing evidence', result.stderr)
            self.assertFalse((root/'out').exists())

    def test_compatibility_receipt_cannot_freeze_even_without_diagnostic_marker(self):
        import json
        for marker in (True, False):
            with self.subTest(marker=marker), tempfile.TemporaryDirectory() as folder:
                root = pathlib.Path(folder)
                raw = {'kind': 'preflight', 'gpu_compatibility': {'scope': 'whole-gpu-feature-compatibility-list'}}
                if marker:
                    raw['diagnostic_only'] = 'gpu-compatibility'
                (root/'raw.json').write_text(json.dumps(raw))
                result = subprocess.run([sys.executable, str(pathlib.Path(__file__).with_name('freeze.py')),
                                         str(root/'raw.json'), str(root/'unused'), str(root/'out')],
                                        capture_output=True, timeout=3)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn(b'not freeze or timing evidence', result.stderr)
                self.assertFalse((root/'out').exists())

    def test_software_compositor_marker_alone_cannot_freeze(self):
        import json
        with tempfile.TemporaryDirectory() as folder:
            root = pathlib.Path(folder)
            (root/'raw.json').write_text(json.dumps({'kind': 'preflight', 'software_compositor': {'timing_eligible': False}}))
            result = subprocess.run([sys.executable, str(pathlib.Path(__file__).with_name('freeze.py')),
                                     str(root/'raw.json'), str(root/'unused'), str(root/'out')],
                                    capture_output=True, timeout=3)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn(b'not freeze or timing evidence', result.stderr)
            self.assertFalse((root/'out').exists())

    def test_signal_error_still_attempts_wait_and_preserves_original_failure(self):
        from types import SimpleNamespace
        child = SimpleNamespace(pid=123, returncode=None, stderr=io.BytesIO())
        waits = []
        def wait(timeout):
            waits.append(timeout)
            child.returncode = 0
            return 0
        child.wait = wait
        def fail_launch(p):
            raise OSError('original launch observation failure')
        with patch.object(cap.subprocess, 'Popen', return_value=child), patch.object(cap.os, 'killpg', side_effect=PermissionError('signal refused')):
            result = cap.capture(['fixed'], stdout=None, stderr=io.BytesIO(), cwd=None, limit=1, launched=fail_launch)
        self.assertEqual(waits, [10])
        self.assertIn('original launch observation failure', result['failure'])
        self.assertIn('PermissionError', result['cleanup'][0]['error'])
        self.assertTrue(result['child_reaped'])
        self.assertFalse(result['usable'])

    def test_signal_and_wait_failure_remain_unknown_not_success(self):
        from types import SimpleNamespace
        child = SimpleNamespace(pid=123, returncode=None, stderr=io.BytesIO())
        def wait(timeout):
            raise subprocess.TimeoutExpired('fixed', timeout)
        child.wait = wait
        def fail_launch(p):
            raise OSError('original')
        with patch.object(cap.subprocess, 'Popen', return_value=child), patch.object(cap.os, 'killpg', side_effect=PermissionError('refused')):
            result = cap.capture(['fixed'], stdout=None, stderr=io.BytesIO(), cwd=None, limit=1, launched=fail_launch)
        self.assertIn('original', result['failure'])
        self.assertEqual([r['operation'] for r in result['cleanup']], ['killpg','wait'])
        self.assertFalse(result['child_reaped'])
        self.assertFalse(result['usable'])


if __name__ == '__main__':
    unittest.main()
