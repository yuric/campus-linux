"""Bounded scanner and process-exit cleanup regressions; no guest/crash required."""
import importlib.util
import json
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
    def test_discovery_error_after_stop_kills_all_retained_handles(self):
        watch = WATCH.Watchdog(1, lambda: None)
        watch.owned = {10: {'fd': 100}, 20: {'fd': 200}}
        sent = []
        def discover():
            self.assertEqual(sent, [(100, signal.SIGSTOP), (200, signal.SIGSTOP)])
            # Discovery may retain a child before encountering an attribution error.
            watch.owned[30] = {'fd': 300}
            raise RuntimeError('identity changed during pidfd acquisition')
        with patch.object(watch, 'descendants', discover), \
             patch.object(watch, 'live', return_value=False), \
             patch.object(WATCH.signal, 'pidfd_send_signal',
                          side_effect=lambda fd, sig: sent.append((fd, sig)), create=True), \
             patch.object(WATCH.os, 'close') as close:
            self.assertFalse(watch.stop())
            close.assert_not_called()
        self.assertEqual(sent[2:], [(300, signal.SIGKILL), (200, signal.SIGKILL),
                                    (100, signal.SIGKILL)])
        self.assertEqual(json.loads(json.dumps(watch.events)), [{
            'operation': 'descendant_freeze', 'pid': None, 'error_type': 'RuntimeError',
            'error': 'identity changed during pidfd acquisition'}])
        self.assertEqual([v['fd'] for v in watch.owned.values()], [100, 200, 300])

    def test_signal_error_does_not_skip_other_retained_handles(self):
        for failed_signal in (signal.SIGSTOP, signal.SIGKILL):
            with self.subTest(signal=failed_signal):
                watch = WATCH.Watchdog(1, lambda: None)
                watch.owned = {10: {'fd': 100}, 20: {'fd': 200}}
                sent = []
                failed_fd = 100 if failed_signal == signal.SIGSTOP else 200
                def send(fd, sig):
                    sent.append((fd, sig))
                    if (fd, sig) == (failed_fd, failed_signal):
                        raise PermissionError('synthetic signal refusal')
                with patch.object(watch, 'descendants'), \
                     patch.object(watch, 'live', return_value=False), \
                     patch.object(WATCH.signal, 'pidfd_send_signal', side_effect=send, create=True), \
                     patch.object(WATCH.time, 'sleep'), \
                     patch.object(WATCH.os, 'close') as close:
                    self.assertFalse(watch.stop())
                    close.assert_not_called()
                self.assertIn((100, signal.SIGSTOP), sent)
                self.assertIn((200, signal.SIGSTOP), sent)
                self.assertEqual(sent[-2:], [(200, signal.SIGKILL), (100, signal.SIGKILL)])
                self.assertEqual(watch.events, [{
                    'operation': failed_signal.name, 'pid': failed_fd // 10,
                    'error_type': 'PermissionError', 'error': 'synthetic signal refusal'}])

    def test_normal_discovery_attribution_error_still_raises(self):
        watch = WATCH.Watchdog(1, lambda: None)
        with patch.object(watch, 'descendants', side_effect=RuntimeError('unattributed child')):
            with self.assertRaisesRegex(RuntimeError, '^unattributed child$'):
                watch.tick()
        self.assertEqual(watch.events, [])

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
