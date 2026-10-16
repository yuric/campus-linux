"""Actual entrypoints/Handler concurrency and bounded fault schedules, no guest."""
import ast
from contextlib import ExitStack
import hashlib
import http.server
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import threading
import unittest
from unittest.mock import Mock, patch
import importlib.util

import desktop
import gated
import test_gated as fixtures
from test_gated import binding, release

SOURCE = Path(__file__).parent
spec = importlib.util.spec_from_file_location('repair_driver', SOURCE / 'gated-driver.py')
driver = importlib.util.module_from_spec(spec)
spec.loader.exec_module(driver)


class EntrypointTests(unittest.TestCase):
    def test_actual_isolated_old_and_new_cli_emit_incomplete_receipts(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            # A caller-CWD module must not be executed, even when it exists.
            (root / 'gated.py').write_text('raise AssertionError("caller module executed")')
            for mode in ('--validate-denial', '--validate-user-manager'):
                output = root / (mode + '.json')
                args = [sys.executable, '-I', '-B', str(SOURCE.resolve() / 'desktop.py'), mode, str(root / 'absent'),
                        '--desktop-receipt-sha256', '0' * 64, '--authority-receipt', str(root / 'authority'),
                        '--authority-receipt-sha256', '0' * 64, '--journal', str(root / 'journal'),
                        '--journal-sha256', '0' * 64, '--authority-helper-sha256', '0' * 64,
                        '--validation-receipt', str(output)]
                if mode == '--validate-user-manager':
                    args += ['--controller-sha256', '0' * 64]
                run = subprocess.run(args, cwd=root, capture_output=True, text=True, timeout=5)
                self.assertEqual(run.returncode, 1, run.stderr)
                self.assertTrue(output.exists(), run.stderr)
                value = json.loads(output.read_text())
                self.assertEqual(value['status'], 'incomplete')
                self.assertNotIn('ModuleNotFoundError', run.stderr)


class HandlerTests(unittest.TestCase):
    def handlers(self, root, gate):
        # Compile the actual nested Handler, preserving the production body.
        path = SOURCE / 'serve.py'
        node = next(n for n in ast.walk(ast.parse(path.read_text())) if isinstance(n, ast.ClassDef) and n.name == 'Handler')
        data = b'bounded package fixture'
        package = root / 'fixture.deb'; package.write_bytes(data)
        artifact = {'format': 'deb', 'architecture': 'arm64', 'version': '2.0.0', 'path': package,
                    'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}
        manifest = {'version': '2.0.0', 'platforms': {'linux-aarch64-deb': {'signature': 'unchanged'}}}
        namespace = dict(http=http, gate=gate, json=json, artifacts={'fixture.deb': artifact},
                         manifest=manifest, record=Mock(), shutil=shutil,
                         digest=lambda path: hashlib.sha256(path.read_bytes()).hexdigest())
        exec(compile(ast.Module(body=[node], type_ignores=[]), str(path), 'exec'), namespace)
        def make(path):
            h = object.__new__(namespace['Handler']); h.path = path; h.connection = Mock()
            h.send_response = Mock(); h.send_header = Mock(); h.end_headers = Mock(); h.send_error = Mock()
            h.wfile = io.BytesIO()
            return h
        return make('/stable/linux.json'), make('/packages/fixture.deb'), json.dumps(manifest).encode(), data

    def test_two_real_workers_immediate_package_and_failed_write(self):
        for broken in (False, True):
            with self.subTest(broken=broken), tempfile.TemporaryDirectory() as directory:
                g = fixtures.GateTests().gate(); b = binding()
                def manifest(connection):
                    g.state, g.binding, g.release = 'released', b, release(b)
                g.manifest = manifest
                first, second, expected, package = self.handlers(Path(directory), g)
                entered, requested, finished, errors = threading.Event(), threading.Event(), threading.Event(), []
                body = io.BytesIO()
                class Writer:
                    def write(self, data):
                        body.write(data); entered.set()
                        if not requested.wait(1): raise AssertionError('second worker missing')
                        # Worker two has started while the complete body is visible.
                        if finished.wait(.05) and not broken: raise AssertionError('package raced manifest delivery')
                        if broken: raise BrokenPipeError('injected partial/failed manifest write')
                    def flush(self): pass
                first.wfile = Writer()
                def deliver():
                    try: first.do_GET()
                    except Exception as error: errors.append(error)
                def fetch():
                    entered.wait(1); requested.set()
                    try: second.do_GET()
                    except Exception as error: errors.append(error)
                    finally: finished.set()
                with patch.object(gated.time, 'monotonic_ns', return_value=1000), \
                        patch.object(gated, 'root_read', return_value=release(b)):
                    threads = [threading.Thread(target=deliver), threading.Thread(target=fetch)]
                    for t in threads: t.start()
                    for t in threads: t.join(2)
                    self.assertFalse(any(t.is_alive() for t in threads))
                if broken:
                    self.assertEqual(g.state, 'failed'); second.send_error.assert_called_with(409)
                    self.assertTrue(any(isinstance(e, BrokenPipeError) for e in errors))
                else:
                    self.assertEqual(errors, [])
                    second.send_error.assert_not_called(); second.send_response.assert_called_with(200)
                    self.assertEqual(body.getvalue(), expected); self.assertEqual(second.wfile.getvalue(), package)

    def test_ordinary_handler_bytes_unchanged(self):
        with tempfile.TemporaryDirectory() as directory:
            first, second, manifest, package = self.handlers(Path(directory), None)
            first.do_GET(); second.do_GET()
            self.assertEqual(first.wfile.getvalue(), manifest)
            self.assertEqual(second.wfile.getvalue(), package)


class PublicationTests(unittest.TestCase):
    def test_final_hint_absent_during_write_and_complete_after_link(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'app.json'; real_write = os.write
            def interleave(fd, raw):
                with self.assertRaises(FileNotFoundError): gated.hint_read(path)
                return real_write(fd, raw)
            with patch.object(gated.os, 'write', side_effect=interleave):
                gated.hint_write(path, {'app_pid': 123})
            self.assertEqual(gated.hint_read(path), {'app_pid': 123})
            with self.assertRaises(FileExistsError): gated.hint_write(path, {'app_pid': 456})
            self.assertEqual(gated.hint_read(path), {'app_pid': 123})

    def test_partial_hint_write_never_publishes(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'app.json'
            with patch.object(gated.os, 'write', return_value=1), self.assertRaises(RuntimeError):
                gated.hint_write(path, {'app_pid': 123})
            self.assertFalse(path.exists())

    def test_readiness_consumes_only_complete_bounded_lines(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'server.jsonl'
            self.assertFalse(driver.server_ready(path))
            for raw in (b'', b'{', b'{"event":"serving"}'):
                path.write_bytes(raw); self.assertFalse(driver.server_ready(path))
            path.write_bytes(b'{"event":"serving"}\n{"event":')
            self.assertTrue(driver.server_ready(path))
            path.write_bytes(b'bad\n')
            with self.assertRaises(ValueError): driver.server_ready(path)
            path.write_bytes(b'x' * (gated.LIMIT + 1))
            with self.assertRaises(RuntimeError): driver.server_ready(path)

    def test_driver_wait_covers_delayed_setup_and_full_retention(self):
        # Prepared at 1s, setup ends at 11s, absent restoration retains until64s.
        # Old launch-relative58s timeout would end at59s and kill the parent early.
        child = Mock()
        def wait(timeout):
            self.assertGreaterEqual(1 + timeout, 64)
            return 1
        child.wait.side_effect = wait
        with patch.object(driver.time, 'monotonic_ns', return_value=1_000_000_000):
            self.assertEqual(driver.wait_recorder(child, {'prepare_deadline_ns': 61_000_000_000}), 1)
        child.terminate.assert_not_called()


class KernelExitTests(unittest.TestCase):
    def test_exe_disappearing_allows_only_same_lifetime_bounded_exit(self):
        def stat_line(state='S', start='10', parent='122'):
            fields = [state, parent] + ['0'] * 17 + [start]
            return '123 (app) ' + ' '.join(fields)
        for transition, accepted in ((['S', 'Z', 'Z'], True), (['S'] * 6, False), (['S', 'changed'], False)):
            with self.subTest(transition=transition):
                values = iter(transition)
                def read(path):
                    if path.name == 'stat':
                        state = next(values)
                        return stat_line('Z' if state == 'changed' else state, '11' if state == 'changed' else '10')
                    if path.name == 'status': return 'Uid:\t1000 1000 1000 1000\nGid:\t1000 1000 1000 1000\n'
                    return 'gui'
                with patch.object(gated.Path, 'read_text', autospec=True, side_effect=read), \
                        patch.object(gated.os, 'readlink', side_effect=FileNotFoundError), patch.object(gated.time, 'sleep') as sleep:
                    if accepted:
                        row = gated.kernel_process(123, zombie=True)
                        self.assertEqual(row['state'], 'Z'); self.assertNotIn('exe', row)
                    else:
                        with self.assertRaises((RuntimeError, FileNotFoundError)): gated.kernel_process(123, zombie=True)
                    self.assertLessEqual(sleep.call_count, 4)


class RetentionFaultTests(unittest.TestCase):
    def test_setup_delay_failure_kills_without_reaping_until_ack_or_bound(self):
        self.retention_fault()

    def test_abort_hint_oserror_kills_before_restoration_without_early_reap(self):
        self.retention_fault('abort')

    def test_malformed_ack_retains_until_valid_ack_or_bound(self):
        self.retention_fault('ack')

    def test_receipt_save_failure_retains_until_ack_or_bound(self):
        self.retention_fault('save')

    def retention_fault(self, fault=None):
        from types import SimpleNamespace
        for acknowledgment_at in (None, 62):
            with self.subTest(acknowledgment_at=acknowledgment_at):
                recorder = desktop.Recorder.__new__(desktop.Recorder)
                recorder.args = SimpleNamespace(gate_directory=Path('/gate'), case='deny', timeout=20,
                                                lease_reference='lease1', gate_server_pid=125)
                recorder.receipt, recorder.save = {'commands': []}, Mock()
                recorder.sample_children = Mock(side_effect=RuntimeError('injected recorder failure'))
                config = {'lease': 'lease1', 'nonce': 'a' * 32, 'boot_id': 'b' * 32,
                          'hints': '/hints', 'prepare_deadline_ns': 61_000_000_000}
                # Recorder launched at 1; actual app setup took ten seconds.
                clock = [11_000_000_000]; restored = [False]
                def sleep(seconds): clock[0] += 1_000_000_000
                events = []
                def hint_write(path, value):
                    if path.name == 'abort.json':
                        events.append('abort')
                        if fault == 'abort': raise OSError('injected abort publication failure')
                def save():
                    if fault == 'save' and 'kill' in events:
                        raise OSError('injected receipt save failure')
                recorder.save.side_effect = save
                def root_read(path):
                    self.assertIn('kill', events, 'restoration waiting preceded kill')
                    events.append('restoration')
                    if acknowledgment_at is None or clock[0] < acknowledgment_at * 1_000_000_000:
                        if fault == 'ack': return {'rule_absent': False}
                        raise FileNotFoundError
                    restored[0] = True
                    return {**{k: config[k] for k in ('lease', 'nonce', 'boot_id')},
                            'rule_absent': True, 'restored_ns': clock[0]}
                child = Mock(pid=123)
                child.poll.side_effect = AssertionError('early poll')
                child.wait.side_effect = lambda **kw: -9 if restored[0] else self.fail('early reap')
                selector = Mock(); selector.get_map.return_value = True
                with ExitStack() as stack:
                    for target, name, options in (
                        (desktop.gated, 'config_read', {'return_value': config}),
                        (desktop.gated, 'hint_write', {'side_effect': hint_write}),
                        (desktop.gated, 'root_read', {'side_effect': root_read}),
                        (desktop.gated, 'child_exit', {'return_value': -9}),
                        (desktop.time, 'monotonic_ns', {'side_effect': lambda: clock[0]}),
                        (desktop.time, 'sleep', {'side_effect': sleep}),
                        (desktop.subprocess, 'Popen', {'return_value': child}),
                        (desktop, 'logind_process', {'return_value': {'session': None}}),
                        (desktop.os, 'set_blocking', {}),
                        (desktop.selectors, 'DefaultSelector', {'return_value': selector})):
                        stack.enter_context(patch.object(target, name, **options))
                    kill = stack.enter_context(patch.object(desktop.os, 'killpg', side_effect=lambda *args: events.append('kill')))
                    with self.assertRaisesRegex(RuntimeError, 'injected recorder failure'):
                        recorder.gated_command([desktop.APP, '--update'])
                    kill.assert_called_once_with(123, desktop.signal.SIGKILL)
                child.poll.assert_not_called(); child.communicate.assert_not_called()
                if acknowledgment_at is None:
                    child.wait.assert_not_called()
                    self.assertGreaterEqual(clock[0], 64_000_000_000)
                    self.assertEqual(recorder._unreaped, [child])
                else:
                    child.wait.assert_called_once()
                    self.assertGreaterEqual(clock[0], 62_000_000_000)
                record = recorder.receipt['commands'][0]
                self.assertEqual(record['gated_error'], 'injected recorder failure')
                self.assertLess(events.index('abort'), events.index('kill'))
                self.assertLess(events.index('kill'), events.index('restoration'))
                if fault == 'abort': self.assertEqual(record['abort_hint_error'], 'injected abort publication failure')
                if fault == 'save': self.assertEqual(record['receipt_save_error'], 'injected receipt save failure')
                if fault == 'ack': self.assertIn('invalid root restoration', record['restoration_observation_error'])
                summary = record['pkexec_pid_observation']
                self.assertIn('name-only is not executable verification', summary['limitation'])


class ControllerCleanupTests(unittest.TestCase):
    def test_release_removed_after_restore_and_ack_withheld_when_rule_remains(self):
        from types import SimpleNamespace
        spec = importlib.util.spec_from_file_location('repair_control', SOURCE / 'gated-control.py')
        control = importlib.util.module_from_spec(spec); spec.loader.exec_module(control)
        for remains in (False, True):
            with self.subTest(remains=remains), tempfile.TemporaryDirectory() as directory:
                root = Path(directory); rel = {'exact': 'release'}
                (root / 'release.json').write_text(json.dumps(rel))
                (root / '.release.json.pending').write_text(json.dumps(rel))
                config = {'lease': 'lease1', 'nonce': 'a' * 32, 'boot_id': 'b' * 32}
                window = Mock(); window.record = {'gate_release': rel, 'status': 'failed'}
                def restore(): self.assertTrue((root / 'release.json').exists())
                window.restore.side_effect = restore
                def publish(directory, name, value):
                    self.assertFalse((root / 'release.json').exists())
                    self.assertFalse((root / '.release.json.pending').exists())
                    self.assertTrue(value['rule_absent'])
                gate = Mock(); gate.require = gated.require; gate.root_read.return_value = rel
                gate.publish.side_effect = publish
                with patch.object(control.os.path, 'lexists', return_value=remains):
                    if remains:
                        with self.assertRaisesRegex(RuntimeError, 'rule remains'):
                            control.restore_and_ack(window, SimpleNamespace(gate_directory=root), gate,
                                                    SimpleNamespace(RULE='/owned/rule'), config)
                        gate.publish.assert_not_called()
                    else:
                        control.restore_and_ack(window, SimpleNamespace(gate_directory=root), gate,
                                                SimpleNamespace(RULE='/owned/rule'), config)
                        gate.publish.assert_called_once()


class PositiveCliTests(unittest.TestCase):
    def test_both_actual_isolated_validators_and_controller_hash_mismatch(self):
        import test_desktop
        direct = test_desktop.DenialCorrelationTests(); direct.setUp()
        user = fixtures.CorrelationTests().fixture()
        for mode, values in (('--validate-denial', (direct.desktop, direct.authority, direct.rows)),
                             ('--validate-user-manager', user)):
            d, a, rows = values
            source_hash = lambda name: hashlib.sha256((SOURCE / name).read_bytes()).hexdigest()
            d['recorder'] = {'sha256': source_hash('desktop.py')}
            a['authority_helper'] = {'sha256': source_hash('authority-window.py')}
            a['gated_control_sources'] = {'controller_sha256': source_hash('gated-control.py'),
                                         'gui_sources': {n: {'sha256': source_hash(n)} for n in
                                                        ('desktop.py', 'gated.py', 'serve.py', 'gated-driver.py')}}
            for wrong in ((False, True) if mode == '--validate-user-manager' else (False,)):
                with self.subTest(mode=mode, wrong=wrong), tempfile.TemporaryDirectory() as directory:
                    root = Path(directory)
                    contents = {'desktop': json.dumps(d), 'authority': json.dumps(a),
                                'journal': '\n'.join(map(json.dumps, rows)) + '\n'}
                    for key, value in contents.items(): (root / key).write_text(value)
                    args = [sys.executable, '-I', '-B', str(SOURCE.resolve() / 'desktop.py'), mode, str(root / 'desktop'),
                            '--authority-receipt', str(root / 'authority'), '--journal', str(root / 'journal'),
                            '--validation-receipt', str(root / 'result'), '--authority-helper-sha256', source_hash('authority-window.py')]
                    for key, flag in (('desktop', '--desktop-receipt-sha256'), ('authority', '--authority-receipt-sha256'),
                                      ('journal', '--journal-sha256')):
                        args += [flag, hashlib.sha256(contents[key].encode()).hexdigest()]
                    if mode == '--validate-user-manager':
                        args += ['--controller-sha256', '0' * 64 if wrong else source_hash('gated-control.py')]
                    result = subprocess.run(args, cwd=root, capture_output=True, text=True, timeout=5)
                    self.assertEqual(result.returncode, 1 if wrong else 0, result.stderr + (root / 'result').read_text())
                    receipt = json.loads((root / 'result').read_text())
                    self.assertEqual(receipt['acceptance'], 'pending_coordinator_review')
                    if wrong: self.assertEqual(receipt['status'], 'incomplete')
                    for key, value in contents.items(): self.assertEqual((root / key).read_text(), value)


class LoadedDeadlineTests(unittest.TestCase):
    def test_gated_loaded_wait_uses_window_origin_after_slow_binding(self):
        import test_authority_window as tests
        w = tests.LoadedMarkerTests().window()
        w.gated_context = True; w.started_at = 1.0
        w.run = Mock()
        # bind_service already consumed the full loaded budget: no new5s wait.
        with patch.object(tests.authority.time, 'monotonic', return_value=6.1):
            with self.assertRaisesRegex(RuntimeError, 'loaded logger marker absent'):
                w.wait_loaded_marker()
        w.run.assert_not_called()


class ControllerEntrypointTests(unittest.TestCase):
    def test_abort_after_preparation_restores_without_begin_or_release(self):
        from types import SimpleNamespace
        spec = importlib.util.spec_from_file_location('abort_control', SOURCE / 'gated-control.py')
        control = importlib.util.module_from_spec(spec); spec.loader.exec_module(control)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve(); hints = root / 'hints'; hints.mkdir()
            uid = hints.stat().st_uid
            gate = Mock(); gate.MODE = gated.MODE; gate.require = gated.require; gate.sha = gated.sha
            sources = {n: {'path': str(root / n), 'sha256': gated.sha(b'source')} for n in
                       ('desktop.py', 'serve.py', 'gated.py', 'gated-driver.py')}
            gate.root_read.return_value = sources; gate.root_read_source.return_value = b'source'
            gate.boot_id.return_value = 'b' * 32
            published = []
            def publish(directory, name, value):
                published.append(name)
                if name == 'config.json': (hints / 'abort.json').write_text('{}')
            gate.publish.side_effect = publish
            authority = Mock(); authority.RULE = root / 'absent-rule'
            window = Mock(); window.record = {'cleanup': 'restored'}; window.started_at = None
            authority.Window.return_value = window
            args = ['gated-control.py']
            options = {'lease': 'lease1', 'session-id': '6', 'app-sha256': 'a' * 64,
                       'source-sha256': 'c' * 64, 'gate-source-sha256': gated.sha(b'source'),
                       'authority-source-sha256': 'd' * 64, 'uid': uid, 'driver-pid': 121,
                       'terminal-pid': 120, 'gate-directory': root / 'gate', 'hints': hints,
                       'source-manifest': root / 'manifest', 'gate-source': root / 'gated.py',
                       'authority-source': root / 'authority-window.py', 'receipt': root / 'receipt'}
            for name, value in options.items(): args += ['--' + name, str(value)]
            with patch.object(control.sys, 'argv', args), patch.object(control.sys, 'platform', 'linux'), \
                    patch.object(control.sys, 'flags', SimpleNamespace(**{**{n: getattr(sys.flags, n) for n in dir(sys.flags) if isinstance(getattr(sys.flags, n), int)}, 'isolated': 1})), \
                    patch.object(control.sys, 'dont_write_bytecode', True), \
                    patch.object(control.os, 'getuid', return_value=0), patch.object(control.os, 'geteuid', return_value=0), \
                    patch.object(control, 'load', side_effect=[authority, gate]), \
                    patch.object(control.signal, 'signal'), patch('builtins.print'):
                self.assertEqual(control.main(), 1)
            window.begin.assert_not_called(); window.restore.assert_called_once()
            self.assertEqual(published, ['config.json', 'restored.json'])
            self.assertEqual(window.record['status'], 'failed')
            self.assertIn('aborted preparation', window.record['error'])
            os.chmod(root / 'gate', 0o700)


class DriverEntrypointTests(unittest.TestCase):
    def test_delayed_recorder_completion_and_stale_log_precondition(self):
        for stale in (False, True):
            with self.subTest(stale=stale), tempfile.TemporaryDirectory() as directory:
                root = Path(directory).resolve()
                config = {'driver_pid': os.getpid(), 'uid': os.getuid(), 'lease': 'lease1',
                          'hints': str(root), 'prepare_deadline_ns': 61_000_000_000}
                argv = ['gated-driver.py']
                for name in ('gate-directory', 'hints', 'index', 'inventory', 'receipt', 'root-preflight'):
                    argv += ['--' + name, str(root if name == 'hints' else root / name)]
                for name in ('lease-reference', 'authority-reference', 'source-head', 'root-preflight-sha256', 'observer'):
                    argv += ['--' + name, 'lease1' if name == 'lease-reference' else 'fixture']
                log = root / 'server.jsonl'
                if stale: log.write_text('{"event":"serving"}\n')
                clock = [1_000_000_000]
                server, child = Mock(pid=125), Mock(pid=122)
                server.poll.return_value = None; child.poll.return_value = 1
                def launch(args, **kwargs):
                    if 'serve.py' in args[2]:
                        log.write_text('{"event":"serving"}\n'); return server
                    return child
                def wait(timeout):
                    # 10s setup then53s retention, counted from recorder launch.
                    self.assertGreaterEqual(timeout, 63)
                    clock[0] = 64_000_000_000
                    return 1
                child.wait.side_effect = wait
                with patch.object(driver.sys if hasattr(driver, 'sys') else sys, 'argv', argv), \
                        patch.object(driver.gated, 'config_read', return_value=config), \
                        patch.object(driver.time, 'monotonic', side_effect=lambda: clock[0] / 1e9), \
                        patch.object(driver.time, 'monotonic_ns', side_effect=lambda: clock[0]), \
                        patch.object(driver.subprocess, 'Popen', side_effect=launch) as popen, patch('builtins.print'):
                    if stale:
                        with self.assertRaisesRegex(RuntimeError, 'stale server log'): driver.main()
                        popen.assert_not_called()
                    else:
                        self.assertEqual(driver.main(), 1)
                        child.wait.assert_called_once(); child.terminate.assert_not_called()
                        server.terminate.assert_called_once()


class BeginOrderingTests(unittest.TestCase):
    def test_binding_arm_rechecks_rule_loaded_and_release_order(self):
        from types import SimpleNamespace
        import test_authority_window as fixtures_authority
        authority = fixtures_authority.authority
        for failing in (None, 'binding', 'pre_rule', 'loaded', 'pre_release'):
            with self.subTest(failing=failing), tempfile.TemporaryDirectory() as directory:
                root = Path(directory); rule = root / 'owned.rules'; events = []
                b = binding()
                config = {'uid': 1000, 'session_id': '6', 'lease': 'lease1', 'nonce': b['nonce']}
                window = authority.Window.__new__(authority.Window)
                window.args = SimpleNamespace(mode='deny', uid=1000, session_id='6', lease='lease1',
                                              subject_pid=None, gate_directory=root, receipt=root / 'receipt')
                window.record = {}; window.save = Mock()
                gate = Mock(); gate.config_read.return_value = config
                gate.sha = gated.sha; gate.encode = gated.encode
                def event(name):
                    events.append(name)
                    if name == failing: raise RuntimeError('injected ' + name)
                def actual_binding(*args): event('binding'); return b
                gate.actual_binding.side_effect = actual_binding
                def arm():
                    event('arm'); window.started_at = 1; window.deadline = 46
                window.arm_deadline = arm
                window.bind_service = Mock(return_value=fixtures_authority.BINDING)
                def recheck(*args):
                    if not rule.exists(): event('pre_rule')
                    else: event('pre_release')
                gate.recheck.side_effect = recheck
                gate.no_pkexec.side_effect = lambda *args: event('no_pkexec')
                def loaded():
                    self.assertEqual(rule.read_bytes(), window.rule_bytes)
                    event('loaded'); window.record['loaded_marker_observed_monotonic_ns'] = 2_000_000_000
                window.wait_loaded_marker = loaded
                window.recheck_service = Mock(side_effect=lambda *args: event('service_recheck'))
                def publish(directory, name, value):
                    self.assertTrue(rule.exists()); event(name)
                gate.publish.side_effect = publish
                window.gated_context = (gate, config, {}, {})
                proc = Mock(); proc.stat.return_value.st_uid = 1000
                proc.__truediv__ = Mock(return_value=Mock(read_text=Mock(return_value='fixture stat')))
                path = Mock(); path.__truediv__ = Mock(return_value=proc)
                real_open = os.open
                def open_rule(*args, **kwargs):
                    event('rule'); return real_open(*args, **kwargs)
                with patch.object(authority, 'RULE', rule), patch.object(authority, 'Path', return_value=path), \
                        patch.object(authority, 'safe_root_parent'), \
                        patch.object(authority.pwd, 'getpwuid', return_value=SimpleNamespace(pw_name='campusqa')), \
                        patch.object(authority.pwd, 'getpwnam', return_value=SimpleNamespace(pw_uid=1000)), \
                        patch.object(authority.os, 'open', side_effect=open_rule), \
                        patch.object(authority.time, 'monotonic', return_value=3), \
                        patch.object(authority.time, 'monotonic_ns', return_value=3_000_000_000), patch('builtins.print'):
                    if failing:
                        with self.assertRaisesRegex(RuntimeError, 'injected ' + failing): window.begin()
                        self.assertNotIn('release.json', events)
                        if failing in ('binding', 'pre_rule'): self.assertFalse(rule.exists())
                        if failing == 'binding': self.assertNotIn('arm', events)
                    else:
                        window.begin()
                        self.assertEqual(events, ['binding', 'arm', 'pre_rule', 'no_pkexec', 'rule',
                                                  'loaded', 'service_recheck', 'pre_release', 'no_pkexec',
                                                  'binding.json', 'release.json'])
