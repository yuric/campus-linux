"""Bounded scanner and process-exit cleanup regressions; no guest/crash required."""
import importlib.util
from pathlib import Path
import signal
import sys
import unittest
from unittest.mock import patch

SOURCE = Path(__file__).resolve().parents[2]/'spikes/982/security/full-report'

def load(name):
    spec = importlib.util.spec_from_file_location('full_report_'+name, SOURCE/(name+'.py'))
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value

WATCH = load('watchdog')
with patch.dict(sys.modules, {'report_scan': load('report_scan')}):
    ScannerTests = load('test_report_scan').ScannerTests


class WatchdogExitRaceTests(unittest.TestCase):
    def test_parent_exit_during_child_read_still_stops_other_retained_pidfds(self):
        watch = WATCH.Watchdog(1, lambda: None)
        watch.owned = {10: {'fd': 100}, 20: {'fd': 200}}
        live = {10, 20}
        sent = []
        def send(pid, sig):
            sent.append((pid, sig))
            if sig == signal.SIGKILL:
                live.discard(pid)
        def read(path):
            if '/10/' in str(path):
                live.discard(10)
                raise FileNotFoundError('retained parent exited')
            return b''
        with patch.object(watch, 'live', lambda pid: pid in live), \
             patch.object(watch, 'send', send), patch.object(WATCH, 'read', read), \
             patch.object(WATCH.time, 'sleep', lambda _: None):
            self.assertTrue(watch.stop())
        self.assertIn((20, signal.SIGKILL), sent)
        self.assertFalse(live)
